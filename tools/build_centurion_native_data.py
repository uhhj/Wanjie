"""Retarget shared native bones and author six baked keyframe animations."""
import math,json
import numpy as np
import build_centurion_parts as art
p=art.p
def rot(deg):
 a=math.radians(deg);return np.array([[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]])
def smooth(x):return x*x*(3-2*x)
def main():
 p.verify();assert p.read('tools/roman_centurion_parts_manifest.json')['status']=='PASS'
 for folder in ['resources','scripts/build','scripts/rig','scripts/tests','scenes/units/odyssey/roman_centurion',p.R+'native/frames']:(p.ROOT/folder).mkdir(parents=True,exist_ok=True)
 shared=p.read('resources/human_medium_rig_v1.json');parents={n:v['parent'] for n,v in shared['bones'].items()};points={n:v['pivot'] for n,v in shared['bones'].items()}
 points.update({n:xy for n,xy in art.PIVOTS.items() if n in points});points.update(neck=[590,394],head=[589,386],cape_root=[570,423],cape_mid=[330,700],cape_tip=[210,1030],sword_socket=[351,857],shield_socket=[962,578])
 bones={}
 for n,parent in parents.items():
  point=np.array(points[n],float);pp=np.array(points[parent],float) if parent else np.zeros(2);local=point-pp
  children=[np.array(points[k])-point for k,par in parents.items() if par==n and points[k]!=points[n]];d=children[0] if children else [0,25]
  bones[n]={'parent':parent,'path':(bones[parent]['path']+'/' if parent else '')+n,'pivot':point.tolist(),'local_position':local.tolist(),'length':max(8.,float(np.linalg.norm(d))),'bone_angle':math.atan2(d[1],d[0])}
 attachments={n:n for n in art.ORDER};attachments.update(helmet='head',sword='sword_socket',cape='cape_root',cape_front='torso')
 p.save('resources/roman_centurion_rig_v1.json',{'id':'HUMAN_MEDIUM_RIG_V1','unit_id':'OD_UNIT_03_ROMAN_CENTURION','shared_source':'scenes/rigs/human_medium_rig_v1.tscn','shared_source_sha256':p.sha('scenes/rigs/human_medium_rig_v1.tscn'),'bones':bones,'attachments':attachments,'draw_order':art.ORDER,'origin':[605,1476],'body_height':1425,'source_canvas':[1024,1536]})
 anims={}
 def new(n,length,times,loop=False):
  a={'length':length,'loop':loop,'times':times,'poses':[]};anims[n]=a
  for t in times:a['poses'].append({'rotations':{n:0. for n in bones},'pelvis_offset':[0.,0.],'hip_offsets':{'near':[0.,0.],'far':[0.,0.]},'visual_rotation':0.,'visual_offset':[0.,0.]})
  return a
 a=new('idle',1.6,[i*.2 for i in range(9)],True)
 for i,pose in enumerate(a['poses']):
  v=math.sin(i*math.pi/4);pose['pelvis_offset']=[.4*v,1.8*v];pose['rotations'].update(torso=.2*v,head=-.16*v,arm_near_upper=.4*v,arm_far_upper=-.25*v,cape_root=.25*v)
 a['poses'][-1]=json.loads(json.dumps(a['poses'][0]))
 def leg_solve(pose,side,ankle,bend):
  h=np.array(points['leg_'+side+'_thigh'],float)+pose['pelvis_offset'];k=np.array(points['knee_'+side],float);f=np.array(points['foot_'+side],float)
  v0=k-np.array(points['leg_'+side+'_thigh']);v1=f-k;l0=np.linalg.norm(v0);l1=np.linalg.norm(v1)
  reach2=l0*l0+l1*l1+2*l0*l1*math.cos(bend);dx=ankle[0]-h[0]
  assert reach2>dx*dx
  h[1]=ankle[1]-math.sqrt(reach2-dx*dx);pose['hip_offsets'][side]=(h-np.array(points['leg_'+side+'_thigh'])-pose['pelvis_offset']).tolist()
  d=ankle-h;upper=math.atan2(d[1],d[0])-math.atan2(l1*math.sin(bend),l0+l1*math.cos(bend))
  thigh=math.degrees(upper-math.atan2(v0[1],v0[0]));shin=math.degrees(upper+bend-math.atan2(v1[1],v1[0]))-thigh
  pose['rotations']['leg_'+side+'_thigh']=thigh;pose['rotations']['leg_'+side+'_shin']=shin
  return thigh+shin
 def walk_leg(pose,side,ankle):
  # Fixed anatomical hip lane; solve thigh and shin together, not ankle-only pitch.
  hip=np.array(points['leg_'+side+'_thigh'],float)+pose['pelvis_offset']
  hip[1]+=50 if side=='near' else 65
  pose['hip_offsets'][side]=[0.,50. if side=='near' else 65.]
  v0=np.array(points['knee_'+side])-np.array(points['leg_'+side+'_thigh'])
  v1=np.array(points['foot_'+side])-np.array(points['knee_'+side])
  l0=np.linalg.norm(v0);l1=np.linalg.norm(v1);d=ankle-hip
  cosine=(d@d-l0*l0-l1*l1)/(2*l0*l1)
  assert -1<cosine<1,(side,cosine)
  bend=math.acos(cosine)
  upper=math.atan2(d[1],d[0])-math.atan2(l1*math.sin(bend),l0+l1*math.cos(bend))
  thigh=math.degrees(upper-math.atan2(v0[1],v0[0]))
  total=math.degrees(upper+bend-math.atan2(v1[1],v1[0]))
  pose['rotations']['leg_'+side+'_thigh']=thigh
  pose['rotations']['leg_'+side+'_shin']=total-thigh
  return total
 a=new('walk',1.05,[i*1.05/64 for i in range(65)],True);a['root_motion_source_px_per_cycle']=280.;contacts=[]
 for i,pose in enumerate(a['poses']):
  phase=i/64;v=math.sin(2*math.pi*phase);pose['pelvis_offset']=[1.2*v,2.5*(1-math.cos(4*math.pi*phase))]
  pose['rotations'].update(torso=.65*v,head=-.55*v,arm_near_upper=-4.5*v,arm_near_fore=1.5*v,arm_far_upper=1.0*v,cape_root=1.0*math.sin(2*math.pi*phase-.35))
  for side,offset,contact in [('near',.5,[13,123]),('far',0.,[45,91])]:
   u=(phase+offset)%1;support=u<.6
   front=675 if side=='near' else 829
   if support:x=front-280*u;lift=0.;pitch=0.
   else:
    s=(u-.6)/.4;x=front-168+168*smooth(s);lift=55*math.sin(math.pi*s)**1.5;pitch=-5*math.sin(2*math.pi*s)
   foot=np.array([x,1476-lift]);ankle=foot-rot(pitch)@np.array(contact);total=walk_leg(pose,side,ankle)
   pose['rotations']['foot_'+side]=pitch-total
   if i<64:contacts.append({'time':a['times'][i],'side':side,'support':support,'support_id':int(math.floor(phase+offset)),'contact_local':contact,'expected_world_contact':(foot+np.array([phase*280,0])).tolist()})
 a['poses'][-1]=json.loads(json.dumps(a['poses'][0]));p.save('resources/roman_centurion_walk_contacts.json',{'samples':contacts})
 a=new('attack_01',1.05,[0,.16,.3,.43,.53,.65,.83,1.05])
 for pose,arm,fore,hand,torso,px,py in zip(a['poses'],[0,-75,-150,-135,-85,-20,-4,0],[0,30,55,25,-5,-10,-4,0],[0,-25,-35,-25,30,10,0,0],[0,-6,-11,-5,19,22,7,0],[0,-10,-20,-8,38,45,15,0],[0,6,12,16,24,20,6,0]):
  pose['rotations'].update(arm_near_upper=arm,arm_near_fore=fore,hand_near=hand,torso=torso,head=-torso*.6,arm_far_upper=-abs(torso)*1.4,cape_root=-torso*.3);pose['pelvis_offset']=[px,py]
  for side in ['near','far']:
   total=leg_solve(pose,side,np.array(points['foot_'+side],float),math.radians(10+py*.6));pose['rotations']['foot_'+side]=-total
 a['method_events']=[{'time':.53,'method':'_event_attack_hit'}]
 a=new('hit',.32,[0,.08,.16,.24,.32])
 for pose,v in zip(a['poses'],[0,1,-.2,.1,0]):pose['rotations'].update(torso=-4*v,head=-1*v,arm_far_upper=3*v,cape_root=1.5*v)
 a=new('death',1.3,[0,.14,.3,.48,.67,.9,1.12,1.3])
 for pose,fold,roll,down in zip(a['poses'],[0,-4,12,24,35,25,15,15],[0,0,0,8,27,65,86,86],[0,8,25,72,148,230,270,270]):
  v=down/270;pose['rotations'].update(torso=fold,head=10*v,arm_near_upper=-40*v,arm_near_fore=-35*v,hand_near=20*v,arm_far_upper=25*v,arm_far_fore=20*v,leg_near_thigh=-40*v,leg_near_shin=52*v,foot_near=-roll-12*v,leg_far_thigh=-25*v,leg_far_shin=50*v,foot_far=-roll-25*v,cape_root=-fold*.2)
  pose['pelvis_offset']=[15*v,down];pose['visual_rotation']=roll;pose['visual_offset']=[150*v,-80*v]
 a=new('skill_command',1.7,[0,.18,.42,.68,.9,1.14,1.4,1.7])
 for pose,v,arm,fore,hand in zip(a['poses'],[0,.15,.65,1,1,1,.5,0],[0,25,85,125,125,125,65,0],[0,8,30,65,65,65,25,0],[0,5,18,35,35,35,15,0]):
  pose['pelvis_offset']=[2*v,-4*v];pose['rotations'].update(torso=-2.5*v,head=-2*v,arm_near_upper=arm,arm_near_fore=fore,hand_near=hand,arm_far_upper=-25*v,arm_far_fore=-13*v,hand_far=15*v,cape_root=-1.5*v)
 a['method_events']=[{'time':.82,'method':'_event_command_release'}]
 p.save('resources/roman_centurion_animations_v1.json',anims)
 print('Authored 23-bone retarget and six animation candidates; no shared rig changes')
if __name__=='__main__':main()
