"""Direct publisher feeds; recent original publication, freely accessible body only."""
import concurrent.futures,datetime as dt,email.utils,html,json,re,xml.etree.ElementTree as ET,zoneinfo
PACIFIC=zoneinfo.ZoneInfo('America/Los_Angeles')
TOPICS={'US':'us-news','GB':'uk-news','TW':'world/taiwan','JP':'world/japan','CN':'world/china','IN':'world/india','DE':'world/germany','FR':'world/france','KR':'world/south-korea','CA':'world/canada','AI':'technology/artificialintelligenceai'}
def recent(s,now):
 try:
  t=dt.datetime.fromisoformat(s.replace('Z','+00:00'))
  return t.tzinfo is not None and 0<=(now.astimezone(PACIFIC).date()-t.astimezone(PACIFIC).date()).days<=1 and t<=now+dt.timedelta(minutes=5)
 except (ValueError,TypeError):return False

def verify(row,get,now):
 if not recent(row['published'],now):return None
 try:
  page=get(row['url']).decode('utf-8','replace')
  if re.search(r'"isAccessibleForFree"\s*:\s*(?:false|"false")',page,re.I):return None
  dates=re.findall(r'<meta[^>]+(?:property|name)=["\'](?:article:published_time|datePublished)["\'][^>]+content=["\']([^"\']+)',page,re.I)
  dates+=re.findall(r'"datePublished"\s*:\s*"([^"]+)"',page)
  if not dates or not recent(dates[0],now):return None
  # A direct article page must contain readable prose, not only a feed preview.
  paragraphs=re.findall(r'<p\b[^>]*>(.*?)</p>',page,re.S|re.I)
  words=sum(len(re.sub('<[^>]+>',' ',p).split()) for p in paragraphs)
  if words<100:return None
  return {**row,'published':dates[0],'accessChecked':now.isoformat(),'freeAccessVerified':True}
 except Exception:return None

def refresh(get,now):
 feeds=[(c,'The Guardian','https://www.theguardian.com/'+t+'/rss') for c,t in TOPICS.items()]
 feeds += [('KR','The Korea Times','https://feed.koreatimes.co.kr/k/southkorea.xml'),('IN','The Indian Express','https://indianexpress.com/section/india/feed/'),('AI','TechCrunch','https://techcrunch.com/category/artificial-intelligence/feed/'),('AI','Ars Technica','https://feeds.arstechnica.com/arstechnica/technology-lab')]
 candidates={c:[] for c in TOPICS};errors=[]
 def feed(item):
  code,source,url=item;rows=[]
  try:
   root=ET.fromstring(get(url))
   for n in root.findall('.//item'):
    try:published=email.utils.parsedate_to_datetime(n.findtext('pubDate')).isoformat()
    except Exception:continue
    if not recent(published,now):continue
    title=n.findtext('title','');link=n.findtext('link','')
    if '/commentisfree/' in link or '/opinion/' in link or re.search(r'\| Letter|TechCrunch Disrupt',title,re.I):continue
    if code=='AI' and source=='Ars Technica' and not re.search(r'\bAI\b|artificial intelligence|OpenAI|Anthropic',title,re.I):continue
    rows.append({'title':html.unescape(title),'url':link,'source':source,'published':published})
    if len(rows)>=(16 if code=='AI' else 6):break
   return code,rows
  except Exception as e:return code,[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
  for code,rows in pool.map(feed,feeds):candidates[code]+=rows
 # Focus Taiwan exposes direct recent article links on its public homepage.
 try:
  page=get('https://focustaiwan.tw/').decode()
  urls=list(dict.fromkeys(re.findall(r'href=["\'](https://focustaiwan.tw/(?:politics|society|business|culture|sports|sci-tech|cross-strait)/\d+)["\']',page)))[:15]
  for url in urls:
   p=get(url).decode();dates=re.findall(r'"datePublished"\s*:\s*"([^"]+)"',p)
   title=re.search(r'<meta[^>]+property="og:title"[^>]+content="([^"]+)"',p)
   if dates and title and recent(dates[0],now):candidates['TW'].append({'title':html.unescape(title[1]),'url':url,'source':'Focus Taiwan','published':dates[0]})
 except Exception:pass
 out={}
 for code,rows in candidates.items():
  rows=list({r['url']:r for r in rows}.values())
  with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:valid=[r for r in pool.map(lambda r:verify(r,get,now),rows) if r]
  out[code]=sorted(valid,key=lambda r:r['published'],reverse=True)[:10 if code=='AI' else 3]
 return out
