"""Release a complete prebuilt lesson set on its Pacific date, without a local computer."""
import collections,datetime as dt,hashlib,json,re,struct,zoneinfo
from card_naming import assign_filenames
PACIFIC=zoneinfo.ZoneInfo('America/Los_Angeles')
COUNTS={'vocabulary':2,'phrasal':2,'idiom':2,'life':1,'grammar':1,'quote':1,'small-talk':1}
def validate(root,edition):
 date=edition['date'];dt.date.fromisoformat(date)
 lessons=edition['lessons'];assert len(lessons)==(11 if edition.get('curriculumVersion',0)>=5 else 10)
 assert collections.Counter(l['image'] for l in lessons)==dict(COUNTS,essay=1) if edition.get('curriculumVersion',0)>=5 else collections.Counter(l['image'] for l in lessons)==COUNTS
 assert len({l['id'] for l in lessons})==len(lessons)
 seen=set();pictures=set()
 for l in lessons:
  from lesson_quality import validate_lesson
  validate_lesson(l)
  if 'level' in l:assert l['level'] in {'B2','C1','C2'},'Invalid CEFR level'
  assert date<'2026-10-07' or re.fullmatch(re.escape(date)+r'-\d+',l['id'])
  if l['image']=='essay':
   if edition.get('essayIllustrationVersion',0)>=1:
    assert l.get('illustration','').startswith('assets/english/'+date+'/') and (root/l['illustration']).is_file(), 'Missing Essay theme illustration'
   assert {c['lessonId'] for c in l['connections']}<={x['id'] for x in lessons if x['image']!='essay'}
   connected={c['lessonId'] for c in l['connections']}
   assert {'vocabulary','phrasal','idiom','grammar'}<={x['image'] for x in lessons if x['id'] in connected}, 'Essay must apply the core language categories'
   png=root/'data/english-images'/date/l['filename'];header=png.read_bytes()[:24]
   assert header[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',header[16:24])==(1434,660),'Missing landscape essay PNG'
   continue
  for key in ['title','meaning','example','notes','conversation','exercise']:assert isinstance(l.get(key),str) and l[key].strip(),key
  title=''.join(c for c in l['title'].casefold() if c.isalnum());assert title not in seen;seen.add(title)
  art=root/l['illustration'];assert art.is_file() and l['illustration'].startswith('assets/english/'+date+'/')
  digest=hashlib.sha256(art.read_bytes()).hexdigest();assert digest not in pictures;pictures.add(digest)
  png=root/'data/english-images'/date/l.get('filename',l['id']+'.png');header=png.read_bytes()[:24]
  assert header[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',header[16:24])==(660,1434),'Missing or wrong-sized PNG'
 for old in (root/'data/english-archive').glob('*.json'):
  if old.stem==date:continue
  for l in json.loads(old.read_text())['lessons']:
   title=''.join(c for c in l['title'].casefold() if c.isalnum());assert title not in seen,'Repeated historical topic'
   art=root/l.get('illustration','')
   if art.is_file():assert hashlib.sha256(art.read_bytes()).hexdigest() not in pictures,'Reused historical art'
 return True

def release(root,now):
 date=now.astimezone(PACIFIC).date().isoformat();staged=root/'data/english-staged'/f'{date}.json';archive=root/'data/english-archive'/f'{date}.json'
 if archive.exists() or not staged.exists():return False
 edition=json.loads(staged.read_text());assert edition['date']==date
 assign_filenames(edition)
 validate(root,edition)
 edition.update(published=now.isoformat(),version=4,cardSize={'width':660,'height':1434})
 archive.write_text(json.dumps(edition,ensure_ascii=False,indent=2)+'\n')
 history={'editions':[]}
 for old in sorted(archive.parent.glob('*.json')):
  e=json.loads(old.read_text())
  if e['date']<=date:history['editions'].append({'date':e['date'],'topics':[{'image':l['image'],'title':l['title']} for l in e['lessons']]})
 (root/'data/english-history.json').write_text(json.dumps(history,ensure_ascii=False,indent=2)+'\n')
 staged.unlink();return True
