"""Pull complete kitchen editions from the public source; never relabel old recipes."""
import datetime as dt,json,pathlib,urllib.request,urllib.error
from release_kitchen import PACIFIC,validate
ROOT=pathlib.Path(__file__).resolve().parents[1]
def sync():
    today=dt.datetime.now(PACIFIC).date()
    for day in (today,today+dt.timedelta(days=1)):
        date=day.isoformat();archive=ROOT/'data/recipes-archive'/f'{date}.json';staged=ROOT/'data/recipes-staged'/f'{date}.json'
        if archive.exists():continue
        if staged.exists():validate(ROOT,json.loads(staged.read_text()));continue
        edition=None
        for folder in ('recipes-staged','recipes-archive'):
            try:
                with urllib.request.urlopen('https://raw.githubusercontent.com/TopChain/RealFamily/main/data/'+folder+'/'+date+'.json',timeout=30) as response:
                    content=response.read(2_000_001);assert len(content)<=2_000_000;edition=json.loads(content)
                break
            except urllib.error.HTTPError as error:
                if error.code!=404:raise
        if edition:
            assert edition['date']==date;validate(ROOT,edition)
            staged.parent.mkdir(parents=True,exist_ok=True);staged.write_text(json.dumps(edition,ensure_ascii=False,indent=2)+'\n')
            print('Synced twenty new kitchen recipes:',date)
if __name__=='__main__':sync()
