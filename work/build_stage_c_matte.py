import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from ai_inpaint_roman_guard import *
# Actual generated silhouette; only portions intersecting cape mask are used.
points=[(478,342),(490,330),(542,327),(595,365),(554,382),(575,395),(582,413),(600,423),(619,443),(632,465),(643,495),(652,528),(673,575),(811,763),(811,880),(722,1030),(862,1467),(252,1467),(254,1360),(276,1170),(316,1084),(348,1036),(357,1005),(335,1000),(321,988),(325,969),(333,947),(338,928),(322,920),(306,910),(291,896),(282,879),(282,860),(288,843),(297,830),(292,807),(287,769),(278,739),(273,714),(278,695),(291,676),(287,650),(292,630),(303,608),(312,583),(299,579),(293,566),(301,540),(300,522),(309,501),(313,477),(318,449),(329,424),(346,406),(368,393),(394,385),(417,382),(439,382),(457,374),(464,354),(472,355),(473,347)]
s=4; m=Image.new('L',(4096,6144)); d=ImageDraw.Draw(m); d.polygon([(x*s,y*s) for x,y in points],fill=255)
m=m.resize((1024,1536),Image.Resampling.LANCZOS); m.save(ROOT/'work/masks/003_generated_body_matte.png')
allowed=mask('work/masks/remove_cape.png'); d=ImageDraw.Draw(allowed); d.rectangle((0,340,270,1160),fill=255)
from PIL import ImageFilter
source_rgb=np.array(check_source()).astype(int); yy,xx=np.indices(source_rgb.shape[:2])
cape_red=(xx>280)&(xx<477)&(yy>325)&(yy<426)&(source_rgb[:,:,0]>1.5*source_rgb[:,:,1])&(source_rgb[:,:,0]>1.3*source_rgb[:,:,2])&(source_rgb[:,:,3]>0)
extra=Image.fromarray(cape_red.astype(np.uint8)*255).filter(ImageFilter.MaxFilter(7))
allowed=Image.fromarray(np.maximum(np.array(allowed),np.array(extra)))
# Audit found that red-biased pixels at the helmet/crest rear edge were falsely
# included by the cape-color helper. Restore the frozen head/helmet region.
ImageDraw.Draw(allowed).rectangle((0,0,1023,341),fill=0)
allowed.save(ROOT/'work/masks/remove_cape.png')
j=import_result(stage_for('003_remove_cape'),ROOT/'work/raw/003_remove_cape.png','work/masks/003_generated_body_matte.png','Actual generated neck/shoulder and outer body silhouette traced. Broad coordinates outside cape mask are irrelevant; only mask intersections sampled. RGB checkerboard is not treated as alpha.')
print(j['output_sha256'])
body=rgba('work/03_complete_body_base.png')
sheet([('Frozen Rig Master',check_source()),('Complete body CANDIDATE - NOT APPROVED',body)],'reports/complete_body_review.png')
sheet([('Neck and shoulder',body.crop((270,320,674,601))),('Skirt and thighs',body.crop((280,835,735,1140)))],'reports/complete_body_detail_review.png',2,(520,400))
