import copy,json,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from lesson_quality import validate_lesson
from release_english import validate
ROOT=pathlib.Path(__file__).resolve().parents[2]
class EssayTests(unittest.TestCase):
 def setUp(self):
  self.edition=json.loads((ROOT/'data/english-archive/2026-10-09.json').read_text());self.essay=self.edition['lessons'][-1]
 def test_complete_landscape_edition(self):self.assertTrue(validate(ROOT,self.edition))
 def test_middle_paragraph_cannot_be_shortened(self):
  lesson=copy.deepcopy(self.essay);lesson['paragraphs'][1]=lesson['paragraphs'][1][:1]
  with self.assertRaises(AssertionError):validate_lesson(lesson)
 def test_essay_must_connect_every_lesson(self):
  edition=copy.deepcopy(self.edition);edition['lessons'][-1]['connections'][0]['lessonId']='missing'
  with self.assertRaises(AssertionError):validate(ROOT,edition)
if __name__=='__main__':unittest.main()
