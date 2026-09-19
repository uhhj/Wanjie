"""Attack V4: higher windup, deeper strike with blade ground contact, monotonic recovery."""
import math
import numpy as np

def build_attack(m):
    times=np.linspace(0,2.3,231);poses=[];previous={}
    # The axe artwork remains unchanged. Translate only its attachment during
    # regripping: primary source (798,1102), support source (772,1322).
    shaft_shift=np.array([23.,-240.]);separation=np.array([-26.,220.])
    for t in times:
        p=m.base()
        # primary grip X/Y, axe angle, pelvis X/Y, torso. Contact key keeps the
        # blade tip at source y~1484 (ground 1485): grip deep and low at 155 deg.
        values=m.lerp_keys(t,[(0,[821,862,0,0,0,0]),(.22,[490,710,40,-8,25,-3]),
            (.50,[455,300,-45,10,20,-12]),(.66,[418,190,-70,15,6,-18]),(.80,[418,190,-70,12,6,-18]),
            (0.98,[925,640,90,45,60,24]),(1.14,[780,916,155,60,150,55]),(1.34,[780,916,155,60,158,57]),
            (1.56,[700,930,120,50,110,45]),(1.80,[640,850,60,20,45,18]),(2.05,[700,840,20,4,10,3]),
            (2.30,[821,862,0,0,0,0])])
        x,y,angle,px,py,torso=values
        weight=float(m.lerp_keys(t,[(0,[0]),(.22,[1]),(1.56,[1]),(2.05,[0]),(2.30,[0])])[0])
        shaft_weight=float(m.lerp_keys(t,[(0,[0]),(.22,[1]),(1.56,[1]),(2.05,[0]),(2.30,[0])])[0])
        shoulder=m.lerp_keys(t,[(0,[0,0,0,0,0,0]),(.22,[0,0,0,0,0,0]),
            (.50,[60,-90,-50,-80,-22,20]),(.66,[85,-115,-70,-100,-30,26]),(.80,[85,-115,-70,-100,-30,26]),
            (.98,[70,0,0,-10,-12,10]),(1.14,[45,25,30,15,-6,-5]),(1.34,[45,25,30,15,-6,-5]),
            (1.56,[15,10,10,5,-2,-2]),(1.80,[0,0,0,0,0,0]),(2.30,[0,0,0,0,0,0])])
        p['pelvis_offset']=[px,py];p['rotations']['torso']=float(torso);p['rotations']['head']=float(-torso*.25)
        p['bone_offsets']={'arm_near_upper':shoulder[:2].tolist(),'arm_far_upper':shoulder[2:4].tolist(),'axe_socket':(shaft_shift*shaft_weight).tolist()}
        p['rotations']['shoulder_near']=float(shoulder[4]);p['rotations']['shoulder_far']=float(shoulder[5])
        a=math.radians(angle);primary=np.array([x,y]);support=primary+m.rot(separation,a)
        for side,point,offset in [('far',primary,np.array([43.,12.])),('near',support,np.array([4.,55.]))]:
            target=point-m.rot(offset,a);orientation=angle
            if side=='near':
                rest=m.fk(p,'hand_near')[0]
                if t<.22:target=np.array([490,710])+m.rot(separation-offset,math.radians(40))
                elif t>1.56:target=np.array([700,930])+m.rot(separation-offset,math.radians(120))
                target=rest*(1-weight)+target*weight
                orientation=torso*(1-weight)+angle*weight
            m.solve(p,'arm_'+side+'_upper','arm_'+side+'_fore','hand_'+side,target,orientation,1,f'attack_v4:{t:.3f}')
            for bone in ['arm_'+side+'_upper','arm_'+side+'_fore','hand_'+side]:
                v=p['rotations'][bone];anchor=previous.get(bone,0.);v=anchor+(v-anchor+180)%360-180
                previous[bone]=v
                # Interpolate target position, never multiply unwrapped angles.
                p['rotations'][bone]=float(v)
        p['rotations']['cape_mid']=float(-torso*.20);p['rotations']['cape_tip']=float(-torso*.35)
        targets={s:np.array(m.B['foot_'+s]['pivot'],float) for s in ['near','far']}
        m.legs(p,targets,{'near':0,'far':0},f'attack_v4:{t:.3f}')
        poses.append(p)
    return {'length':2.3,'loop':False,'times':times.tolist(),'poses':poses,'method_events':[{'time':1.14,'method':'_event_attack_hit'}]}
