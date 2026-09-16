"""Local native bindings, unchanged texture pixels and UVs."""
import numpy as np
from PIL import Image
import roman_centurion_pipeline as p
from build_cretan_archer_local_skinning import mesh_grid
SPECS=[('arm_near_upper','torso','arm_near_upper','y',470,560),('arm_far_upper','torso','arm_far_upper','y',530,615),
 ('arm_near_fore','arm_near_upper','arm_near_fore','axis',-10,42),('arm_far_fore','arm_far_upper','arm_far_fore','axis',-10,42),
 ('leg_near_thigh','pelvis','leg_near_thigh','y',970,1050),('leg_far_thigh','pelvis','leg_far_thigh','y',995,1080),
 ('leg_near_shin','knee_near','leg_near_shin','y',1095,1170),('leg_far_shin','knee_far','leg_far_shin','y',1095,1170),
 ('foot_near','leg_near_shin','foot_near','y',1345,1400),('foot_far','leg_far_shin','foot_far','y',1345,1400)]
def weights(vertices,spec,data):
 _,stationary,moving,axis,start,end=spec
 if axis=='y':v=vertices[:,1]
 else:
  a=np.array(data['bones'][moving]['pivot']);child='hand_near' if 'near' in moving else 'hand_far';d=np.array(data['bones'][child]['pivot'])-a;d=d/np.linalg.norm(d);v=(vertices-a)@d
 w=np.clip((v-start)/(end-start),0,1);return w*w*(3-2*w)
def main():
 data=p.read('resources/roman_centurion_rig_v1.json');rows=[]
 for spec in SPECS:
  n,stationary,moving,*_=spec;file='assets/units/odyssey/roman_centurion/parts/'+n+'.png';a=np.array(Image.open(p.ROOT/file));vertices,triangles=mesh_grid(a[:,:,3]);w=weights(vertices,spec,data)
  rows.append({'part':n,'stationary_bone':stationary,'moving_bone':moving,'vertices':vertices.tolist(),'uv':vertices.tolist(),'triangles':triangles,'stationary_weights':(1-w).tolist(),'moving_weights':w.tolist(),'texture_sha256':p.sha(file)})
 p.save('resources/roman_centurion_local_skinning.json',{'rig_sha256':p.sha('resources/roman_centurion_rig_v1.json'),'meshes':rows,'texture_pixels_changed':0})
 print('10 native local bindings; texture RGB and UVs unchanged')
if __name__=='__main__':main()
