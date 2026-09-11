import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from ai_inpaint_roman_guard import *
# White everywhere because only the narrowly drawn sword mask is sampled.
# This traced gap follows the ACTUAL returned skirt and inner leg silhouettes.
points=[(471,1004),(489,1008),(510,1015),(535,1017),(557,1020),(565,1038),(572,1060),(579,1080),(578,1104),(568,1129),(550,1156),(453,1156),(416,1103),(444,1061),(462,1027)]
s=4; m=Image.new('L',(4096,6144),255); d=ImageDraw.Draw(m)
d.polygon([(x*s,y*s) for x,y in points],fill=0)
m=m.resize((1024,1536),Image.Resampling.LANCZOS)
# Neutral pale checker pixels in the gap boundary, never applied to armor areas.
rgb=np.array(Image.open(ROOT/'work/raw/002_remove_sword.png')).astype(int)
ma=np.array(m); yy,xx=np.indices(ma.shape)
roi=(xx>442)&(xx<586)&(yy>998)&(yy<1130)
ma[roi&(rgb.max(axis=2)-rgb.min(axis=2)<25)&(rgb.mean(axis=2)>140)]=0
Image.fromarray(ma).save(ROOT/'work/masks/002_generated_body_matte.png')
j=import_result(stage_for('002_remove_sword'),ROOT/'work/raw/002_remove_sword.png','work/masks/002_generated_body_matte.png','Only sword pixels sampled. Actual inner-leg gap traced; pale neutral checker pixels excluded only inside that gap ROI. No generic white/gray removal from armor.')
print(j['output_sha256'])
sheet([('Sword occlusion repair',rgba('work/02_no_shield_no_sword.png').crop((230,790,721,1140)))],'reports/002_sword_area_review.png',1,(600,450))
