"""Persist immutable Pacific-date views for health and recipes; never backfill invented days."""
import datetime as dt,json,zoneinfo
PACIFIC=zoneinfo.ZoneInfo('America/Los_Angeles')
def catalog(root,name):return json.loads((root/name).read_text().split('=',1)[1].strip().rstrip(';'))
def snapshot(root,data,now):
 day=now.astimezone(PACIFIC).date().isoformat();history={}
 for topic in ['health','recipes']:
  directory=root/'data'/f'{topic}-archive';directory.mkdir(parents=True,exist_ok=True);file=directory/f'{day}.json'
  if not file.exists():
   if topic=='health':
    checked=data.get('researchChecked')
    if checked and dt.datetime.fromisoformat(checked).astimezone(PACIFIC).date().isoformat()==day:
     edition={'date':day,'published':checked,'profiles':catalog(root,'health-guidance.js'),'research':data.get('research',[]),'researchChecked':checked,'researchUpdated':data.get('researchUpdated')}
    else:edition=None
   else:
    # Recipe archives are created only by release_kitchen after authoring validation.
    edition=None
   if edition:file.write_text(json.dumps(edition,ensure_ascii=False,indent=2)+'\n')
  history[topic]=sorted([p.stem for p in directory.glob('*.json') if p.stem<=day],reverse=True)
 (root/'data/daily-history.json').write_text(json.dumps(history,indent=2)+'\n')
 return history
