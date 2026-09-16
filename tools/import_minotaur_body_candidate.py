from pathlib import Path
import json,hashlib,numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
W=ROOT/'work/minotaur_breaker';R=ROOT/'reports/minotaur_breaker';src=np.array(Image.open(W/'00_rig_master_rgba.png'));raw=np.array(Image.open(W/'raw/001_complete_body.png').convert('RGB'));mask=np.array(Image.open(W/'masks/body_completion.png'))>0
neutral=(raw.max(2).astype(int)-raw.min(2).astype(int)<24)&(raw.min(2)>65)
flood=Image.fromarray(np.where(neutral,255,0).astype('uint8')).copy()
for seed in [(0,0),(1023,0),(0,1535),(1023,1535)]:
 if flood.getpixel(seed)==255:ImageDraw.floodfill(flood,seed,128)
alpha=np.where(np.array(flood)==128,0,255).astype('uint8');candidate=src.copy();candidate[mask,:3]=raw[mask];candidate[mask,3]=alpha[mask];# Remove only reviewed trailing-cape slivers, never armor/fur.
cleanup=Image.new('L',(1024,1536));cd=ImageDraw.Draw(cleanup)
for poly in [[(117,545),(172,477),(173,522),(143,586),(116,621)],[(177,1050),(246,1007),(235,1064),(211,1127),(178,1170)]]:
 cd.polygon(poly,fill=255)
cut=np.array(cleanup)>0;candidate[cut,3]=0;mask|=cut
# Isolated background specks cannot serve as body parts. Keep connected body.
connected=Image.fromarray(np.where(candidate[:,:,3]>0,255,0).astype('uint8')).copy()
ImageDraw.floodfill(connected,(510,600),128)
specks=(candidate[:,:,3]>0)&(np.array(connected)!=128)
candidate[specks,3]=0;mask|=specks
Image.fromarray(np.where(mask,255,0).astype('uint8')).save(W/'masks/body_completion_effective.png')
Image.fromarray(candidate).save(W/'candidates/01_body_local_candidate.png')
review=Image.new('RGB',(1024,820),'#808080')
for i,a in enumerate([src,candidate]):
 b=Image.new('RGBA',(1024,1536),'#808080');b.alpha_composite(Image.fromarray(a));b.thumbnail((512,768));review.paste(b.convert('RGB'),(i*512,30))
review.save(R/'complete_body_candidate_review.png')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
record={'job':'001_complete_body','input_file':str(W/'00_rig_master_rgba.png'),'input_sha256':sha(W/'00_rig_master_rgba.png'),'mask':str(W/'masks/body_completion_effective.png'),'prompt_file':str(W/'prompts/001_complete_body.txt'),'tool':'built-in image_gen','raw_output':str(W/'raw/001_complete_body.png'),'raw_sha256':sha(W/'raw/001_complete_body.png'),'raw_format':'RGB with baked checker; not approved as formal RGBA','candidate':str(W/'candidates/01_body_local_candidate.png'),'candidate_sha256':sha(W/'candidates/01_body_local_candidate.png'),'outside_mask_rgba_changes':int(np.any(src!=candidate,2)[~mask].sum()),'status':'CANDIDATE_REVIEW_REQUIRED','note':'Neutral edge-connected checker segmentation only for local AI regions; master pixels protected outside mask. Raw model output NOT formal art.'}
(R/'ai_jobs/001_complete_body.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
