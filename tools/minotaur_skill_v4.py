"""Skill V4: front-low axe carry; hand and blade stay clear of the body silhouette."""
import math
import numpy as np

def build_skill(m):
    length=4.2;times=np.linspace(0,length,421);poses=[];previous={}
    start=.60;finish=3.48;cycle=.48;stride=480.;stance=.55
    for t in times:
        p=m.base();context=f'skill_v4:{t:.3f}'
        envelope=float(m.lerp_keys(t,[(0,[0]),(.6,[1]),(3.48,[1]),(4.2,[0])])[0])
        running=start<=t<=finish
        elapsed=float(np.clip(t-start,0,finish-start));phase=elapsed/cycle
        p['root_distance']=elapsed*(stride/cycle)
        bounce=-12*math.sin(phase*4*math.pi) if running else 0
        p['pelvis_offset']=[35*envelope,125*envelope+bounce]
        p['rotations']['torso']=56*envelope
        p['rotations']['head']=6*envelope
        angles={}
        targets={}
        for side,offset in [('near',0.),('far',.5)]:
            u=(phase+offset)%1
            if u<stance:
                shift=stride*(stance*.5-u);lift=0;angle=0
            else:
                v=(u-stance)/(1-stance)
                shift=stride*(-stance*.5+stance*m.smooth(v));lift=95*math.sin(math.pi*v);angle=-14*math.sin(math.pi*v)
            target=np.array(m.B['foot_'+side]['pivot'],float);target[0]=(445 if side=='near' else 475)+shift;target[1]-=lift
            rest=np.array(m.B['foot_'+side]['pivot'],float)
            if t<start:
                step=float(np.clip((t-(0.08 if side=='near' else .30))/.28,0,1))
                target=rest+(target-rest)*m.smooth(step);target[1]-=35*math.sin(math.pi*step)
            elif t>finish:
                step=float(np.clip((t-finish-(0 if side=='near' else .32))/.36,0,1))
                target=target+(rest-target)*m.smooth(step);target[1]-=35*math.sin(math.pi*step)
            targets[side]=target;angles[side]=angle*envelope
        m.legs(p,targets,angles,context)
        # Axe carried low in front: the hand sweeps forward-down in the open air
        # ahead of the chest, and the blade hangs beside the leading leg. No
        # bone_offsets: the hand keeps the original grip point on the shaft.
        sway=5*math.sin(phase*2*math.pi) if running else 0
        carry_env=float(m.lerp_keys(t,[(0,[0]),(.60,[1]),(3.48,[1]),(4.2,[0])])[0])
        grip_x=float(m.lerp_keys(t,[(0,[778]),(.18,[770]),(.42,[762]),(.60,[760]),(3.48,[760]),(3.95,[770]),(4.2,[778])])[0])
        grip_y=float(m.lerp_keys(t,[(0,[850]),(.18,[890]),(.42,[935]),(.60,[950]),(3.48,[950]),(3.95,[890]),(4.2,[850])])[0])
        axe_angle=float(m.lerp_keys(t,[(0,[0]),(.18,[45]),(.42,[118]),(.60,[150]),(3.48,[150]),(3.95,[45]),(4.2,[0])])[0])+sway*carry_env
        q=m.base();q['pelvis_offset']=p['pelvis_offset'];q['rotations']['torso']=p['rotations']['torso']
        m.solve(q,'arm_far_upper','arm_far_fore','hand_far',np.array([grip_x,grip_y]),axe_angle,1,context)
        for bone in ['arm_far_upper','arm_far_fore','hand_far']:
            v=q['rotations'][bone];anchor=previous.get(bone,0.);v=anchor+(v-anchor+180)%360-180;previous[bone]=v
            p['rotations'][bone]=float(v)
        p['rotations']['arm_near_upper']=(26+5*math.sin(phase*2*math.pi))*envelope
        p['rotations']['arm_near_fore']=-18*envelope
        p['rotations']['cape_root']=20*envelope
        p['rotations']['cape_mid']=(15+4*math.sin(phase*2*math.pi-.4))*envelope
        p['rotations']['cape_tip']=(12+5*math.sin(phase*2*math.pi-.8))*envelope
        poses.append(p)
    return {'length':length,'loop':False,'times':times.tolist(),'poses':poses,
        'method_events':[{'time':3.24,'method':'_event_skill_hit'}]}
