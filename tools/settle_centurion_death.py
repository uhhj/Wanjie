"""Fit authored death poses to the actual alpha silhouette floor, not bbox corners."""
import numpy as np
from PIL import Image
import roman_centurion_pipeline as p
from build_centurion_native_data import rot
from build_centurion_skinning import SPECS,weights
def main():
 data=p.read('resources/roman_centurion_rig_v1.json');anims=p.read('resources/roman_centurion_animations_v1.json');origin=np.array(data['origin']);specs={s[0]:s for s in SPECS};samples={}
 for part in data['draw_order']:
  a=np.array(Image.open(p.ROOT/f'assets/units/odyssey/roman_centurion/parts/{part}.png'));y,x=np.where(a[:,:,3]>32);samples[part]=np.column_stack([x,y])[::3]
 rows=[]
 for index,pose in enumerate(anims['death']['poses']):
  v=min(1,abs(pose['visual_rotation'])/86);pose['bone_scales']={'cape_root':[1-.8*v,1.]};fk={}
  for name,rec in data['bones'].items():
   off=np.array(rec['local_position'],float)
   if name=='pelvis':off+=pose['pelvis_offset']
   if name.startswith('leg_') and name.endswith('_thigh'):off+=pose['hip_offsets'][name.split('_')[1]]
   pm,pp=fk[rec['parent']] if rec['parent'] else (np.eye(2),np.zeros(2))
   fk[name]=(pm@rot(pose['rotations'][name])@np.diag(pose.get('bone_scales',{}).get(name,[1,1])),pp+pm@off)
  bottom=-1e9
  def transformed(pts,bone):
   matrix,position=fk[bone];return (pts-np.array(data['bones'][bone]['pivot']))@matrix.T+position
  for part,pts in samples.items():
   if part in ['sword','cape','cape_front']:continue
   if part in specs:
    spec=specs[part];w=weights(pts,spec,data)[:,None];out=transformed(pts,spec[1])*(1-w)+transformed(pts,spec[2])*w
   else:out=transformed(pts,data['attachments'][part])
   out=(out-origin)@rot(pose['visual_rotation']).T
   bottom=max(bottom,float(out[:,1].max()))
  pose['visual_offset'][1]=-bottom
  rows.append({'key':index,'time':anims['death']['times'][index],'floor_correction_source_px':-bottom,'method':'Actual alpha material vertices including native weights'})
 p.save('resources/roman_centurion_animations_v1.json',anims);p.save(p.R+'native/death_floor_keys.json',{'keys':rows,'intermediate_gpu_frames_require_review':True})
if __name__=='__main__':main()
