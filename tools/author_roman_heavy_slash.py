"""Author only Roman Guard attack keys; preserve art, rig and other animations."""
import json,copy,math
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
def rotation(a):
 a=math.radians(a);return np.array([[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]])
def main():
 path=ROOT/'resources/roman_guard_animations_v1.json';animations=json.loads(path.read_text(encoding='utf-8'))
 bones=json.loads((ROOT/'resources/human_medium_rig_v1.json').read_text(encoding='utf-8'))['bones']
 base=copy.deepcopy(animations['attack_01']['poses'][0])
 # time, pelvis X/Y, pelvis/torso, upper/fore/hand, shield arm, cape
 keys=[(0,0,0,0,0,0,0,0,0,0),(.16,-10,6,-2,-5,-55,-35,15,-12,-2),
 (.34,-12,9,-3,-7,-130,-50,40,-20,-25),(.42,-5,7,-1,-3,-128,-42,34,-23,-30),
 (.52,18,12,3,11,-95,-5,70,-27,-35),(.60,22,14,4,12,-65,5,65,-22,-40),
 (.72,18,11,3,8,-25,0,30,-18,-30),(.90,8,6,1,3,4,-5,0,-8,-8),(1.2,0,0,0,0,0,0,0,0,0)]
 times=sorted(set([round(float(t),5) for t in np.linspace(0,1.2,121)]+[k[0] for k in keys]));poses=[]
 max_error=0
 for t in times:
  j=next((i for i in range(len(keys)-1) if keys[i][0]<=t<=keys[i+1][0]),len(keys)-2)
  a,b=keys[j],keys[j+1];u=(t-a[0])/(b[0]-a[0]);u=u*u*(3-2*u);v=np.array(a[1:])*(1-u)+np.array(b[1:])*u
  dx,dy,pr,tr,up,fore,hand,shield,cape=v;p=copy.deepcopy(base);r=p['rotations'];p['pelvis_offset']=[dx,dy]
  r.update(pelvis=pr,torso=tr,head=-(pr+tr)*.72,arm_near_upper=up,arm_near_fore=fore,hand_near=hand,arm_far_upper=shield,arm_far_fore=shield*.6,hand_far=-shield*1.6-pr-tr,cape_root=cape,cape_mid=cape*.15,cape_tip=cape*.08)
  # Two-bone legs solve to unchanged world ankles; plate remains thigh-aligned.
  for side in ['near','far']:
   thigh='leg_'+side+'_thigh';knee='knee_'+side;shin='leg_'+side+'_shin';foot='foot_'+side
   hip0=np.array(bones[thigh]['pivot']);k=np.array(bones[knee]['pivot']);f=np.array(bones[foot]['pivot']);pel=np.array(bones['pelvis']['pivot'])
   hip=pel+np.array([dx,dy])+rotation(pr)@(hip0-pel);v0=k-hip0;v1=f-k;delta=f-hip;l0=np.linalg.norm(v0);l1=np.linalg.norm(v1)
   sign=1 # Both knees flex toward the direction of travel; do not mirror the rear leg.
   c=(delta@delta-l0*l0-l1*l1)/(2*l0*l1)
   if c>1.00001:raise ValueError('unreachable planted ankle')
   bend=sign*math.acos(float(np.clip(c,-1,1)));ang=math.atan2(delta[1],delta[0])-math.atan2(l1*math.sin(bend),l0+l1*math.cos(bend))
   world0=math.degrees(ang-math.atan2(v0[1],v0[0]));world1=math.degrees(ang+bend-math.atan2(v1[1],v1[0]))
   r[thigh]=world0-pr;r[knee]=0;r[shin]=world1-world0;r[foot]=-world1
   error=np.linalg.norm(hip+rotation(world0)@v0+rotation(world1)@v1-f);max_error=max(max_error,float(error))
  if t==0 or t==1.2:p=copy.deepcopy(base)
  poses.append(p)
 animations['attack_01']={'length':1.2,'loop':False,'times':times,'poses':poses,'method_events':[{'time':.52,'node':'RigEventRelay','method':'_event_attack_hit'}],'motion':'whole-body heavy downward slash','planted_ankle_error_source_px':max_error}
 path.write_text(json.dumps(animations,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('Planted ankle max error',max_error)
if __name__=='__main__':main()
