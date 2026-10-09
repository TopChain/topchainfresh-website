"""Validate a newly authored edition against permanent history, then publish it."""
import sys,json,pathlib,collections,datetime,zoneinfo,unicodedata,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
def norm(s):return ''.join(c for c in unicodedata.normalize('NFKC',s).casefold() if c.isalnum())
def publish(date):
 p=ROOT/'data';file=p/'english-archive'/f'{date}.json';e=json.loads(file.read_text());assert e['date']==date
 expected={'vocabulary':2,'phrasal':2,'idiom':2,'life':1,'grammar':1,'quote':1,'small-talk':1}
 if e.get('curriculumVersion',0)>=5:expected['essay']=1
 assert collections.Counter(l['image'] for l in e['lessons'])==expected,'Wrong daily category counts'
 assert len({l['id'] for l in e['lessons']})==len(e['lessons']),'Duplicate IDs'
 seen=set();past_images=set()
 for old in (p/'english-archive').glob('*.json'):
  if old==file:continue
  for l in json.loads(old.read_text())['lessons']:
   seen.add(norm(l['title']))
   asset=ROOT/l.get('illustration','')
   if asset.is_file():past_images.add(hashlib.sha256(asset.read_bytes()).hexdigest())
 from lesson_quality import validate_lesson
 for l in e['lessons']:
  validate_lesson(l)
  if l['image']=='essay':continue
  for field in ['title','meaning','example','notes','conversation','exercise']:assert l.get(field),'Missing '+field
  key=norm(l['title']);assert key not in seen,'Repeated topic: '+l['title'];seen.add(key)
 assert len({l.get('illustration') for l in e['lessons'] if l['image']!='essay'})==10,'Each lesson needs a distinct illustration'
 current_images=set()
 for l in e['lessons']:
  if l['image']=='essay':continue
  asset=ROOT/l.get('illustration','');assert asset.is_file() and 'assets/english/' in l['illustration'],'Missing topic illustration: '+l['title']
  digest=hashlib.sha256(asset.read_bytes()).hexdigest();assert digest not in current_images|past_images,'Reused illustration: '+l['title'];current_images.add(digest)
 from card_naming import assign_filenames
 assign_filenames(e)
 e['cardSize']={'width':660,'height':1434};e['version']=4;e['published']=e.get('published',datetime.datetime.now(datetime.timezone.utc).isoformat());file.write_text(json.dumps(e,ensure_ascii=False,indent=2)+'\n')
 history={'editions':[]}
 for old in sorted((p/'english-archive').glob('*.json')):
  edition=json.loads(old.read_text());history['editions'].append({'date':edition['date'],'topics':[{'image':l['image'],'title':l['title']} for l in edition['lessons']]})
 (p/'english-history.json').write_text(json.dumps(history,ensure_ascii=False,indent=2)+'\n')
 d=json.loads((p/'latest.json').read_text());d['english']=e;d.setdefault('daily',{})['englishUpdated']=e['published'];d.setdefault('status',{})['english']={'ok':True,'updated':e['published']};(p/'latest.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');print('Published',date,'with 10 unique topics;',len(history['editions']),'archived editions')
if __name__=='__main__':publish(sys.argv[1] if len(sys.argv)>1 else datetime.datetime.now(zoneinfo.ZoneInfo('America/Los_Angeles')).date().isoformat())
