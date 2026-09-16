"""Large-biped native keyframes. IK bakes rotations, never stretches bones."""
from pathlib import Path
import json,math,hashlib,shutil
import numpy as np
from PIL import Image
from build_minotaur_candidates import ORDER
ROOT=Path(__file__).resolve().parents[1];W=ROOT/'work/minotaur_breaker';R=ROOT/'reports/minotaur_breaker'
DATA=json.loads((ROOT/'resources/minotaur_breaker_rig_v1.json').read_text());B=DATA['bones']
def rot(v,a):
    c,s=math.cos(a),math.sin(a);return np.array([c*v[0]-s*v[1],s*v[0]+c*v[1]])
def base():return {'rotations':dict.fromkeys(B,0.0),'pelvis_offset':[0.,0.],'visual_offset':[0.,0.],'visual_rotation':0.,'root_distance':0.}
def fk(p,name):
    b=B[name];parent=b['parent'];pos,ang=fk(p,parent) if parent else (np.zeros(2),0.)
    local=np.array(b['local_position'],float)
    local+=p.get('bone_offsets',{}).get(name,[0.,0.])
    if name=='pelvis':local+=p['pelvis_offset']
    return pos+rot(local,ang),ang+math.radians(p['rotations'][name])
ISSUES=[]
def solve(p,upper,lower,tip,target,orientation,branch,context):
    origin,_=fk(p,upper);u=np.array(B[lower]['pivot'])-B[upper]['pivot'];v=np.array(B[tip]['pivot'])-B[lower]['pivot']
    l1,l2=np.linalg.norm(u),np.linalg.norm(v);delta=np.array(target)-origin;distance=np.linalg.norm(delta)
    # Avoid hidden stretching: clamp only for candidate generation and report every miss.
    bounded=min(l1+l2-0.01,max(abs(l1-l2)+0.01,distance))
    if abs(distance-bounded)>0.5:ISSUES.append({'context':context,'chain':upper,'reach_error':float(abs(distance-bounded))})
    angle=math.atan2(delta[1],delta[0]);a=angle+branch*math.acos(np.clip((l1*l1+bounded*bounded-l2*l2)/(2*l1*bounded),-1,1))
    joint=origin+rot([l1,0],a);end=origin+delta/max(distance,1e-9)*bounded
    lower_angle=math.atan2(*(end-joint)[::-1]);parent=B[upper]['parent'];parent_angle=fk(p,parent)[1] if parent else 0
    p['rotations'][upper]=math.degrees(a-math.atan2(u[1],u[0])-parent_angle)
    # Knee intermediary is a stationary pivot node; lower inherits upper rotation.
    lower_parent_angle=fk(p,B[lower]['parent'])[1]
    p['rotations'][lower]=math.degrees(lower_angle-math.atan2(v[1],v[0])-lower_parent_angle)
    p['rotations'][tip]=orientation-math.degrees(fk(p,B[tip]['parent'])[1])
def legs(p,targets,angles,context):
    for side in ['near','far']:
        solve(p,'leg_'+side+'_thigh','leg_'+side+'_shin','foot_'+side,targets[side],angles[side],-1,context)
def grip(p,point,angle,context):
    a=math.radians(angle);primary=np.array(point,float);support=primary+rot(np.array(DATA['axe_grips']['support_source'])-DATA['axe_grips']['primary_source'],a)
    far_offset=np.array(DATA['axe_grips']['primary_source'])-B['hand_far']['pivot']
    near_offset=np.array(B['axe_support_socket']['pivot'])-B['hand_near']['pivot']
    for side,target,offset in [('far',primary,far_offset),('near',support,near_offset)]:
        solve(p,'arm_'+side+'_upper','arm_'+side+'_fore','hand_'+side,target-rot(offset,a),angle,1,context)
    p['rotations']['axe_socket']=0
def smooth(x):return x*x*(3-2*x)
def lerp_keys(t,keys):
    for i in range(len(keys)-1):
        if keys[i][0]<=t<=keys[i+1][0]:
            u=smooth((t-keys[i][0])/(keys[i+1][0]-keys[i][0]));return np.array(keys[i][1])*(1-u)+np.array(keys[i+1][1])*u
    return np.array(keys[-1][1])
def main():
    animations={}
    for name,length,count,loop in [('idle',2.0,33,True),('walk',1.4,65,True),('attack_01',1.35,65,False),('skill_01',1.8,81,False),('hit',.4,21,False),('death',1.7,65,False)]:
        times=np.linspace(0,length,count);poses=[]
        for t in times:
            phase=t/length;p=base();context=f'{name}:{t:.4f}'
            if name=='idle':
                w=math.sin(phase*2*math.pi);p['pelvis_offset']=[0,2*w];p['rotations'].update(torso=.35*w,head=-.25*w,cape_mid=.5*w,cape_tip=.7*math.sin(phase*2*math.pi-.25))
            elif name=='walk':
                stride=180.;p['root_distance']=stride*phase;p['pelvis_offset']=[1.5*math.sin(phase*2*math.pi),20+4*math.cos(phase*4*math.pi)]
                p['rotations']['pelvis']=.55*math.sin(phase*2*math.pi);p['rotations']['torso']=-p['rotations']['pelvis']*.8;p['rotations']['head']=-.1*math.sin(phase*2*math.pi)
                targets={};angles={}
                for side,offset in [('near',0),('far',.5)]:
                    u=(phase+offset)%1;ankle=np.array(B['foot_'+side]['pivot'],float)
                    ankle[0]=448 if side=='near' else 478
                    if u<.62:ankle[0]+=stride*(.31-u);angles[side]=0.
                    else:
                        v=(u-.62)/.38;ankle[0]+=stride*(-.31+.62*smooth(v));ankle[1]-=30*math.sin(math.pi*v);angles[side]=-4*math.sin(math.pi*v)
                    targets[side]=ankle
                legs(p,targets,angles,context)
                p['rotations']['arm_near_upper']=2.5*math.sin(phase*2*math.pi);p['rotations']['arm_near_fore']=-1*math.sin(phase*2*math.pi)
                p['rotations']['cape_mid']=1.1*math.sin(phase*2*math.pi-.4);p['rotations']['cape_tip']=1.6*math.sin(phase*2*math.pi-.7)
            elif name in ['attack_01','skill_01']:
                # Explicit approach to the two-handed hold, wind-up, strike and recovery.
                if name=='attack_01':
                    value=lerp_keys(phase,[(0,[0,490,710,45,0]),(.2,[1,490,710,45,9]),(.43,[1,465,635,-20,13]),(.62,[1,665,745,100,19]),(.76,[1,620,735,85,15]),(1,[0,620,735,85,0])])
                else:
                    value=lerp_keys(phase,[(0,[0,495,725,45,0]),(.18,[1,495,725,45,28]),(.35,[1,495,725,45,30]),(.64,[1,600,740,80,24]),(.77,[1,650,760,105,38]),(1,[0,620,735,85,0])])
                    p['root_distance']=float(220*np.clip((phase-.25)/.43,0,1))
                weight,x,y,angle,sink=value;p['pelvis_offset']=[12*weight,sink];p['rotations']['torso']=3*weight
                if weight>0:
                    q=base();q['pelvis_offset']=p['pelvis_offset'];q['rotations']['torso']=p['rotations']['torso'];grip(q,[x,y],angle,context)
                    # Blending only during approach/release, exact hold while weight is one.
                    for n in ['arm_near_upper','arm_near_fore','hand_near','arm_far_upper','arm_far_fore','hand_far']:
                        p['rotations'][n]=q['rotations'][n]*weight
                targets={s:np.array(B['foot_'+s]['pivot'],float) for s in ['near','far']}
                if name=='skill_01':
                    charge=np.clip((phase-.25)/.43,0,1)
                    envelope=min(1.,phase/.25,max(0.,(1-phase)/.23))
                    for side,offset in [('near',0),('far',.5)]:
                        u=(charge+offset)%1
                        if u<.5:targets[side][0]+=220*(.25-u)*envelope
                        else:
                            swing=(u-.5)*2;targets[side][0]+=(-55+110*smooth(swing))*envelope
                            targets[side][1]-=42*math.sin(math.pi*swing)*envelope
                    if phase<.25:
                        for side,start,sign in [('near',0,1),('far',.125,-1)]:
                            step=np.clip((phase-start)/.125,0,1);targets[side]=np.array(B['foot_'+side]['pivot'],float)
                            targets[side][0]+=55*sign*smooth(step);targets[side][1]-=12*math.sin(math.pi*step)
                    elif phase>.77:
                        for side,start,sign in [('near',.77,1),('far',.885,-1)]:
                            step=np.clip((phase-start)/.115,0,1);targets[side]=np.array(B['foot_'+side]['pivot'],float)
                            targets[side][0]+=55*sign*(1-smooth(step));targets[side][1]-=20*math.sin(math.pi*step)
                legs(p,targets,{'near':0,'far':0},context)
                p['rotations']['head']=-1.5*weight;p['rotations']['cape_mid']=-2*weight;p['rotations']['cape_tip']=-4*weight
            elif name=='hit':
                w=math.sin(math.pi*phase)*(1-phase);p['rotations']['torso']=-6*w;p['rotations']['head']=2*w;p['pelvis_offset']=[-6*w,2*w]
            else:
                sink=float(lerp_keys(phase,[(0,[0]),(.22,[20]),(.5,[105]),(.75,[170]),(1,[170])])[0]);p['pelvis_offset']=[25*phase,sink]
                legs(p,{s:B['foot_'+s]['pivot'] for s in ['near','far']},{'near':0,'far':0},context)
                p['rotations']['torso']=float(lerp_keys(phase,[(0,[0]),(.2,[-8]),(.6,[28]),(1,[27])])[0]);p['rotations']['head']=4*phase
                p['visual_rotation']=float(lerp_keys(phase,[(0,[0]),(.5,[0]),(.88,[76]),(1,[78])])[0]);p['visual_offset']=[-30*phase,float(lerp_keys(phase,[(0,[0]),(.5,[0]),(.58,[-55]),(.66,[-122]),(.78,[-190]),(.88,[-201]),(1,[-201])])[0])]
                p['rotations']['arm_near_upper']=-18*phase;p['rotations']['arm_near_fore']=-25*phase;p['rotations']['cape_mid']=-4*phase
                p['rotations']['cape_root']=-31*phase;p['rotations']['cape_tip']=8*phase
                p['rotations']['axe_socket']=0
                carry=smooth(np.clip(phase/.45,0,1))
                p['rotations']['arm_far_upper']=-45*carry
                p['rotations']['arm_far_fore']=-30*carry
                p['rotations']['hand_far']=75*carry-p['rotations']['torso']
                settle=smooth(np.clip((phase-.5)/.5,0,1))
                final=base();final['pelvis_offset']=[25,170];final['rotations']['torso']=27
                to_final_source=lambda world:np.array(DATA['origin'])+rot(np.array(world)-[-30,-145],math.radians(-78))
                legs(final,{'near':to_final_source([-40,-140]),'far':to_final_source([32,-200])},{'near':12,'far':12},'death_final_contact')
                solve(final,'arm_far_upper','arm_far_fore','hand_far',to_final_source([355,-215]),12,1,'death_final_axe_contact')
                for bone in ['leg_near_thigh','leg_near_shin','foot_near','leg_far_thigh','leg_far_shin','foot_far','arm_far_upper','arm_far_fore','hand_far']:
                    p['rotations'][bone]=p['rotations'][bone]*(1-settle)+final['rotations'][bone]*settle
                axe_world=90*smooth(np.clip((phase-.45)/.20,0,1))
                p['rotations']['hand_far']=axe_world-p['visual_rotation']-math.degrees(fk(p,B['hand_far']['parent'])[1])
            poses.append(p)
        for bone in B:
            a=np.unwrap(np.radians([p['rotations'][bone] for p in poses]))
            for p,v in zip(poses,np.degrees(a)):p['rotations'][bone]=float(v)
        animations[name]={'length':length,'loop':loop,'times':times.tolist(),'poses':poses}
        if name in ['attack_01','skill_01']:animations[name]['method_events']=[{'time':length*(.60 if name=='attack_01' else .73),'method':'_event_attack_hit' if name=='attack_01' else '_event_skill_hit'}]
    from minotaur_heavy_actions_v2 import build_actions
    import sys
    animations.update(build_actions(sys.modules[__name__]))
    (ROOT/'resources/minotaur_breaker_animation_candidates.json').write_text(json.dumps(animations,indent=2)+'\n')
    (R/'candidate_ik_reach.json').write_text(json.dumps({'status':'PASS' if not ISSUES else 'NEEDS_KEYFRAME_REPAIR','scope':'Baked IK reach only; visual motion not approved','issues':ISSUES},indent=2)+'\n')
    DATA['draw_order']=ORDER;DATA['attachments']={'cape':'cape_root','axe':'axe_socket','knee_near_support':'knee_near','knee_far_support':'knee_far'}
    (ROOT/'resources/minotaur_breaker_rig_v1.json').write_text(json.dumps(DATA,indent=2)+'\n')
    out=W/'candidates/native_parts';out.mkdir(exist_ok=True)
    cut=np.array(Image.open(W/'masks/body_checker_gap_cleanup.png'))>0
    manifest=[]
    for name in ORDER:
        input_name='arm_far_upper_completed' if name=='arm_far_upper' else name
        a=np.array(Image.open(W/'candidates/parts'/f'{input_name}.png'));a[cut,3]=0;a[a[:,:,3]==0,:3]=0
        p=out/f'{name}.png';Image.fromarray(a).save(p);manifest.append({'name':name,'file':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    (W/'candidates/manifest.json').write_text(json.dumps({'status':'CANDIDATE_ONLY','parts':manifest},indent=2)+'\n')
    print('Six animation candidates; IK reach issues:',len(ISSUES))
if __name__=='__main__':main()
