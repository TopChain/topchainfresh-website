"""One complete recipe per US Letter PDF; immutable dates and searchable text."""
import hashlib,json,pathlib,io,html
from reportlab.pdfgen import canvas
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import reportlab
ROOT=pathlib.Path(__file__).resolve().parents[1]
fonts=pathlib.Path(reportlab.__file__).parent/'fonts'
pdfmetrics.registerFont(TTFont('Kitchen',str(fonts/'Vera.ttf')))
pdfmetrics.registerFont(TTFont('KitchenBold',str(fonts/'VeraBd.ttf')))
pdfmetrics.registerFontFamily('Kitchen',normal='Kitchen',bold='KitchenBold')
def export(recipe,date,index):
 out=ROOT/'data/recipe-pdfs'/date;out.mkdir(parents=True,exist_ok=True)
 name=f'Family Kitchen_{date}_{index:02d}.pdf';dest=out/name
 digest=hashlib.sha256(('layout-1'+json.dumps(recipe,sort_keys=True)).encode()).hexdigest()
 stamp=dest.with_suffix('.sha256')
 if dest.exists() and stamp.exists() and stamp.read_text()==digest:return
 def draw(size,write=False):
  buf=io.BytesIO();c=canvas.Canvas(buf,pagesize=(612,792),pageCompression=1,invariant=1)
  c.setTitle(recipe['title']);c.setAuthor('Family Kitchen')
  c.setStrokeColorRGB(.57,.66,.56);c.roundRect(24,24,564,744,8,stroke=1,fill=0)
  c.setFillColorRGB(.20,.29,.22);c.setFont('KitchenBold',11);c.drawString(40,746,'Family Kitchen - '+recipe['cuisine'])
  c.setFont('Kitchen',9);c.drawRightString(572,746,date+' - PT')
  y=724
  def para(text,font=size,bold=False,gap=6):
   nonlocal y
   style=ParagraphStyle('recipe',fontName='KitchenBold' if bold else 'Kitchen',fontSize=font,leading=font*1.34,textColor='#28352c')
   p=Paragraph(text,style);w,h=p.wrap(532,900);p.drawOn(c,40,y-h);y-=h+gap
  esc=lambda v:html.escape(str(v))
  para(esc(recipe['title']),19,True,10)
  para(f"Serves {recipe['serves']} | {recipe['meal']} | Prep {recipe['prep']} min | Cook {recipe['cook']} min",10,False,12)
  para('INGREDIENTS',10,True)
  # Compact, readable ingredient list, preserving every original quantity.
  para(' &nbsp; / &nbsp; '.join(esc(i['amount'])+' '+esc(i['name']) for i in recipe['ingredients']),gap=12)
  para('METHOD',10,True)
  for i,step in enumerate(recipe['steps'],1):para(f'<b>{i}.</b> '+esc(step),gap=5)
  para('KITCHEN NOTE',9,True,3);para(esc(recipe['note']),gap=7)
  para('ALLERGENS',9,True,3);para(esc(recipe['allergens'])+'. Check every product label.',gap=7)
  if recipe.get('storage'):para('STORAGE &amp; LEFTOVERS',9,True,3);para(esc(recipe['storage']),gap=8)
  para('Wash produce, avoid cross-contamination, refrigerate leftovers promptly. Poultry: 165°F / 74°C; fish: 145°F / 63°C.',8,gap=0)
  c.showPage();c.save()
  return y,buf.getvalue()
 chosen=None
 for n in range(23,16,-1):
  y,data=draw(n/2)
  if y>=38:chosen=(n/2,data);break
 if not chosen:raise ValueError('Recipe cannot fit legibly on one Letter page: '+recipe['title'])
 dest.write_bytes(chosen[1]);stamp.write_text(digest)
 return chosen[0]
def main():
 count=0
 for folder in ('recipes-archive','recipes-staged'):
  for file in sorted((ROOT/'data'/folder).glob('*.json')):
   edition=json.loads(file.read_text())
   for i,r in enumerate(edition['recipes'],1):export(r,edition['date'],i);count+=1
 print(f'Letter recipe PDFs verified: {count}')
if __name__=='__main__':main()
