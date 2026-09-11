import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from rg_common import *
from PIL import ImageFilter
# Actual returned silhouette, traced at 3x. Limited to distal bracer and fist.
points=[(686,660),(706,668),(720,679),(727,697),(729,718),(742,745),(751,756),(760,774),(763,786),(773,798),(781,813),(786,827),(782,840),(773,850),(761,859),(748,864),(733,862),(724,855),(718,844),(712,836),(710,825),(716,811),(715,798),(718,783),(707,773),(695,766),(675,753),(664,739),(650,731),(647,709)]
scale=4
m=Image.new('L',(4096,6144)); d=ImageDraw.Draw(m); d.polygon([(x*scale,y*scale) for x,y in points],fill=255)
m=m.resize((1024,1536),Image.Resampling.LANCZOS)
# Generated hand is warm skin/brown leather; pale neutral pixels at this
# traced boundary are baked checkerboard, verified against the raw close-up.
rgb=np.array(Image.open(ROOT/'work/raw/001_remove_shield.png')).astype(int)
ma=np.array(m)
neutral=(rgb.max(axis=2)-rgb.min(axis=2)<35)&(rgb.mean(axis=2)>75)
ma[neutral]=0
m=Image.fromarray(ma)
m.save(ROOT/'work/masks/001_generated_hand_matte.png')
allowed=mask('work/masks/remove_shield.png'); d=ImageDraw.Draw(allowed)
d.polygon([(694,755),(730,751),(769,766),(792,798),(796,847),(766,880),(711,876),(697,848),(697,792)],fill=255)
d.rectangle((780,400,1023,1300),fill=255)
allowed.save(ROOT/'work/masks/remove_shield.png')
write('work/masks/001_generated_hand_matte.json',{'status':'VISUALLY_TRACED','method':'4x supersampled polygon based on actual raw output silhouette; no generated pixels outside edit region are retained','raw_sha256':sha('work/raw/001_remove_shield.png'),'points':points,'canvas':[1024,1536],'caution':'Boundary remains subject to art review; raw tool output has baked checkerboard.'})
print('Stage A matte and wrist context ready')
