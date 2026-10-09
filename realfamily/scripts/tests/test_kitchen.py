import datetime as dt,json,pathlib,sys,tempfile,unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import release_kitchen as k
from daily_archives import snapshot
class KitchenTests(unittest.TestCase):
 def edition(self):
  return {'date':'2026-10-09','editorialApproved':True,'recipes':[{'cuisine':c,'meal':m,'title':c+' new '+m,'serves':6,'prep':15,'cook':30,'ingredients':[{'name':'Ingredient '+str(i),'amount':'100 g'} for i in range(5)],'steps':['Prepare the measured ingredients carefully using the specified pan and equipment.']*6,'allergens':'None','note':'Example note','storage':'Refrigerate within 2 hours.','photo':{'url':'https://upload.wikimedia.org/example.jpg','source':'https://commons.wikimedia.org/wiki/File:Example.jpg','author':'Photographer','license':'CC BY-SA 4.0','licenseUrl':'https://creativecommons.org/licenses/by-sa/4.0','alt':'Dish'},'videoSearch':'https://www.youtube.com/results?search_query=recipe'} for c in k.CUISINES for m in ('Main','Snack')]}
 def root(self,path):
  root=pathlib.Path(path);(root/'recipes.js').write_text('const FAMILY_RECIPES=[];');(root/'data/recipes-staged').mkdir(parents=True);return root
 def test_requires_each_theme_pair_and_six_servings(self):
  with tempfile.TemporaryDirectory() as d:
   root=self.root(d);e=self.edition();k.validate(root,e)
   e['recipes'][0]['cuisine']='European'
   with self.assertRaises(AssertionError):k.validate(root,e)
   e=self.edition();e['recipes'][0]['serves']=2
   with self.assertRaises(AssertionError):k.validate(root,e)
 def test_midnight_release_is_immutable(self):
  with tempfile.TemporaryDirectory() as d:
   root=self.root(d);e=self.edition();staged=root/'data/recipes-staged/2026-10-09.json';staged.write_text(json.dumps(e))
   self.assertFalse(k.release(root,dt.datetime(2026,10,9,6,59,tzinfo=dt.timezone.utc)))
   self.assertTrue(k.release(root,dt.datetime(2026,10,9,7,0,tzinfo=dt.timezone.utc)))
   archive=root/'data/recipes-archive/2026-10-09.json';content=archive.read_bytes();staged.write_text(json.dumps(e))
   self.assertFalse(k.release(root,dt.datetime(2026,10,9,8,0,tzinfo=dt.timezone.utc)));self.assertEqual(archive.read_bytes(),content)
 def test_no_new_date_for_rotated_static_catalog(self):
  with tempfile.TemporaryDirectory() as d:
   root=self.root(d);snapshot(root,{'daily':{'date':'2026-10-09','kitchenUpdated':'2026-10-09T07:00:00Z'}},dt.datetime(2026,10,9,7,tzinfo=dt.timezone.utc))
   self.assertFalse((root/'data/recipes-archive/2026-10-09.json').exists())
if __name__=='__main__':unittest.main()
