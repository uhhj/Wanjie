"""Review-only assembly and localized baked-background cleanup; no formal promotion."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image,ImageDraw
from build_minotaur_candidates import ORDER
ROOT=Path(__file__).resolve().parents[1];W=ROOT/'work/minotaur_breaker';R=ROOT/'reports/minotaur_breaker'
def main():
    src=Image.open(W/'01_complete_body_rgba.png');a=np.array(src);original=a.copy()
    # Inspected AI-only gap between near upper arm and torso, not metal/fur art.
    m=Image.new('L',src.size);ImageDraw.Draw(m).polygon([(339,609),(365,602),(358,635),(344,657),(335,636)],fill=255)
    allowed=np.array(Image.open(W/'masks/body_completion_effective.png'))>0
    neutral=(a[:,:,:3].max(2).astype(int)-a[:,:,:3].min(2).astype(int)<24)&(a[:,:,:3].min(2)>65)
    cut=(np.array(m)>0)&allowed&neutral&(a[:,:,3]>0);a[cut,3]=0
    out=W/'01_complete_body_rgba_v2.png';Image.fromarray(a).save(out)
    Image.fromarray(cut.astype('uint8')*255).save(W/'masks/body_checker_gap_cleanup.png')
    (R/'body_local_alpha_fix.json').write_text(json.dumps({'input_sha256':hashlib.sha256((W/'01_complete_body_rgba.png').read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'removed_checker_pixels':int(cut.sum()),'rgb_changed_pixels':int(np.any(original[:,:,:3]!=a[:,:,:3],2).sum()),'scope':'Only inspected generated near-armpit gap; no source art modified'},indent=2)+'\n')
    composite=Image.new('RGBA',src.size)
    for name in ORDER:
        path=W/'candidates/parts'/f'{name}.png'
        if name=='arm_far_upper':path=W/'candidates/parts/arm_far_upper_completed.png'
        if not path.exists():raise RuntimeError(f'Missing candidate {name}')
        p=np.array(Image.open(path));p[cut,3]=0
        composite.alpha_composite(Image.fromarray(p))
    composite.save(R/'candidate_recomposed.png')
    master=Image.open(W/'00_rig_master_rgba.png')
    sheet=Image.new('RGB',(1200,850),'#aaa');d=ImageDraw.Draw(sheet)
    for row,height in enumerate([360,288]):
        for col,im in enumerate([master,composite]):
            scale=height/1435;im=im.resize((round(1024*scale),round(1536*scale)),Image.Resampling.LANCZOS)
            x=40+col*400;y=30+row*420
            bg=Image.new('RGBA',im.size,'#ddd');bg.alpha_composite(im);sheet.paste(bg.convert('RGB'),(x,y+25))
            d.text((x,y),f'{"SOURCE" if col==0 else "CANDIDATE"} {height}px',fill='black')
    sheet.save(R/'candidate_recomposition_combat_review.png')
    print('Local alpha cleanup pixels:',cut.sum(),'; assembly remains candidate.')
if __name__=='__main__':main()
