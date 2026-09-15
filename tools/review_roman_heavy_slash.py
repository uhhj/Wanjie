from pathlib import Path
import json
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
r=ROOT/'reports/roman_heavy_slash';m=json.loads((r/'capture_manifest.json').read_text(encoding='utf-8'))
sheet=Image.new('RGB',(1520,800),'white')
for row,h in enumerate([256,192]):
 fs=[f for f in m['frames'] if f['height']==h];ims=[Image.open(ROOT/f['path'].replace('res://','')).convert('RGB').crop((70,0,450,340)) for f in fs]
 ims[0].save(r/f'heavy_slash_{h}.gif',save_all=True,append_images=ims[1:],duration=[round(fs[i+1]['time']*100)*10-round(fs[i]['time']*100)*10 for i in range(15)]+[700],loop=0)
 for i,k in enumerate([2,4,6,8]):
  sheet.paste(ims[k],(i*380,row*400));ImageDraw.Draw(sheet).text((i*380+5,row*400+345),f'{h}px / t={fs[k]["time"]:.2f}',fill='black')
sheet.save(r/'combat_review.png')
