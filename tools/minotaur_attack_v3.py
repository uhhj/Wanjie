"""Lower shaft grips, extended strike and direct (non-spinning) recovery."""
import math
import numpy as np

def build_attack(m):
    times=np.linspace(0,2.1,211);poses=[];previous={}
    # The axe artwork remains unchanged. Translate only its attachment during
    # regripping: primary source (798,1102), support source (772,1322).
    shaft_shift=np.array([23.,-240.]);separation=np.array([-26.,220.])
    for t in times:
        p=m.base()
        values=m.lerp_keys(t,[(0,[821,862,0,0,0,0]),(.22,[490,710,40,-8,25,-3]),
            (.64,[430,230,-60,10,15,-14]),(.78,[430,230,-60,10,15,-14]),
            (.98,[925,640,90,45,60,24]),(1.12,[730,900,140,45,110,36]),
            (1.26,[723,900,140,45,112,36]),(1.52,[620,800,70,15,38,12]),
            (1.80,[700,840,25,0,8,0]),(2.1,[821,862,0,0,0,0])])
        x,y,angle,px,py,torso=values
        weight=float(m.lerp_keys(t,[(0,[0]),(.22,[1]),(1.26,[1]),(1.80,[0]),(2.1,[0])])[0])
        shaft_weight=float(m.lerp_keys(t,[(0,[0]),(.22,[1]),(1.52,[1]),(2.1,[0])])[0])
        shoulder=m.lerp_keys(t,[(0,[0,0,0,0,0,0]),(.22,[0,0,0,0,0,0]),
            (.64,[80,-110,-65,-100,-28,25]),(.78,[80,-110,-65,-100,-28,25]),
            (.98,[70,0,0,-10,-12,10]),(1.12,[50,20,25,10,-8,-5]),
            (1.26,[50,20,25,10,-8,-5]),(1.52,[0,0,0,0,0,0]),(2.1,[0,0,0,0,0,0])])
        p['pelvis_offset']=[px,py];p['rotations']['torso']=float(torso);p['rotations']['head']=float(-torso*.35)
        p['bone_offsets']={'arm_near_upper':shoulder[:2].tolist(),'arm_far_upper':shoulder[2:4].tolist(),'axe_socket':(shaft_shift*shaft_weight).tolist()}
        p['rotations']['shoulder_near']=float(shoulder[4]);p['rotations']['shoulder_far']=float(shoulder[5])
        a=math.radians(angle);primary=np.array([x,y]);support=primary+m.rot(separation,a)
        for side,point,offset in [('far',primary,np.array([43.,12.])),('near',support,np.array([4.,55.]))]:
            target=point-m.rot(offset,a);orientation=angle
            if side=='near':
                rest=m.fk(p,'hand_near')[0]
                if t<.22:target=np.array([490,710])+m.rot(separation-offset,math.radians(40))
                elif t>1.26:target=np.array([723,900])+m.rot(separation-offset,math.radians(140))
                target=rest*(1-weight)+target*weight
                orientation=torso*(1-weight)+angle*weight
            m.solve(p,'arm_'+side+'_upper','arm_'+side+'_fore','hand_'+side,target,orientation,1,f'attack_v3:{t:.3f}')
            for bone in ['arm_'+side+'_upper','arm_'+side+'_fore','hand_'+side]:
                v=p['rotations'][bone];anchor=previous.get(bone,0.);v=anchor+(v-anchor+180)%360-180
                previous[bone]=v
                # Interpolate target position, never multiply unwrapped angles.
                p['rotations'][bone]=float(v)
        p['rotations']['cape_mid']=float(-torso*.20);p['rotations']['cape_tip']=float(-torso*.35)
        targets={s:np.array(m.B['foot_'+s]['pivot'],float) for s in ['near','far']}
        m.legs(p,targets,{'near':0,'far':0},f'attack_v3:{t:.3f}')
        poses.append(p)
    return {'length':2.1,'loop':False,'times':times.tolist(),'poses':poses,'method_events':[{'time':1.06,'method':'_event_attack_hit'}]}
