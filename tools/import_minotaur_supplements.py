"""Candidate-only local art imports. Frozen references are never written."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib
import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
W=ROOT/'work/minotaur_breaker'; R=ROOT/'reports/minotaur_breaker'
SIZE=(1024,1536)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def mask(name,points):
    m=Image.new('L',SIZE);ImageDraw.Draw(m).polygon(points,fill=255)
    m.save(W/'masks'/f'{name}.png');return np.array(m)>0
def save_part(name,a):
    a[a[:,:,3]==0,:3]=0
    p=W/'candidates/parts'/f'{name}.png';Image.fromarray(a).save(p);return p
def job(number,name,source,output,details):
    record={'job':number,'tool':'built-in image_gen','status':'CANDIDATE_REVIEW_REQUIRED',
      'recorded_at_utc':datetime.now(timezone.utc).isoformat(),'input':str(source.relative_to(ROOT)),
      'input_sha256':sha(source),'raw_output':f'work/minotaur_breaker/raw/{name}.png',
      'raw_sha256':sha(W/'raw'/f'{name}.png'),'output':str(output.relative_to(ROOT)),
      'output_sha256':sha(output),'prompt_file':f'work/minotaur_breaker/prompts/{name}.txt',**details}
    (R/'ai_jobs'/f'{name}.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
def main():
    source=W/'00_rig_master_rgba.png'; master=np.array(Image.open(source))
    body=np.array(Image.open(W/'01_complete_body_rgba.png'))
    # The isolated arm output was enlarged by the tool: record registration explicitly.
    raw=Image.open(W/'raw/003_far_upper_arm.png').convert('RGB')
    crop=raw.crop((550,560,766,930)).resize((150,250),Image.Resampling.LANCZOS)
    c=np.array(crop);rgb=c.astype(int)
    chroma=(rgb.max(2)-rgb.min(2)>24)&(rgb[:,:,0]>rgb[:,:,2]+20)
    arm=np.zeros((1536,1024,4),np.uint8);arm[550:800,568:718,:3]=c
    arm[550:800,568:718,3]=chroma.astype(np.uint8)*255
    p=save_part('arm_far_upper_completed',arm)
    job('003','003_far_upper_arm',W/'01_complete_body_rgba.png',p,
        {'registration':{'raw_crop':[550,560,766,930],'target_box':[568,550,718,800]},
         'scope':'Only hidden fur upper arm. Original extracted upper arm remains as evidence.',
         'alpha_method':'local brown chroma isolation from baked neutral checker; candidate review required'})
    # Source-visible cape pixels win over AI. New cloth is restricted behind body.
    area=mask('cape_region',[(312,300),(430,360),(418,950),(295,1130),(165,1270),(0,1260),(0,850),(120,500)])
    visible=area&(master[:,:,3]>0)&(body[:,:,3]==0)
    hidden=mask('cape_hidden_completion',[(291,354),(385,391),(411,490),(385,927),(292,1064),(215,1170),(140,1130),(135,673),(185,480)])
    rawcape=Image.open(W/'raw/004_cape.png').convert('RGB')
    reg=rawcape.transform(SIZE,Image.Transform.AFFINE,(1.12,0,-3,0,1.40,-310),Image.Resampling.BICUBIC)
    c=np.array(reg);ci=c.astype(int)
    red=(ci[:,:,0]>ci[:,:,1]*1.35)&(ci[:,:,0]>ci[:,:,2]*1.35)
    fill=hidden&red&~visible
    cape=np.zeros_like(master);cape[fill,:3]=c[fill];cape[fill,3]=255;cape[visible]=master[visible]
    p=save_part('cape',cape)
    job('004','004_cape',source,p,{'source_visible_pixels':int(visible.sum()),'ai_hidden_pixels':int(fill.sum()),
        'visible_source_rgba_changes':int(np.any(cape[visible]!=master[visible],axis=1).sum()),
        'mask':'work/minotaur_breaker/masks/cape_hidden_completion.png',
        'registration_output_to_raw':[1.12,0,-3,0,1.4,-310]})
    # Retain existing equipment completion, remove only the identified forearm remnant.
    axe=np.array(Image.open(W/'axe_visible_input.png'))
    rawaxe=np.array(Image.open(W/'raw/002_axe_grip.png').convert('RGB'))
    repair=np.array(Image.open(W/'masks/axe_grip_completion.png'))>0
    colored=rawaxe.max(2).astype(int)-rawaxe.min(2).astype(int)>24
    fill=repair&(axe[:,:,3]==0)&colored
    axe[fill,:3]=rawaxe[fill];axe[fill,3]=255
    cut=mask('axe_forearm_fragment_cleanup',[(650,702),(673,709),(700,747),(709,780),(684,786),(647,751)])
    axe[cut]=0;p=save_part('axe',axe)
    record=json.loads((R/'ai_jobs/002_axe_grip.json').read_text())
    record['output_sha256']=sha(p);record['reviewed_forearm_fragment_cleanup_mask']='work/minotaur_breaker/masks/axe_forearm_fragment_cleanup.png'
    (R/'ai_jobs/002_axe_grip.json').write_text(json.dumps(record,indent=2)+'\n')
    sheet=Image.new('RGB',(1024,768),'#aaa');d=ImageDraw.Draw(sheet)
    for i,n in enumerate(['arm_far_upper_completed','cape','axe']):
        im=Image.open(W/'candidates/parts'/f'{n}.png');b=Image.new('RGBA',SIZE,'#808080');b.alpha_composite(im)
        b.thumbnail((330,710));sheet.paste(b.convert('RGB'),(i*340,38));d.text((i*340+5,10),n,fill='black')
    sheet.save(R/'supplement_candidates_review.png')
    # Missing knee-back anatomy revealed by native bending, independent support layers.
    raw=Image.open(W/'raw/005_knee_support.png').convert('RGB');rgb=np.array(raw);ci=rgb.astype(int)
    foreground=(ci[:,:,0]-ci[:,:,2]>26)&(ci[:,:,0]>ci[:,:,1]*1.12)
    yy,xx=np.where(foreground);bbox=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1))
    rgba=np.dstack([rgb,foreground.astype(np.uint8)*255]);rgba[~foreground,:3]=0
    tile=Image.fromarray(rgba).crop(bbox)
    outputs=[]
    for side,box in [('near',(200,1000,430,1190)),('far',(455,1010,685,1200))]:
        x,y,x1,y1=box;part=Image.new('RGBA',SIZE);part.alpha_composite(tile.resize((x1-x,y1-y),Image.Resampling.LANCZOS),(x,y))
        p=save_part('knee_'+side+'_support',np.array(part));part.getchannel('A').save(W/'masks'/('knee_'+side+'_support.png'))
        outputs.append({'file':str(p.relative_to(ROOT)),'sha256':sha(p),'target_box':box})
    job('005','005_knee_support',source,W/'candidates/parts/knee_near_support.png',{'outputs':outputs,'raw_crop':bbox,'scope':'Hidden knee backs exposed by native bend; rendered behind original cape and armor. Not a replacement for knee armor.','shared_completion':'Both knee support layers use the same generated fur-joint patch with separate registration.'})
    print('Equipment, far upper arm, and two knee support candidates saved; not promoted.')
if __name__=='__main__':main()
