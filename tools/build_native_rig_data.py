"""Author source-space native rig and five animation key sets; no asset edits."""
import math,json,shutil
from pathlib import Path
from rg_common import ROOT,read,write,sha,rgba,mask,np

BONES={
 'pelvis':('',(530,701)), 'torso':('pelvis',(533,695)),
 'neck':('torso',(526,395)), 'head':('neck',(537,290)),
 'arm_near_upper':('torso',(457,510)), 'arm_near_fore':('arm_near_upper',(332,671)),
 'hand_near':('arm_near_fore',(329,835)), 'sword_socket':('hand_near',(328,867)),
 'arm_far_upper':('torso',(641,601)), 'arm_far_fore':('arm_far_upper',(680,695)),
 'hand_far':('arm_far_fore',(740,782)), 'shield_socket':('hand_far',(744,821)),
 'cape_root':('torso',(508,415)), 'cape_mid':('cape_root',(250,760)), 'cape_tip':('cape_mid',(150,1040)),
 'leg_near_thigh':('pelvis',(421,995)), 'knee_near':('leg_near_thigh',(388,1083)),
 'leg_near_shin':('knee_near',(388,1083)), 'foot_near':('leg_near_shin',(332,1331)),
 'leg_far_thigh':('pelvis',(619,1003)), 'knee_far':('leg_far_thigh',(640,1083)),
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
    write('reports/native_rig_v2/frozen_asset_baseline.json',{'files':{p['file']:sha(p['file']) for p in m['parts']},'body_file':'work/05_complete_body_candidate_v2_rgba_clean.png','body_sha256':sha('work/05_complete_body_candidate_v2_rgba_clean.png'),'near_knee_mesh_sha256':sha('assets/units/odyssey/roman_guard/near_knee_skinning_v1.json')})
    # Every animation explicitly keys every bone, preventing state-transition residue.
    anims={}
    def new(name,length,times,loop=False):
        a={'length':length,'loop':loop,'times':times,'poses':[]}
        for t in times:a['poses'].append({'rotations':{n:0.0 for n in BONES},'pelvis_offset':[0,0],'hip_offsets':{'near':[0,0],'far':[0,0]},'visual_rotation':0.0,'visual_offset':[0,0],'helmet_rotation':0.0})
        anims[name]=a;return a
    a=new('idle',1.6,[0,.4,.8,1.2,1.6],True)
    for i,p in enumerate(a['poses']):
        v=math.sin(i*math.pi/2);p['pelvis_offset']=[0,1.5*v];p['rotations'].update(torso=.12*v,head=-.08*v,shield_socket=.3*v,sword_socket=-.35*v,cape_root=.16*math.sin(i*math.pi/2-.4));p['helmet_rotation']=.08*v
    a['poses'][-1]=json.loads(json.dumps(a['poses'][0]))
    # Offline two-link construction of key poses. No runtime IK and no root translation.
    a=new('walk',1.0,[i/12 for i in range(13)],True);contacts=[]
    for i,p in enumerate(a['poses']):
        phase=i/12;bob=2*(1-math.cos(phase*4*math.pi));p['pelvis_offset']=[0,bob]
        p['rotations'].update(torso=.45*math.sin(phase*2*math.pi),arm_near_upper=-1.5*math.sin(phase*2*math.pi),arm_far_upper=1.0*math.sin(phase*2*math.pi),cape_root=.45*math.sin(phase*2*math.pi-.5))
        for side,offset in [('near',0),('far',.5)]:
            u=(phase+offset)%1;support=u<.5
            swing=math.sin((u-.5)*2*math.pi) if not support else 0
            hip=BONES['leg_'+side+'_thigh'][1];knee=BONES['knee_'+side][1];ankle=BONES['foot_'+side][1]
            target=(ankle[0]+36*swing,ankle[1]-22*swing)
            # Projected hip lift is hidden under the skirt; keyframed, not runtime IK.
            p['hip_offsets'][side]=[30*swing,-24*swing]
            h=(hip[0]+30*swing,hip[1]+bob-24*swing);v0=(knee[0]-hip[0],knee[1]-hip[1]);v1=(ankle[0]-knee[0],ankle[1]-knee[1]);l0=math.hypot(*v0);l1=math.hypot(*v1)
            dx,dy=target[0]-h[0],target[1]-h[1];dist=math.hypot(dx,dy);cosk=max(-1,min(1,(dist*dist-l0*l0-l1*l1)/(2*l0*l1)))
            rest0=math.atan2(v0[1],v0[0]);rest1=math.atan2(v1[1],v1[0]);sign=-1 if rest1<rest0 else 1
            bend=sign*math.acos(cosk);upper=math.atan2(dy,dx)-math.atan2(l1*math.sin(bend),l0+l1*math.cos(bend))
            thigh=math.degrees(upper-rest0);shin=math.degrees(upper+bend-rest1)-thigh
            p['rotations']['leg_'+side+'_thigh']=thigh;p['rotations']['leg_'+side+'_shin']=shin;p['rotations']['foot_'+side]=-thigh-shin
            contacts.append({'time':phase,'side':side,'support':support,'target_ankle':list(target)})
    a['poses'][-1]=json.loads(json.dumps(a['poses'][0]));a['support_intervals']={'near':[[0,.5]],'far':[[.5,1.0]]}
    write('resources/walk_contact_targets.json',contacts)
    a=new('attack_01',.8,[0,.15,.28,.36,.4,.5,.62,.8])
    for p,f in zip(a['poses'],[0,-.08,.32,.8,.95,1,.48,0]):
        p['rotations'].update(torso=3*f,arm_near_upper=-30*f,arm_near_fore=-12*f,hand_near=1*f,head=-1*f,arm_far_upper=-1.5*f,cape_root=-8*f)
        p['pelvis_offset']=[3*f,0]
    for p,angle in zip(a['poses'],[0,-1,-14,-24,-24,-24,-20,0]):p['rotations']['cape_root']=angle
    a['method_events']=[{'time':.4,'node':'RigEventRelay','method':'_event_attack_hit'}]
    a=new('hit',.32,[0,.08,.16,.24,.32])
    for p,f in zip(a['poses'],[0,1,-.2,.15,0]):p['rotations'].update(torso=-3*f,head=-1*f,shield_socket=2*f)
    a=new('death',1.1,[0,.22,.44,.66,.88,1.1])
    for p,f in zip(a['poses'],[0,.08,.23,.55,.9,1]):
        p['visual_rotation']=-83*f;p['visual_offset']=[-16*f,-20*f]
        p['rotations'].update(torso=-5*math.sin(f*math.pi),arm_far_upper=8*f,arm_near_upper=-6*f,leg_near_shin=8*f,leg_far_shin=-6*f)
        p['pelvis_offset']=[0,35*f]
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
            pr,pp=transforms[parent] if parent else (np.eye(2),np.zeros(2))
            transforms[name]=(pr@rot(pose['rotations'][name]),pp+pr@offset)
        max_y=-99999
        for name,bone,points in clouds:
            rr,pp=transforms[bone];world=(points-np.array(BONES[bone][1]))@rr.T+pp-origin
            final=world@rot(pose['visual_rotation']).T
            max_y=max(max_y,float(final[:,1].max()))
        pose['visual_offset'][1]=-max_y
    write('resources/roman_guard_animations_v1.json',anims)
    print('Prepared 23 generic bones and exactly five animation key sets')

if __name__=='__main__':main()
