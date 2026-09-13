"""Reference-led Archer attack keys. Pure authoring: no art or scene writes.

Requires the Archer-specific 440,448 / 382,600 / 388,789 near-arm controls.
The inherited skeleton topology is unchanged. Godot plays baked tracks; all IK
and contact checks here are offline authoring, not runtime animation substitutes.
"""
import math
import numpy as np


def _v(value): return np.asarray(value,dtype=float)
def _r(deg):
    angle=math.radians(deg)
    return np.array([[math.cos(angle),-math.sin(angle)],[math.sin(angle),math.cos(angle)]])
def _smooth(x):
    x=max(0.,min(1.,x));return x*x*(3.-2.*x)
def _curve(keys,t):
    if t<=keys[0][0]:return _v(keys[0][1])
    for (ta,a),(tb,b) in zip(keys,keys[1:]):
        if t<=tb:
            u=_smooth((t-ta)/(tb-ta));return _v(a)*(1-u)+_v(b)*u
    return _v(keys[-1][1])


def author_attack(data):
    bones=data['bones'];pivots={name:_v(rec['pivot']) for name,rec in bones.items()}
    expected={'arm_near_upper':[440,448],'arm_near_fore':[382,600],'hand_near':[388,789]}
    for name,point in expected.items():
        if not np.allclose(pivots[name],point):
            raise ValueError(f'Attack V2 requires Archer deformation pivot {name}={point}; no shared-rig or art mutation is performed here')
    length=1.20;nock_time=.44;release_time=.82
    anchors=[0,.05,.12,.20,.23,.29,.34,.44,.53,.66,.70,.78,.81999,.82,.85,.88,.96,1.06,1.14,1.18,1.20]
    times=sorted(set(round(float(t),5) for t in list(np.linspace(0,length,121))+anchors))
    entry={'length':length,'loop':False,'times':times,'poses':[],
        'nock_time':nock_time,'release_time':release_time,
        'key_phases':[
            {'name':'ready','time':0}, {'name':'retrieve_from_quiver','time':.20},
            {'name':'bring_arrow_forward','time':.34}, {'name':'nock_arrow','time':.44},
            {'name':'raise_and_draw','time':.53}, {'name':'face_anchor_aim','time':.70},
            {'name':'release_and_follow_through','time':.82}, {'name':'recover','time':1.06}],
        'method_events':[{'time':release_time,'node':'RigEventRelay','method':'_event_attack_release'}]}
    finger_offset=_v([19,70]);rest_grip=pivots['bow_socket'];rest_hand=pivots['hand_near']+finger_offset
    a=pivots['arm_near_fore']-pivots['arm_near_upper'];bb=pivots['hand_near']-pivots['arm_near_fore']
    reach=float(np.linalg.norm(a)+np.linalg.norm(bb))
    direction=pivots['hand_near']-pivots['arm_near_upper'];direction/=np.linalg.norm(direction)
    # A 7-source-pixel extension naturally joins the two projected elbow
    # branches. No interpolation is allowed to introduce a 360-degree spin.
    straight_hand=pivots['arm_near_upper']+direction*(reach-.001)+finger_offset
    near_targets=[(0,rest_hand),(.05,straight_hand),(.12,[298,610]),(.20,[320,238]),(.23,[320,238]),
                  (.29,[270,510]),(.34,[480,675]),(.44,[771.55,600]),(.82,[550,310]),(.88,[526,303]),
                  (.96,[735,360]),(1.06,[680,600]),(1.14,[425,835]),(1.18,straight_hand),(1.20,rest_hand)]
    near_angles=[(0,0),(.05,0),(.12,-45),(.20,-130),(.23,-135),(.29,-100),(.34,-90),(.44,-90),(.82,-90),
                 (.88,-98),(.96,-90),(1.06,-65),(1.14,-25),(1.18,0),(1.20,0)]
    bow_targets=[(0,rest_grip),(.26,rest_grip),(.34,[852,685]),(.44,[863,600]),(.53,[940,323]),
                 (.82,[940,323]),(.88,[937,328]),(.96,[912,440]),(1.06,[867,635]),(1.18,rest_grip),(1.20,rest_grip)]
    errors=[];previous=None

    def empty_pose():
        return {'rotations':{name:0. for name in bones},'pelvis_offset':[0.,0.],
            'hip_offsets':{'near':[0.,0.],'far':[0.,0.]},'shoulder_offsets':{'near':[0.,0.],'far':[0.,0.]},
            'visual_rotation':0.,'visual_offset':[0.,0.],'bow_offset':[0.,0.],
            'bow_draw_point':[-91.45,0.],'arrow_visible':False,'arrow_rotation':0.}

    def fk(pose):
        tr={}
        for name,rec in bones.items():
            offset=_v(rec['local_position']).copy()
            if name=='pelvis':offset+=pose['pelvis_offset']
            for side in ['near','far']:
                if name=='arm_'+side+'_upper':offset+=pose['shoulder_offsets'][side]
                if name=='leg_'+side+'_thigh':offset+=pose['hip_offsets'][side]
            if name=='bow_socket':offset+=pose['bow_offset']
            rr,pp=tr[rec['parent']] if rec['parent'] else (np.eye(2),_v([0,0]))
            tr[name]=(rr@_r(pose['rotations'][name]),pp+rr@offset)
        return tr

    def aim_arm(pose,side,material_target,hand_angle,branch):
        upper='arm_'+side+'_upper';fore='arm_'+side+'_fore';hand='hand_'+side
        current=fk(pose);shoulder=current[upper][1]
        hand_point=finger_offset if side=='near' else pivots['bow_socket']-pivots[hand]
        wrist=material_target-_r(hand_angle)@hand_point
        v0=pivots[fore]-pivots[upper];v1=pivots[hand]-pivots[fore]
        l0=float(np.linalg.norm(v0));l1=float(np.linalg.norm(v1));delta=wrist-shoulder;dist=float(np.linalg.norm(delta))
        if dist>l0+l1+1.e-6 or dist<abs(l0-l1)-1.e-6:
            raise ValueError(f'Unreachable {side} wrist at t={t}: {dist:.3f} vs [{abs(l0-l1):.3f},{l0+l1:.3f}]')
        bend=branch*math.acos(float(np.clip((dist*dist-l0*l0-l1*l1)/(2*l0*l1),-1,1)))
        angle=math.atan2(delta[1],delta[0])-math.atan2(l1*math.sin(bend),l0+l1*math.cos(bend))
        r0=math.atan2(v0[1],v0[0]);r1=math.atan2(v1[1],v1[0])
        world_upper=math.degrees(angle-r0);world_fore=math.degrees(angle+bend-r1)
        parent_r=current[bones[upper]['parent']][0];parent_angle=math.degrees(math.atan2(parent_r[1,0],parent_r[0,0]))
        pose['rotations'][upper]=world_upper-parent_angle
        pose['rotations'][fore]=world_fore-world_upper
        pose['rotations'][hand]=hand_angle-world_fore

    for t in times:
        pose=empty_pose()
        activity=float(_curve([(0,0),(.26,0),(.53,1),(.88,1),(1.15,0),(1.20,0)],t))
        pose['pelvis_offset']=[5*activity,0.]
        pose['rotations'].update(torso=1.2*activity,head=-1.15*activity,cape_root=-.65*activity,quiver_socket=.3*activity)
        pose['shoulder_offsets']['far']=[6*activity,-3*activity]
        grip=_curve(bow_targets,t)
        # The original far elbow has a negative bend; stay on that branch.
        aim_arm(pose,'far',grip,0.,-1)
        trans=fk(pose);bow_r,bow_p=trans['bow_socket']
        undrawn=bow_p+bow_r@_v([-91.45,0.])
        if t<.53:nock=undrawn
        elif t<.66:nock=undrawn*(1-_smooth((t-.53)/.13))+_v([550,310])*_smooth((t-.53)/.13)
        elif t<release_time:nock=_v([550,310])
        elif t<.85:nock=_v([550,310])*(1-_smooth((t-release_time)/.03))+undrawn*_smooth((t-release_time)/.03)
        else:nock=undrawn
        pose['bow_draw_point']=(bow_r.T@(nock-bow_p)).tolist()
        hand_target=nock if nock_time<=t<release_time else _curve(near_targets,t)
        hand_angle=float(_curve(near_angles,t))
        # The near arm uses a rear-facing projected draw branch. Branch changes
        # occur only at the explicitly almost-straight ready/recovery control.
        branch=-1 if t<=.05 or t>=1.18 else 1
        aim_arm(pose,'near',hand_target,hand_angle,branch)
        pose['arrow_visible']=nock_time<=t<release_time
        pose['arrow_rotation']=-math.degrees(math.atan2(bow_r[1,0],bow_r[0,0]))
        if t==0 or t==length:pose=empty_pose()
        if previous is not None and t!=length:
            for name,value in pose['rotations'].items():
                pose['rotations'][name]=value+360*round((previous['rotations'][name]-value)/360)
        now=fk(pose)
        if nock_time<=t<release_time:
            hand_world=now['hand_near'][1]+now['hand_near'][0]@finger_offset
            bow_world=now['bow_socket'][1]+now['bow_socket'][0]@_v(pose['bow_draw_point'])
            errors.append(float(np.linalg.norm(hand_world-bow_world)))
        entry['poses'].append(pose);previous=pose
    jumps={name:max(abs(entry['poses'][i+1]['rotations'][name]-entry['poses'][i]['rotations'][name]) for i in range(len(times)-1)) for name in bones}
    if max(jumps.values())>180:raise ValueError(f'Wrapped angle/spin detected: {jumps}')
    if max(errors,default=0)>1.e-5:raise ValueError('Nock/material FK contact mismatch')
    assert all(value==0 for value in entry['poses'][0]['rotations'].values())
    assert all(value==0 for value in entry['poses'][-1]['rotations'].values())
    entry['offline_contact_validation']={'scope':'FK authoring only; actual GPU visual gate still required',
        'visible_nock_material_max_error_source_px':max(errors,default=0),
        'max_neighbor_rotation_change_degrees':max(jumps.values()),'method_event_count':1,
        'near_face_nock_target':[550,310],'bow_aim_grip_target':[940,323],
        'near_draw_branch':'positive after near-straight retrieval transition; elbow back/outward',
        'far_arm_branch':'negative throughout','ready_and_recovery_all_rotations_zero':True}
    return entry
