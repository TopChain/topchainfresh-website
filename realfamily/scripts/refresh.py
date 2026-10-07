"""Public-source refresh. No secrets, fabricated prices, or paid data access."""
import concurrent.futures, datetime as dt, json, pathlib, urllib.request, urllib.parse, xml.etree.ElementTree as ET, zoneinfo, re
from session_status import classify, analysis_gate

ROOT=pathlib.Path(__file__).resolve().parents[1]
DEST=ROOT/'data/latest.json'
NOW=dt.datetime.now(dt.timezone.utc)
STAMP=NOW.isoformat()
PACIFIC=zoneinfo.ZoneInfo('America/Los_Angeles')
DAILY_DATE=NOW.astimezone(PACIFIC).date().isoformat()
HEADERS={'User-Agent':'Mozilla/5.0 (compatible; RealFamily/1.0; public educational news digest)'}
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers=HEADERS),timeout=25) as r: return r.read()
def load_old():
    try:return json.loads(DEST.read_text())
    except Exception:return {'countries':{},'ai':[],'markets':{},'research':[],'status':{}}
data=load_old()
countries=[('US','United States'),('TW','Taiwan'),('GB','United Kingdom'),('JP','Japan'),('CN','China'),('IN','India'),('DE','Germany'),('FR','France'),('KR','South Korea'),('CA','Canada')]
def news_task(item):
    code,name=item
    domains=['reuters.com','apnews.com','bbc.com','cnn.com','theguardian.com','nytimes.com','ft.com','aljazeera.com']
    regional={'TW':['focustaiwan.tw','taipeitimes.com'],'JP':['japantimes.co.jp','english.kyodonews.net'],'IN':['thehindu.com','indianexpress.com'],'KR':['koreaherald.com','koreatimes.co.kr'],'CA':['cbc.ca','ctvnews.ca'],'DE':['dw.com'],'FR':['france24.com','lemonde.fr'],'CN':['scmp.com'],'US':['nbcnews.com','cbsnews.com'],'GB':['bbc.co.uk']}
    domains+=regional.get(code,[])
    if code=='AI':domains+=['theverge.com','techcrunch.com','arstechnica.com','wired.com','technologyreview.com']
    query=('artificial intelligence' if code=='AI' else name)+' ('+' OR '.join('site:'+d for d in domains)+') when:1d'
    url='https://news.google.com/rss/search?'+urllib.parse.urlencode({'q':query,'hl':'en-US','gl':'US','ceid':'US:en'})
    tree=ET.fromstring(get(url));rows=[];seen=set()
    for node in tree.findall('.//item'):
        title=node.findtext('title','');source=node.findtext('source','Unknown publisher');clean=title.rsplit(' - '+source,1)[0]
        if clean.lower() in seen:continue
        seen.add(clean.lower())
        from email.utils import parsedate_to_datetime
        published=parsedate_to_datetime(node.findtext('pubDate')).isoformat()
        rows.append({'title':clean,'url':node.findtext('link'),'source':source,'published':published})
        if len(rows)==(10 if code=='AI' else 3):break
    if not rows:raise ValueError('Empty feed')
    return code,rows
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    futures={pool.submit(news_task,c):c[0] for c in countries+[('AI','AI')]}
    successes=0
    for future in concurrent.futures.as_completed(futures):
        code=futures[future]
        try:
            key,rows=future.result()
            if key=='AI':data['ai']=rows
            else:data['countries'][key]=rows
            data['status'][code]={'ok':True,'updated':STAMP};successes+=1
        except Exception as e:data['status'][code]={'ok':False,'checked':STAMP,'error':str(e)[:160]}
    if successes==11:data['newsUpdated']=STAMP
    elif successes:data['newsPartialUpdated']=STAMP

# Latest daily bars can be incomplete; do not label them final before exchange close.
markets=[('America/New_York','16:00',['^DJI','^IXIC','^GSPC','^SOX','^RUT']),('Asia/Shanghai','15:00',['000001.SS','399001.SZ','000300.SS','000688.SS','399006.SZ']),('Asia/Tokyo','15:30',['^N225','^TOPX']),('Asia/Kolkata','15:30',['^NSEI','^BSESN','^NSEBANK']),('Asia/Hong_Kong','16:00',['^HSI','^HSCE','HSTECH.HK']),('America/Toronto','16:00',['^GSPTSE','TX60.TS']),('Europe/London','16:30',['^FTSE','^FTMC','^FTAS']),('Europe/Paris','17:30',['^FCHI','^SBF120']),('Europe/Berlin','17:30',['^GDAXI','^MDAXI','^SDAXI','^TECDAX']),('Asia/Taipei','13:30',['^TWII','^TWOII']),('Asia/Seoul','15:30',['^KS11','^KQ11']),('Australia/Sydney','16:00',['^AXJO','^AORD']),('Asia/Riyadh','15:00',['^TASI.SR']),('Europe/Zurich','17:30',['^SSMI','^SPI'])]
def market_task(symbol,tz,close_time):
    url='https://query1.finance.yahoo.com/v8/finance/chart/'+urllib.parse.quote(symbol,safe='')+'?range=3mo&interval=1d'
    chart=json.loads(get(url))['chart']['result'][0];quotes=chart['indicators']['quote'][0];times=chart['timestamp']
    bars=[(t,c) for t,c in zip(times,quotes['close']) if c is not None]
    if len(bars)<2:raise ValueError('Insufficient history')
    timestamp,close=bars[-1];previous=bars[-2][1];local=dt.datetime.fromtimestamp(timestamp,zoneinfo.ZoneInfo(tz));local_now=NOW.astimezone(zoneinfo.ZoneInfo(tz))
    regular=chart.get('meta',{}).get('currentTradingPeriod',{}).get('regular',{})
    market_status=classify(NOW,regular,tz)
    provisional=local.date()==local_now.date() and market_status in ['Trading now','Lunch break','Not yet open']
    change=(close/previous-1)*100;ma20=sum(c for _,c in bars[-20:])/min(20,len(bars))
    direction='above' if close>ma20 else 'below'
    gate=analysis_gate(NOW,regular,tz,local.date().isoformat())
    analysis=f'Rule-based observation (not AI): the latest daily bar changed {change:+.2f}% and sits {direction} its 20-session average ({ma20:,.2f}). Next session, watch whether price holds that average and whether participation confirms the move. No directional forecast is asserted.'
    if not gate['analysisReady']:analysis=None
    return symbol,{**gate,'close':close,'change':change,'session':local.strftime('%Y-%m-%d'),'state':'Provisional daily bar' if provisional else 'Historical daily bar; finality unverified','updated':STAMP,'timezone':tz,'marketStatus':market_status,'regularSession':regular,'analysis':analysis,'source':url}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    futures={pool.submit(market_task,s,t,c):s for t,c,symbols in markets for s in symbols}
    for future in concurrent.futures.as_completed(futures):
        symbol=futures[future]
        try:key,row=future.result();data['markets'][key]=row;data['status'][symbol]={'ok':True,'updated':STAMP}
        except Exception as e:data['status'][symbol]={'ok':False,'checked':STAMP,'error':str(e)[:160]}
if any(v.get('updated')==STAMP for v in data['markets'].values()):data['marketUpdated']=STAMP
# Refresh research at most daily. Indexing date and publication date are separate.
research_date=dt.datetime.fromisoformat(data.get('researchChecked',data.get('researchUpdated'))).astimezone(PACIFIC).date().isoformat() if data.get('researchChecked') or data.get('researchUpdated') else None
if research_date!=DAILY_DATE:
    try:
        query='(TITLE_ABS:nutrition OR TITLE_ABS:exercise OR TITLE_ABS:"physical activity" OR TITLE_ABS:"dietary supplements" OR TITLE_ABS:sleep) AND (TITLE_ABS:infant OR TITLE_ABS:children OR TITLE_ABS:adolescent OR TITLE_ABS:adult OR TITLE_ABS:elderly OR TITLE_ABS:"older adults") AND FIRST_PDATE:['+(NOW-dt.timedelta(days=60)).strftime('%Y-%m-%d')+' TO '+NOW.strftime('%Y-%m-%d')+']'
        url='https://www.ebi.ac.uk/europepmc/webservices/rest/search?'+urllib.parse.urlencode({'query':query,'format':'json','pageSize':8,'sort':'FIRST_PDATE_D desc','resultType':'core'})
        results=json.loads(get(url))['resultList']['result'];rows=[]
        for r in results:
            pubtypes=r.get('pubTypeList',{}).get('pubType',[])
            rows.append({'title':r['title'],'url':'https://europepmc.org/article/'+r['source']+'/'+r['id'],'journal':r.get('journalInfo',{}).get('journal',{}).get('title','Journal'),'date':r.get('firstPublicationDate',r.get('pubYear','Unknown')),'type':', '.join(pubtypes[:2]) or 'Publication','population':'Population and study limitations require full-text review','abstractExcerpt':' '.join(re.sub('<[^>]*>',' ',r.get('abstractText','')).split()[:25])+(' …' if r.get('abstractText') else '')})
        known={r['url'] for r in data.get('research',[])}
        fresh=[dict(r,discoveredDate=DAILY_DATE,discoveredAt=STAMP) for r in rows if r['url'] not in known]
        if fresh:data['research']=fresh+data.get('research',[]);data['researchUpdated']=STAMP
        data['researchChecked']=STAMP;data['status']['research']={'ok':True,'checked':STAMP,'newCount':len(fresh)}
        (ROOT/'data/research-archive.json').write_text(json.dumps(data['research'],ensure_ascii=False,indent=2)+'\n')
    except Exception as e:data['status']['research']={'ok':False,'checked':STAMP,'error':str(e)[:160]}
if data.get('daily',{}).get('date')!=DAILY_DATE:
    offset=NOW.astimezone(PACIFIC).date().toordinal()
    data['daily']={'date':DAILY_DATE,'timezone':'America/Los_Angeles','kitchenUpdated':STAMP,'englishUpdated':STAMP,'recipeIndices':[(offset%10)*2,(offset%10)*2+1],'practiceEdition':offset%3,'mode':'Curated daily selection and practice rotation'}
# Publish only an actually authored edition. Never rotate old lessons or relabel their date.
archive=ROOT/'data/english-archive'/f'{DAILY_DATE}.json'
if archive.exists():
    current=json.loads(archive.read_text())
    if data.get('english',{}).get('date')!=current['date'] or data.get('english',{}).get('version')!=4 or data.get('english',{}).get('revision')!=current.get('revision'):
        data['english']=current
    data['daily']['englishUpdated']=current.get('published',STAMP)
else:
    data['daily']['englishUpdated']=data.get('english',{}).get('published',data.get('daily',{}).get('englishUpdated'))
    data['status']['english']={'ok':False,'checked':STAMP,'error':'New daily edition awaiting authoring; previous edition retained with its original date.'}
if not data.get('marketCaps',{}).get('checked','').startswith(STAMP[:7]):
    try:
        cap_url='https://api.worldbank.org/v2/country/USA;CHN;JPN;IND;HKG;CAN;GBR;FRA;DEU;KOR;AUS;SAU;CHE/indicator/CM.MKT.LCAP.CD?format=json&date=2025&per_page=100'
        cap_result=json.loads(get(cap_url))
        aliases={'Hong Kong SAR, China':'Hong Kong','Korea, Rep.':'South Korea'}
        caps={aliases.get(r['country']['value'],r['country']['value']):r['value'] for r in cap_result[1] if r['value'] is not None}
        if len(caps)>=10:data['marketCaps']={'year':2025,'source':cap_url,'checked':STAMP,'values':caps,'datasetUpdated':cap_result[0]['lastupdated']}
    except Exception as e:data['status']['marketCaps']={'ok':False,'checked':STAMP,'error':str(e)[:160]}
data['checked']=STAMP
DEST.parent.mkdir(exist_ok=True);DEST.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'news_countries':len(data['countries']),'ai_stories':len(data['ai']),'market_benchmarks':len(data['markets']),'research_papers':len(data['research']),'failed_sources':[k for k,v in data['status'].items() if not v['ok']]}))
