"""Author source-space native rig and five animation key sets; no asset edits."""
import math,json,shutil
from pathlib import Path
from rg_common import ROOT,read,write,sha,rgba,mask,np
from walk_reference_trajectory import target as walk_foot_target, SOLE

BONES={
 'pelvis':('',(530,701)), 'torso':('pelvis',(533,695)),
 'neck':('torso',(526,395)), 'head':('neck',(537,290)),
 'arm_near_upper':('torso',(375,555)), 'arm_near_fore':('arm_near_upper',(332,671)),
 'hand_near':('arm_near_fore',(329,835)), 'sword_socket':('hand_near',(328,867)),
 'arm_far_upper':('torso',(641,601)), 'arm_far_fore':('arm_far_upper',(680,695)),
 'hand_far':('arm_far_fore',(740,782)), 'shield_socket':('hand_far',(744,821)),
 'cape_root':('torso',(508,415)), 'cape_mid':('cape_root',(250,760)), 'cape_tip':('cape_mid',(150,1040)),
 'leg_near_thigh':('pelvis',(430,900)), 'knee_near':('leg_near_thigh',(388,1083)),
 'leg_near_shin':('knee_near',(388,1083)), 'foot_near':('leg_near_shin',(332,1331)),
 'leg_far_thigh':('pelvis',(592,910)), 'knee_far':('leg_far_thigh',(640,1083)),
 'leg_far_shin':('knee_far',(640,1083)), 'foot_far':('leg_far_shin',(658,1334))}

def main():
    for p in ['resources','scripts/build','scenes/rigs','scenes/tests','scenes/units/odyssey/roman_guard','reports/animations','reports/native_rig_v2']:(ROOT/p).mkdir(parents=True,exist_ok=True)
    for p in ['reports','work','art_source','tools','docs']:(ROOT/p/'.gdignore').write_text('')
    (ROOT/'resources/masks').mkdir(exist_ok=True)
    for side in ['front','back']:shutil.copy2(ROOT/f'work/masks/cape_{side}_region.png',ROOT/f'resources/masks/cape_{side}_region.png')
    paths={};records={};scene=['[gd_scene format=3]','[node name="Skeleton2D" type="Skeleton2D"]']
    for name,(parent,point) in BONES.items():
        path=(paths[parent]+'/' if parent else '')+name;paths[name]=path
        pp=BONES[parent][1] if parent else (0,0);local=[point[0]-pp[0],point[1]-pp[1]]
        kids=[pos for p,pos in BONES.values() if p==name and pos!=point]
        d=[kids[0][i]-point[i] for i in [0,1]] if kids else [0,25]
        length=max(8,math.hypot(*d));angle=math.atan2(d[1],d[0])
        records[name]={'parent':parent,'path':path,'pivot':list(point),'local_position':local,'length':length,'bone_angle':angle}
        scene += [f'[node name="{name}" type="Bone2D" parent="{paths[parent] if parent else "."}"]',f'position = Vector2({local[0]}, {local[1]})',f'rest = Transform2D(1, 0, 0, 1, {local[0]}, {local[1]})','auto_calculate_length_and_angle = false',f'length = {length}',f'bone_angle = {angle}']
    (ROOT/'scenes/rigs/human_medium_rig_v1.tscn').write_text('\n\n'.join(scene)+'\n',encoding='utf-8')
    bbox=rgba('work/05_complete_body_candidate_v2_rgba_clean.png').getchannel('A').getbbox()
    write('resources/human_medium_rig_v1.json',{'id':'HUMAN_MEDIUM_RIG_V1','bones':records,'origin':[530,1460],'body_height':bbox[3]-bbox[1],'near_knee_pivot':[388,1083]})
    m=read('tools/roman_guard_parts_manifest.json')
    baseline={'files':{p['file']:sha(p['file']) for p in m['parts']},'body_file':'work/05_complete_body_candidate_v2_rgba_clean.png','body_sha256':sha('work/05_complete_body_candidate_v2_rgba_clean.png'),'near_knee_mesh_sha256':sha('assets/units/odyssey/roman_guard/near_knee_skinning_v1.json')}
    baseline_path='reports/native_rig_v2/frozen_asset_baseline.json'
    if (ROOT/baseline_path).exists():
        assert read(baseline_path)==baseline,'STOP: frozen assets differ from native entry baseline'
    else:write(baseline_path,baseline)
    # Every animation explicitly keys every bone, preventing state-transition residue.
    anims={}
    def new(name,length,times,loop=False):
        a={'length':length,'loop':loop,'times':times,'poses':[]}
        for t in times:a['poses'].append({'rotations':{n:0.0 for n in BONES},'pelvis_offset':[0,0],'hip_offsets':{'near':[0,0],'far':[0,0]},'shoulder_offset':[0,0],'visual_rotation':0.0,'visual_offset':[0,0],'helmet_rotation':0.0})
        anims[name]=a;return a
    a=new('idle',1.6,[0,.4,.8,1.2,1.6],True)
    for i,p in enumerate(a['poses']):
        v=math.sin(i*math.pi/2);p['pelvis_offset']=[0,1.5*v];p['rotations'].update(torso=.12*v,head=-.08*v,shield_socket=.3*v,sword_socket=-.35*v,cape_root=.16*math.sin(i*math.pi/2-.4));p['helmet_rotation']=.08*v
    a['poses'][-1]=json.loads(json.dumps(a['poses'][0]))
    # Author matched forward root motion and planted world-space contacts.
    # 48 poses keep interpolation error below a combat display pixel.
    a=new('walk',1.0,[i/48 for i in range(49)],True);contacts=[]
    a['root_motion_source_px_per_cycle']=387 # +7.5%; cadence and contact structure unchanged.
    for i,p in enumerate(a['poses']):
        phase=i/48;bob=3.5*(1-math.cos((phase+.125)*4*math.pi));weight_shift=1.5*math.sin(phase*2*math.pi);p['pelvis_offset']=[weight_shift,bob]
        sway=math.cos(phase*2*math.pi)
        counter=1.2*sway-.2*math.sin(phase*2*math.pi)
        inertia=.3*math.sin(phase*4*math.pi-.35)
        p['rotations'].update(torso=counter,head=-.85*counter,arm_near_upper=11.8*sway,arm_near_fore=-3-3.4*sway,hand_near=-2*sway,arm_far_upper=-counter,arm_far_fore=inertia,hand_far=-inertia,cape_root=-8-3*math.sin(phase*2*math.pi-.5))
        for side,offset in [('near',0),('far',.5)]:
            u=(phase+offset)%1;support=u<.5
            swing=math.sin((u-.5)*2*math.pi) if not support else 0
            hip=BONES['leg_'+side+'_thigh'][1];knee=BONES['knee_'+side][1];ankle=BONES['foot_'+side][1]
            # Reference gait: heel contact -> flat support -> raised heel/toe-off.
            # Swing trails the lower leg before passing and forward placement.
            center=480 if side=='near' else 535
            target,pitch=walk_foot_target(u,center,ankle[1])
            v0=(knee[0]-hip[0],knee[1]-hip[1]);v1=(ankle[0]-knee[0],ankle[1]-knee[1]);l0=math.hypot(*v0);l1=math.hypot(*v1)
            rest0=math.atan2(v0[1],v0[0]);rest1=math.atan2(v1[1],v1[0])
            # Keep the approved knee deformation range; projected hip translation
            # beneath the skirt supplies the pelvis/leg depth change, without scaling.
            # Both knees flex toward the facing direction, never backwards.
            # Weight acceptance softens the planted knee; peak swing flexion
            # occurs while the lower leg is still trailing, before passing.
            if support:
                flex=4*math.sin(math.pi*min(u/.3125,1))**2
            else:
                flex=16*math.sin(math.pi*((u-.5)*2)**.65)
            bend=math.radians((3 if side=='near' else 12)+flex)
            reach2=l0*l0+l1*l1+2*l0*l1*math.cos(bend)
            hx=hip[0]+weight_shift
            hy=target[1]-math.sqrt(reach2-(target[0]-hx)**2)
            p['hip_offsets'][side]=[hx-hip[0]-weight_shift,hy-hip[1]-bob]
            h=(hx,hy)
            dx,dy=target[0]-h[0],target[1]-h[1];dist=math.hypot(dx,dy);cosk=max(-1,min(1,(dist*dist-l0*l0-l1*l1)/(2*l0*l1)))
            rest0=math.atan2(v0[1],v0[0]);rest1=math.atan2(v1[1],v1[0]);sign=1
            bend=sign*math.acos(cosk);upper=math.atan2(dy,dx)-math.atan2(l1*math.sin(bend),l0+l1*math.cos(bend))
            thigh=math.degrees(upper-rest0);shin=math.degrees(upper+bend-rest1)-thigh
            p['rotations']['leg_'+side+'_thigh']=thigh;p['rotations']['leg_'+side+'_shin']=shin;p['rotations']['foot_'+side]=pitch-thigh-shin
            contacts.append({'time':phase,'side':side,'support':support,'target_ankle':list(target),'world_foot_pitch':pitch,'sole_profile':SOLE.tolist()})
    a['poses'][-1]=json.loads(json.dumps(a['poses'][0]));a['support_intervals']={'near':[[0,.5]],'far':[[.5,1.0]]}
    write('resources/walk_contact_targets.json',contacts)
    a=new('attack_01',.8,[0,.15,.28,.36,.4,.5,.62,.8])
    for p,f,lift in zip(a['poses'],[0,-.14,.20,.80,.98,1,.48,0],[0,.8,1,1,1,1,.75,0]):
        p['rotations'].update(torso=7*f,arm_near_upper=-95*f,arm_near_fore=-14*f,hand_near=63*f,head=-4*f,arm_far_upper=-30*lift,arm_far_fore=-35*lift,hand_far=65*lift-7*f,cape_root=-8*f)
        p['pelvis_offset']=[20*f,3*f]
    for p,angle in zip(a['poses'],[0,-1,-24,-40,-40,-40,-35,0]):p['rotations']['cape_root']=angle
    a['method_events']=[{'time':.4,'node':'RigEventRelay','method':'_event_attack_hit'}]
    a=new('hit',.32,[0,.08,.16,.24,.32])
    for p,f in zip(a['poses'],[0,1,-.2,.15,0]):p['rotations'].update(torso=-3*f,head=-1*f,shield_socket=2*f)
    a=new('death',1.1,[0,.12,.25,.42,.62,.82,.98,1.1])
    # Recoil -> buckling -> folded collapse -> impact -> settled asymmetrical pose.
    stages=[
      (0,0,0,0,0,0,0,0,0,0),
      (-2,-10,7,-8,8,0,2,-2,0,0),
      (-8,-16,12,-16,20,12,8,-6,5,8),
      (-23,12,10,-28,30,28,17,-12,12,24),
      (-48,27,16,-40,42,25,19,-16,24,44),
      (-82,24,22,-48,48,8,18,-17,34,62),
      (-102,12,10,-44,44,-18,18,-15,30,68),
      (-100,14,12,-45,45,-16,18,-15,30,68)]
    for p,(roll,torso,head,arm,fore,thigh,shin,farshin,fararm,down) in zip(a['poses'],stages):
        p['visual_rotation']=roll;p['visual_offset']=[roll*.9,0]
        p['rotations'].update(torso=torso,head=head,arm_near_upper=arm,arm_near_fore=fore,hand_near=-fore*.45,arm_far_upper=fararm,arm_far_fore=-fararm*.35,shield_socket=fararm*.3,leg_near_thigh=thigh,leg_near_shin=shin,foot_near=-thigh*.35,leg_far_thigh=-thigh*.35,leg_far_shin=farshin,foot_far=8 if down else 0,cape_root=-torso*.6)
        p['pelvis_offset']=[-down*.25,down]
    for p,angle in zip(a['poses'],[0,0,-4,-8,8,20,26,25]):p['rotations']['leg_far_thigh']=angle
    for p,angle in zip(a['poses'],[0,-8,-24,-32,-35,-32,-20,-20]):p['rotations']['cape_root']=angle
    # Preserve the user-accepted death image transforms after correcting hip axes.
    for p in a['poses']:
        for side,old in [('near',(421,995)),('far',(619,1003))]:
            delta=np.array(BONES['leg_'+side+'_thigh'][1])-np.array(old)
            t=math.radians(p['rotations']['leg_'+side+'_thigh'])
            rr=np.array([[math.cos(t),-math.sin(t)],[math.sin(t),math.cos(t)]])
            p['hip_offsets'][side]=((rr-np.eye(2))@delta).tolist()
        delta=np.array(BONES['arm_near_upper'][1])-np.array([457,510])
        t=math.radians(p['rotations']['arm_near_upper'])
        rr=np.array([[math.cos(t),-math.sin(t)],[math.sin(t),math.cos(t)]])
        p['shoulder_offset']=((rr-np.eye(2))@delta).tolist()
    # Keyframe floor clearance from source alpha points; no runtime ragdoll.
    origin=np.array([530,1460])
    attach={'head':'head','helmet':'head','torso':'torso','pelvis':'pelvis','sword':'sword_socket','shield':'shield_socket','cape':'cape_root'}
    def rot(deg):
        t=math.radians(deg);return np.array([[math.cos(t),-math.sin(t)],[math.sin(t),math.cos(t)]])
    clouds=[]
    for draw in m['draw_passes']:
        name=draw['part'];alpha=np.array(rgba(next(p['file'] for p in m['parts'] if p['name']==name)))[:,:,3]
        if draw.get('clip_mask'):alpha=(alpha.astype(float)*np.array(mask(draw['clip_mask']))/255).astype(np.uint8)
        yy,xx=np.where(alpha>64);clouds.append((name,'torso' if name=='cape' and 'front' in draw.get('clip_mask','') else attach.get(name,name),np.column_stack([xx,yy])))
    for pose in a['poses'][1:]:
        transforms={}
        for name,(parent,pivot) in BONES.items():
            offset=np.array(records[name]['local_position'],float)
            if name=='pelvis':offset+=pose['pelvis_offset']
            if name in ['leg_near_thigh','leg_far_thigh']:offset+=pose['hip_offsets']['near' if 'near' in name else 'far']
            if name=='arm_near_upper':offset+=pose['shoulder_offset']
            pr,pp=transforms[parent] if parent else (np.eye(2),np.zeros(2))
            transforms[name]=(pr@rot(pose['rotations'][name]),pp+pr@offset)
        max_y=-99999
        for name,bone,points in clouds:
            rr,pp=transforms[bone];world=(points-np.array(BONES[bone][1]))@rr.T+pp-origin
            final=world@rot(pose['visual_rotation']).T
            max_y=max(max_y,float(final[:,1].max()))
        pose['visual_offset'][1]=-max_y
    write('resources/roman_guard_animations_v1.json',anims)
    # Local native skinning, using only existing approved texture pixels.
    # Shoulder armor stays on torso; boot cuff follows shin while sole follows foot.
    for name,start,end,stationary,moving in [
      ('arm_near_upper',550,610,'torso','arm_near_upper'),
      ('arm_far_upper',605,660,'torso','arm_far_upper'),
      ('foot_far',1320,1360,'leg_far_shin','foot_far')]:
        texture_part='foot_near' if name=='foot_far' else name
        texture_file=f'assets/units/odyssey/roman_guard/parts/{texture_part}.png'
        alpha=np.array(rgba(texture_file))[:,:,3]
        ys,xs=np.where(alpha>0);step=6;x0=int(xs.min()//step*step);x1=int(xs.max()//step*step+step);y0=int(ys.min()//step*step);y1=int(ys.max()//step*step+step)
        vertices=[];triangles=[];lookup={}
        for y in range(y0,y1,step):
            for x in range(x0,x1,step):
                if not alpha[y:y+step+1,x:x+step+1].any():continue
                ids=[]
                for point in [(x,y),(x+step,y),(x+step,y+step),(x,y+step)]:
                    if point not in lookup:lookup[point]=len(vertices);vertices.append(point)
                    ids.append(lookup[point])
                triangles.extend([[ids[0],ids[1],ids[2]],[ids[0],ids[2],ids[3]]])
        points=np.array(vertices)
        t=np.clip((points[:,1]-start)/(end-start),0,1);weights=t*t*(3-2*t)
        # Torso-edge pixels inside each arm extraction stay on the torso.
        if name=='arm_near_upper':
            edge=np.clip((points[:,0]-390)/55,0,1);weights*=1-edge*edge*(3-2*edge)
        if name=='arm_far_upper':
            edge=np.clip((points[:,0]-620)/33,0,1);weights*=edge*edge*(3-2*edge)
        geometry=points.copy()
        if name=='foot_far':geometry+=np.array(BONES['foot_far'][1])-np.array(BONES['foot_near'][1])
        write(f'resources/{name}_local_skinning.json',{'part':name,'texture_file':texture_file,'texture_sha256':sha(texture_file),'stationary_bone':stationary,'moving_bone':moving,'transition_source_y':[start,end],'vertices':geometry.tolist(),'uv':vertices,'triangles':triangles,'moving_weights':weights.tolist(),'stationary_weights':(1-weights).tolist(),'usage':'walk and attack shoulder joints; walk far shoe uses approved near-shoe pixels for matching forward-facing view; original draws for other poses'})
    print('Prepared 23 generic bones and exactly five animation key sets')

if __name__=='__main__':main()
