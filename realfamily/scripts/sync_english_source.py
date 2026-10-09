"""Parent website pulls only complete, dated English editions from its public source."""
import datetime as dt,json,pathlib,shutil,tempfile,zoneinfo,urllib.request,urllib.error,urllib.parse
from release_english import validate
ROOT=pathlib.Path(__file__).resolve().parents[1]
def sync():
    day=dt.datetime.now(zoneinfo.ZoneInfo('America/Los_Angeles')).date()
    with tempfile.TemporaryDirectory(prefix='realfamily-source-') as directory:
        source=pathlib.Path(directory)/'source'
        source.mkdir()
        def download(relative):
            assert not pathlib.PurePosixPath(relative).is_absolute() and '..' not in pathlib.PurePosixPath(relative).parts
            url='https://raw.githubusercontent.com/TopChain/RealFamily/main/'+urllib.parse.quote(relative,safe='/')
            with urllib.request.urlopen(url,timeout=30) as response:
                content=response.read(4_000_001);assert len(content)<=4_000_000,'Source asset too large'
            destination=source/relative;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(content)
            return destination
        for date in (day.isoformat(),(day+dt.timedelta(days=1)).isoformat()):
            target_archive=ROOT/'data/english-archive'/f'{date}.json';target_staged=ROOT/'data/english-staged'/f'{date}.json'
            if target_archive.exists():continue
            if target_staged.exists():
                try:validate(ROOT,json.loads(target_staged.read_text()));continue
                except (AssertionError,FileNotFoundError):pass
            edition_path=None
            for category in ('english-staged','english-archive'):
                try:edition_path=download('data/'+category+'/'+date+'.json');break
                except urllib.error.HTTPError as error:
                    if error.code!=404:raise
            if not edition_path:continue
            edition=json.loads(edition_path.read_text());assert edition['date']==date
            for lesson in edition['lessons']:
                assert lesson['image']=='essay' or lesson['illustration'].startswith('assets/english/'+date+'/')
                assert '/' not in lesson['filename'] and '\\' not in lesson['filename']
                if lesson.get('illustration'):download(lesson['illustration'])
                download('data/english-images/'+date+'/'+lesson['filename'])
                download('data/english-print/'+date+'/'+lesson['filename'].replace('.png','.svg'))
                download('data/english-print/'+date+'/'+lesson['filename'])
            # Validate against all local historical teaching points and image hashes.
            archive_dir=source/'data/english-archive';archive_dir.mkdir(parents=True,exist_ok=True)
            for old in (ROOT/'data/english-archive').glob('*.json'):
                if old.stem==date:continue
                link=archive_dir/old.name
                if not link.exists():link.symlink_to(old)
                for lesson in json.loads(old.read_text())['lessons']:
                    if lesson['image']=='essay':continue
                    asset=source/lesson['illustration']
                    if not asset.exists():asset.parent.mkdir(parents=True,exist_ok=True);asset.symlink_to(ROOT/lesson['illustration'])
            validate(source,edition)
            # Copy assets first and expose a dated edition only when all ten are available.
            for lesson in edition['lessons']:
                for rel in ([lesson['illustration']] if lesson.get('illustration') else [])+['data/english-images/'+date+'/'+lesson['filename'],'data/english-print/'+date+'/'+lesson['filename'].replace('.png','.svg'),'data/english-print/'+date+'/'+lesson['filename']]:
                    destination=ROOT/rel;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source/rel,destination)
            target_staged.parent.mkdir(parents=True,exist_ok=True)
            target_staged.write_text(json.dumps(edition,ensure_ascii=False,indent=2)+'\n')
            print('Synced complete English edition:',date)
if __name__=='__main__':sync()
