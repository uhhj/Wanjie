"""Assemble actual native GPU frames; never synthesize character movement."""
from pathlib import Path
import json
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'reports/minotaur_breaker';F=R/'animations'
def main():
    data=json.loads((R/'capture_manifest.json').read_text())
    for name in ['idle','walk','attack_01','skill_01','hit','death']:
        for height in [360,288]:
            frames=[]
            for i in range(16):
                im=Image.open(F/f'{name}_{height}_{i:02}.png').convert('RGB')
                ImageDraw.Draw(im).text((10,10),f'CANDIDATE {name} | {height}px | {i+1}/16',fill='black');frames.append(im)
            duration={'idle':2000,'walk':1400,'attack_01':1350,'skill_01':1800,'hit':400,'death':1700}[name]
            frames[0].save(F/f'{name}_{height}.gif',save_all=True,append_images=frames[1:],duration=duration//16,loop=0)
        # Full-size battle-scale images, no thumbnail resampling of character pixels.
        sheet=Image.new('RGB',(3200,1120),'#ddd')
        for j,i in enumerate([0,3,6,9,12,15]):
            im=Image.open(F/f'{name}_360_{i:02}.png').convert('RGB');sheet.paste(im,((j%4)*800,(j//4)*560))
            ImageDraw.Draw(sheet).text(((j%4)*800+10,(j//4)*560+10),f'{name} frame {i}',fill='black')
        sheet.save(R/f'{name}_candidate_contact_sheet.png')
    print('Six actual-native animation GIF pairs and contact sheets saved.')
if __name__=='__main__':main()
