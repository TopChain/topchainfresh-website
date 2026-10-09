import datetime,io,pathlib,sys,tempfile,unittest,urllib.error,urllib.parse
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import sync_english_source as s
SOURCE=s.ROOT
class SourceSyncTests(unittest.TestCase):
    def test_missing_editions_copy_all_art_before_exposing_the_date(self):
        class Fixed(datetime.datetime):
            @classmethod
            def now(cls,tz=None):return cls(2026,10,8,12,tzinfo=tz)
        def get(url,timeout):
            rel=urllib.parse.unquote(url.split('/main/',1)[1]);file=SOURCE/rel
            if not file.is_file():raise urllib.error.HTTPError(url,404,'missing',{},None)
            return io.BytesIO(file.read_bytes())
        with tempfile.TemporaryDirectory() as folder,patch.object(s,'ROOT',pathlib.Path(folder)),patch.object(s.dt,'datetime',Fixed),patch.object(s.urllib.request,'urlopen',side_effect=get):
            s.sync()
            for date in ('2026-10-08','2026-10-09'):
                import json
                edition=json.loads((s.ROOT/'data/english-staged'/f'{date}.json').read_text())
                s.validate(s.ROOT,edition)
                self.assertEqual(len(list((s.ROOT/'data/english-images'/date).glob('*.png'))),len(edition['lessons']))
            self.assertFalse((s.ROOT/'data/latest.json').exists())
            # A second check performs no downloads and preserves complete editions.
            with patch.object(s.urllib.request,'urlopen',side_effect=AssertionError('No unnecessary download')):s.sync()
if __name__=='__main__':unittest.main()
