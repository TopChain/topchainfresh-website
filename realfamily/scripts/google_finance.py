"""Read only public Google Finance quote-page data; fail closed on schema changes."""
import json,re,datetime as dt,zoneinfo
from session_status import classify,analysis_gate
SYMBOLS={'^DJI':'.DJI:INDEXDJX','^IXIC':'.IXIC:INDEXNASDAQ','^GSPC':'.INX:INDEXSP','^SOX':'SOX:INDEXNASDAQ','^RUT':'RUT:INDEXRUSSELL','000001.SS':'000001:SHA','399001.SZ':'399001:SHE','000300.SS':'000300:SHA','000688.SS':'000688:SHA','399006.SZ':'399006:SHE','^N225':'NI225:INDEXNIKKEI','^TOPX':'TOPIX:INDEXTOPIX','^NSEI':'NIFTY_50:INDEXNSE','^BSESN':'SENSEX:INDEXBOM','^NSEBANK':'NIFTY_BANK:INDEXNSE','^HSI':'HSI:INDEXHANGSENG','^HSCE':'HSCEI:INDEXHANGSENG','^GSPTSE':'OSPTX:INDEXTSI','^FTSE':'UKX:INDEXFTSE','^FCHI':'PX1:INDEXEURO','^GDAXI':'DAX:INDEXDB','^TWII':'TAIEX:INDEXTPE','^KS11':'KOSPI:KRX','^KQ11':'KOSDAQ:KRX','^AXJO':'XJO:INDEXASX','^SSMI':'SMI:INDEXSWX'}
def walk(x):
 if isinstance(x,list):
  yield x
  for v in x:yield from walk(v)
def callbacks(html):
 dec=json.JSONDecoder()
 for m in re.finditer(r"AF_initDataCallback\(\{key: 'ds:\d+'",html):
  p=html.find('data:',m.end())+5
  try:yield dec.raw_decode(html[p:])[0]
  except (ValueError,TypeError):continue

def quote(symbol,tz,get,now):
 pair=SYMBOLS.get(symbol)
 if not pair:raise ValueError('No verified Google Finance symbol mapping available')
 url='https://www.google.com/finance/quote/'+pair+'?hl=en'
 html=get(url).decode('utf-8');payloads=list(callbacks(html));key=pair.split(':')
 candidates=[n for d in payloads for n in walk(d) if len(n)>21 and n[1]==key and isinstance(n[5],list) and isinstance(n[5][0],(float,int))]
 if not candidates:raise ValueError('Google Finance quote unavailable or page schema changed')
 n=candidates[0];timestamp=n[11][0];local=dt.datetime.fromtimestamp(timestamp,zoneinfo.ZoneInfo(tz));regular={}
 def epoch(a):return dt.datetime(*[v or 0 for v in a[:6]],tzinfo=zoneinfo.ZoneInfo(tz)).timestamp()
 try:
  periods=[p for p in n[19] if len(p)>2 and len(p[1])>=6 and len(p[2])>=6]
  if periods:regular={'start':epoch(periods[0][1]),'end':epoch(periods[-1][2])}
 except (ValueError,TypeError,IndexError):pass
 bars={}
 for d in payloads:
  daily=[node for node in walk(d) if len(node)>8 and node[0]==key and node[8]==86400]
  for a in (row for node in daily for row in walk(node)):
   if len(a)==6 and isinstance(a[4],str) and re.match(r'^\d{4}-\d\d-\d\dT',a[4]) and all(isinstance(v,(int,float)) for v in a[:4]):
    t=dt.datetime.fromisoformat(a[4]);date=t.astimezone(zoneinfo.ZoneInfo(tz)).date().isoformat()
    # Daily historical arrays use 24-hour resolution, not intraday candles.
    if t.hour==int(dt.datetime.fromtimestamp(regular.get('end',0),zoneinfo.ZoneInfo(tz)).hour) and t.minute==int(dt.datetime.fromtimestamp(regular.get('end',0),zoneinfo.ZoneInfo(tz)).minute):bars[date]=a[1]
 status=classify(now,regular,tz);session=local.date().isoformat();gate=analysis_gate(now,regular,tz,session)
 price=float(n[5][0]);analysis=None
 # Require a historical daily close for this session, not just a late quote.
 verified=session in bars and abs(bars[session]-price)<max(.02,price*.00001)
 if not verified:
  gate['analysisReady']=False
  if status=='Closed':gate['analysisStatus']='Awaiting a matching Google Finance daily close; analysis withheld.'
 if gate['analysisReady']:
  ordered=sorted(bars.items())
  if len(ordered)>=20:
   ma=sum(c for _,c in ordered[-20:])/20
   analysis=f'Rule-based observation (not AI): the verified close changed {n[5][2]:+.2f}% and is {"above" if price>ma else "below"} its 20-session average ({ma:,.2f}). Next trading session, watch the average and price confirmation; no reliable direction is asserted.'
  else:gate.update(analysisReady=False,analysisStatus='Insufficient Google Finance daily history for a 20-session observation.')
 return {**gate,'close':price,'change':float(n[5][2]),'session':session,'state':'Verified daily close' if verified else 'Latest quote; closing finality unverified','updated':now.isoformat(),'quoteAt':local.isoformat(),'timezone':tz,'marketStatus':status,'regularSession':regular,'analysis':analysis,'source':url,'provider':'Google Finance'}
