"""Parent website pulls only complete, dated English editions from its public source."""
import datetime as dt,json,pathlib,shutil,subprocess,tempfile,zoneinfo
from release_english import validate
ROOT=pathlib.Path(__file__).resolve().parents[1]
def sync():
    day=dt.datetime.now(zoneinfo.ZoneInfo('America/Los_Angeles')).date()
    with tempfile.TemporaryDirectory(prefix='realfamily-source-') as directory:
        source=pathlib.Path(directory)/'source'
        subprocess.run(['git','clone','--quiet','--depth','1','https://github.com/TopChain/RealFamily.git',str(source)],check=True)
        for date in (day.isoformat(),(day+dt.timedelta(days=1)).isoformat()):
            target_archive=ROOT/'data/english-archive'/f'{date}.json';target_staged=ROOT/'data/english-staged'/f'{date}.json'
            if target_archive.exists():continue
            if target_staged.exists():
                try:validate(ROOT,json.loads(target_staged.read_text()));continue
                except (AssertionError,FileNotFoundError):pass
            candidates=[source/'data/english-archive'/f'{date}.json',source/'data/english-staged'/f'{date}.json']
            edition_path=next((p for p in candidates if p.exists()),None)
            if not edition_path:continue
            edition=json.loads(edition_path.read_text());validate(source,edition)
            # Copy assets first and expose a dated edition only when all ten are available.
            for lesson in edition['lessons']:
                for rel in [lesson['illustration'],'data/english-images/'+date+'/'+lesson['filename']]:
                    destination=ROOT/rel;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source/rel,destination)
            target_staged.parent.mkdir(parents=True,exist_ok=True)
            target_staged.write_text(json.dumps(edition,ensure_ascii=False,indent=2)+'\n')
            print('Synced complete English edition:',date)
if __name__=='__main__':sync()
