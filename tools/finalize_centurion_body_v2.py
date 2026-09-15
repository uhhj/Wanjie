"""Reproduce localized V2 neck/thigh patch; never replace frozen source."""
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];w=ROOT/'work/roman_centurion'
a=np.array(Image.open(w/'02_residue_fixed_candidate.png'));raw=np.array(Image.open(w/'raw/004_local_neck_thigh.png').convert('RGB'));src=np.array(Image.open(w/'00_master_rgba.png'))
for name in ['fix_neck_v2','fix_thigh_v2']:
 weight=np.array(Image.open(w/'masks'/f'{name}.png'))/255.;weight*=a[:,:,3]>0
 a[:,:,:3]=np.rint(a[:,:,:3]*(1-weight[:,:,None])+raw*weight[:,:,None]).astype('uint8')
z=Image.new('L',(1024,1536));d=ImageDraw.Draw(z);d.polygon([(349,589),(349,615),(342,644),(331,663),(323,680),(318,711),(318,776),(318,809),(307,835),(299,870),(301,887),(291,886),(298,835),(309,810),(309,711),(320,670),(334,634),(338,589)],fill=255)
colors=a[:,:,:3].astype(int);red=(colors[:,:,0]>colors[:,:,1]*1.7)&(abs(colors[:,:,1]-colors[:,:,2])<20);sel=(np.array(z)>0)&red;a[sel,3]=0
Image.fromarray(sel.astype('uint8')*255).save(w/'masks/exterior_cape_cleanup_v2.png')
a[:350]=src[:350];a[a[:,:,3]==0,:3]=0
protected=np.array(Image.open(w/'masks/protect_face_hand_v2.png'))>0;a[protected]=src[protected]
Image.fromarray(a).save(w/'03_complete_body_v2.png')
