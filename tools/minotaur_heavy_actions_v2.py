"""Motion-reference driven actions; existing textures, rig and other clips stay fixed."""
import math
import numpy as np

def build_actions(m):
    result={}
    for name,length,count in [('attack_01',1.8,181),('skill_01',4.2,421)]:
        times=np.linspace(0,length,count);poses=[];previous={}
        for t in times:
            p=m.base();context=f'{name}_v2:{t:.3f}'
            targets={s:np.array(m.B['foot_'+s]['pivot'],float) for s in ['near','far']}
            if name=='attack_01':
                # grip weight, primary grip X/Y, axe angle, pelvis X/Y, torso
                values=m.lerp_keys(t,[(0,[0,490,710,40,0,0,0]),(.22,[1,490,710,40,-8,25,-3]),
                    (.64,[1,470,190,-70,10,15,-14]),(.78,[1,470,190,-70,10,15,-14]),
                    (.94,[1,710,490,70,45,25,12]),(1.08,[1,730,900,145,45,110,36]),
                    (1.22,[1,723,900,155,45,112,36]),(1.48,[1,590,780,90,15,38,12]),
                    (1.8,[0,490,710,40,0,0,0])])
                weight,x,y,angle,px,py,torso=values
                p['pelvis_offset']=[px,py];p['rotations']['torso']=torso
                p['rotations']['head']=-torso*.35
                shoulder=m.lerp_keys(t,[(0,[0,0,0,0,0,0]),(.22,[0,0,0,0,0,0]),
                    (.64,[80,-110,-65,-100,-28,25]),(.78,[80,-110,-65,-100,-28,25]),
                    (.94,[55,-55,-20,-40,-12,10]),(1.08,[50,20,25,10,-8,-5]),
                    (1.22,[50,20,25,10,-8,-5]),(1.48,[0,0,0,0,0,0]),(1.8,[0,0,0,0,0,0])])
                p['bone_offsets']={'arm_near_upper':shoulder[:2].tolist(),'arm_far_upper':shoulder[2:4].tolist()}
                p['rotations']['shoulder_near']=float(shoulder[4]);p['rotations']['shoulder_far']=float(shoulder[5])
                q=m.base();q['pelvis_offset']=[px,py];q['rotations']['torso']=torso
                q['bone_offsets']=p['bone_offsets']
                m.grip(q,[x,y],angle,context)
                for bone in ['arm_near_upper','arm_near_fore','hand_near','arm_far_upper','arm_far_fore','hand_far']:
                    v=q['rotations'][bone];anchor=previous.get(bone,0.)
                    v=anchor+(v-anchor+180)%360-180;previous[bone]=v
                    p['rotations'][bone]=float(v*weight)
                p['rotations']['cape_mid']=-torso*.20;p['rotations']['cape_tip']=-torso*.35
                m.legs(p,targets,{'near':0,'far':0},context)
            else:
                # Six full alternating running cycles, 480 source px each.
                start=.60;finish=3.48;cycle=.48;stride=480.;stance=.55
                envelope=float(m.lerp_keys(t,[(0,[0]),(.6,[1]),(3.48,[1]),(4.2,[0])])[0])
                running=start<=t<=finish
                elapsed=float(np.clip(t-start,0,finish-start));phase=elapsed/cycle
                p['root_distance']=elapsed*(stride/cycle)
                bounce=-12*math.sin(phase*4*math.pi) if running else 0
                p['pelvis_offset']=[35*envelope,105*envelope+bounce]
                p['rotations']['torso']=40*envelope
                p['rotations']['head']=10*envelope
                angles={}
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
                # Retain the axe at the rear flank; horns lead the charge.
                q=m.base();q['pelvis_offset']=p['pelvis_offset'];q['rotations']['torso']=p['rotations']['torso']
                primary=np.array(m.DATA['axe_grips']['primary_source'],float)*(1-envelope)+np.array([430.,860.+bounce])*envelope;axe_angle=-115.*envelope
                offset=np.array(m.DATA['axe_grips']['primary_source'])-m.B['hand_far']['pivot']
                m.solve(q,'arm_far_upper','arm_far_fore','hand_far',primary-m.rot(offset,math.radians(axe_angle)),axe_angle,1,context)
                for bone in ['arm_far_upper','arm_far_fore','hand_far']:
                    v=q['rotations'][bone];anchor=previous.get(bone,0.);v=anchor+(v-anchor+180)%360-180;previous[bone]=v
                    p['rotations'][bone]=float(v)
                p['rotations']['arm_near_upper']=(20+4*math.sin(phase*2*math.pi))*envelope
                p['rotations']['arm_near_fore']=-15*envelope
                p['rotations']['cape_root']=16*envelope
                p['rotations']['cape_mid']=(12+3*math.sin(phase*2*math.pi-.4))*envelope
                p['rotations']['cape_tip']=(10+4*math.sin(phase*2*math.pi-.8))*envelope
            poses.append(p)
        for bone in m.B:
            vals=np.degrees(np.unwrap(np.radians([p['rotations'][bone] for p in poses])))
            for p,v in zip(poses,vals):p['rotations'][bone]=float(v)
        result[name]={'length':length,'loop':False,'times':times.tolist(),'poses':poses,
            'method_events':[{'time':1.06 if name=='attack_01' else 3.24,'method':'_event_attack_hit' if name=='attack_01' else '_event_skill_hit'}]}
    from minotaur_attack_v4 import build_attack
    from minotaur_skill_v3 import build_skill
    result['attack_01']=build_attack(m)
    result['skill_01']=build_skill(m)
    return result
