"""Native joint transition weights; exact source UVs and unchanged PNGs."""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
import build_cretan_archer_local_skinning as grid_builder
# 24 source pixels = approximately 6 displayed pixels at the larger combat size.
# Texture UVs remain exact; grid density only controls local bone interpolation.
grid_builder.GRID_STEP=24
mesh_grid=grid_builder.mesh_grid
ROOT=Path(__file__).resolve().parents[1]
SPECS=[
 ('knee_near_support','leg_near_thigh','leg_near_shin',1090,1140,None,0,1),
 ('knee_far_support','leg_far_thigh','leg_far_shin',1110,1160,None,0,1),
 ('arm_near_upper','torso','arm_near_upper',490,550,'arm_near_fore',625,685),
 ('arm_near_fore','arm_near_upper','arm_near_fore',625,685,None,0,1),
 ('arm_far_upper','torso','arm_far_upper',550,610,'arm_far_fore',725,785),
 ('arm_far_fore','arm_far_upper','arm_far_fore',725,785,None,0,1),
 ('leg_near_thigh','leg_near_thigh','leg_near_shin',1090,1140,None,0,1),
 ('leg_near_shin','leg_near_thigh','leg_near_shin',1090,1140,None,0,1),
 ('leg_far_thigh','leg_far_thigh','leg_far_shin',1110,1160,None,0,1),
 ('leg_far_shin','leg_far_thigh','leg_far_shin',1110,1160,None,0,1),
 ('foot_near','leg_near_shin','foot_near',1325,1400,None,0,1),
 ('foot_far','leg_far_shin','foot_far',1335,1400,None,0,1),
 ('cape','cape_root','cape_mid',480,760,'cape_tip',900,1120)]
def smooth(v):v=np.clip(v,0,1);return v*v*(3-2*v)
def main():
 records=[]
 for part,stationary,moving,start,end,extra,low,high in SPECS:
  path=ROOT/'work/minotaur_breaker/candidates/native_parts'/f'{part}.png'
  vertices,triangles=mesh_grid(np.array(Image.open(path))[:,:,3]);t=smooth((vertices[:,1]-start)/(end-start));u=smooth((vertices[:,1]-low)/(high-low)) if extra else np.zeros_like(t)
  weights={stationary:(1-t),moving:t*(1-u)}
  if extra:weights[extra]=t*u
  if part in ['leg_near_thigh','leg_far_thigh']:
   # The top edge remains under the skirt while the femur turns below it.
   start=935 if part=='leg_near_thigh' else 950
   root=1-smooth((vertices[:,1]-start)/65.)
   weights={bone:value*(1-root) for bone,value in weights.items()}
   weights['pelvis']=root
  assert np.allclose(sum(weights.values()),1)
  records.append({'part':part,'texture_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'vertices':vertices.tolist(),'uv':vertices.tolist(),'triangles':triangles,'weights':{k:v.tolist() for k,v in weights.items()}})
 (ROOT/'resources/minotaur_breaker_skinning_candidates.json').write_text(json.dumps({'status':'CANDIDATE_MOTION_REVIEW_REQUIRED','texture_changes':0,'meshes':records},indent=2)+'\n')
 print('Native joint/cape meshes:',len(records))
if __name__=='__main__':main()
