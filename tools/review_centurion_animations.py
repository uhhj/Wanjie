"""Assemble actual Godot frames at 100% combat display scale."""
from pathlib import Path
from PIL import Image,ImageDraw
import roman_centurion_pipeline as p
def main():
 root=p.ROOT/p.R/'native';manifest=p.read(p.R+'native/capture_manifest.json');out=p.ROOT/p.R/'animations';out.mkdir(exist_ok=True)
 for name in ['idle','walk','attack_01','hit','death','skill_command']:
  for h in [256,192]:
   rows=[r for r in manifest['frames'] if r['animation']==name and r['height']==h];assert len(rows)==16
   frames=[]
   for row in rows:
    path=row['file'].replace('res://','');assert p.sha(path)==row['sha256'];a=Image.open(p.ROOT/path).convert('RGBA')
    bg=Image.new('RGBA',a.size,'#e4e7e8');bg.alpha_composite(a);im=bg.convert('RGB');d=ImageDraw.Draw(im);d.line([(15,421),(685,421)],fill='#9a9d9e',width=1)
    for x in range(30,690,30):d.line([(x,422),(x,428)],fill='#9a9d9e',width=1)
    d.text((8,8),f'{name} | {h}px | {row["frame"]+1:02d}/16 | {row["time"]:.3f}s',fill='black');frames.append(im)
   step=(rows[-1]['time']-rows[0]['time'])/15*1000
   # GIF stores centiseconds: distribute rounding, rather than shortening every
   # walk frame from 65.625ms to 60ms and accidentally speeding up the gait.
   duration=[round((i+1)*step/10)*10-round(i*step/10)*10 for i in range(16)]
   frames[0].save(out/f'{name}_{h}.gif',save_all=True,append_images=frames[1:],duration=duration,loop=0,disposal=2)
   # Crop fixed display framing only; never scale character pixels in review.
   sheet=Image.new('RGB',(460*4,420*2),'#eee')
   for j,i in enumerate([0,2,4,6,8,10,12,15]):
    im=frames[i].crop((140,60,600,480));ImageDraw.Draw(im).text((5,5),f'{name} {h}px frame {i+1}',fill='black');sheet.paste(im,((j%4)*460,(j//4)*420))
   sheet.save(out/f'{name}_{h}_review.png')
 print('Six 16-frame GIFs and contact sheets at each display scale')
if __name__=='__main__':main()
