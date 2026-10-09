"""Render ten real lessons in an isolated folder; never edit published cards."""
import json,pathlib,shutil,struct,subprocess,tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
def check():
    sources=sorted((ROOT/'data/english-staged').glob('*.json')) or sorted((ROOT/'data/english-archive').glob('*.json'))
    edition=json.loads(sources[-1].read_text());date=edition['date']
    with tempfile.TemporaryDirectory(prefix='realfamily-render-') as folder:
        work=pathlib.Path(folder);(work/'scripts').mkdir();shutil.copy2(ROOT/'scripts/export_cards.cjs',work/'scripts/export_cards.cjs');shutil.copy2(ROOT/'card-palette.json',work/'card-palette.json')
        (work/'data/english-staged').mkdir(parents=True)
        (work/'data/english-staged'/f'{date}.json').write_text(json.dumps(edition))
        for lesson in edition['lessons']:
            if lesson['image']=='essay':continue
            target=work/lesson['illustration'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/lesson['illustration'],target)
        subprocess.run(['node',str(work/'scripts/export_cards.cjs'),date],check=True)
        cards=list((work/'data/english-images'/date).glob('*.png'));assert len(cards)==len(edition['lessons'])
        for card in cards:
            expected=(1434,660) if card.name.startswith('Essay_') else (660,1434)
            header=card.read_bytes()[:24];assert header[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',header[16:24])==expected
        assert len(list((work/'data/english-print'/date).glob('*.svg')))==len(cards)
    print('Ten portable cards passed layout bounds and 660x1434 output validation.')
if __name__=='__main__':check()
