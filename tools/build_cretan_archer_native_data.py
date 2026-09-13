"""Archer-only retargeting and offline keyframe authoring for the shared rig family.

No Roman files or approved art are edited. Contact targets are authored in source
space; Godot plays the baked keys, with no runtime IK or third-party nodes.
"""
import math, json
import numpy as np
from PIL import Image
import cretan_archer_pipeline as p
import build_cretan_archer_parts as parts
from review_cretan_archer_repaired_parts import ORDER

DATA='resources/cretan_archer_rig_v1.json'
ANIMS='resources/cretan_archer_animations_v1.json'
GROUND=1460.0
STRIDE=420.0
SUPPORT=.55

def rotation(deg):
    a=math.radians(deg);return np.array([[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]])
def smooth(t):
    t=max(0.,min(1.,t));return t*t*(3-2*t)
def vec(x):return np.array(x,float)
def solve_arm(shoulder,target,l0,l1,rest0,rest1,sign):
    d=target-shoulder;dist=np.linalg.norm(d)
    co=np.clip((dist*dist-l0*l0-l1*l1)/(2*l0*l1),-1,1)
    bend=sign*math.acos(co)
    a=math.atan2(d[1],d[0])-math.atan2(l1*math.sin(bend),l0+l1*math.cos(bend))
    return math.degrees(a-rest0),math.degrees(a+bend-rest1)-math.degrees(a-rest0)

def main():
    p.verify_frozen();assert p.valid_external_body()
    shared=p.load('resources/human_medium_rig_v1.json')
    pivots={n:vec(v['pivot']) for n,v in shared['bones'].items()}
    pivots.update({n:vec(xy) for n,xy in parts.PIVOTS.items() if n in pivots and xy})
    # Archer-only deformation controls; rest textures keep their exact source positions.
    pivots.update(arm_near_upper=vec([440,448]),arm_near_fore=vec([382,600]))
    pivots.update(neck=vec([532,360]),knee_near=vec(parts.PIVOTS['leg_near_shin']),knee_far=vec(parts.PIVOTS['leg_far_shin']),
                  cape_root=vec(parts.PIVOTS['cloak']),cape_mid=vec([405,403]),cape_tip=vec([334,523]),
                  sword_socket=vec([407,859]),shield_socket=vec([844,725]),
                  bow_socket=vec([844,725]),arrow_socket=vec([752.55,725]),quiver_socket=vec([325,337]))
    parents={n:v['parent'] for n,v in shared['bones'].items()}
    parents.update(bow_socket='hand_far',arrow_socket='bow_socket',quiver_socket='torso')
    bones={}
    for n,parent in parents.items():
        point=pivots[n];pp=pivots[parent] if parent else vec([0,0]);local=point-pp
        children=[pivots[k] for k,par in parents.items() if par==n and np.linalg.norm(pivots[k]-point)>0]
        d=children[0]-point if children else vec([0,25])
        bones[n]={'parent':parent,'path':(bones[parent]['path']+'/' if parent else '')+n,'pivot':point.tolist(),
                  'local_position':local.tolist(),'length':max(8.,float(np.linalg.norm(d))),'bone_angle':math.atan2(d[1],d[0])}
    attachments={n:n for n in parts.POLYGONS};attachments.update(bow='bow_socket',bow_string='bow_socket',arrow_single='arrow_socket',quiver='quiver_socket',cloak='cape_root')
    data={'id':'HUMAN_MEDIUM_RIG_V1','unit_id':'OD_UNIT_02_CRETAN_ARCHER','shared_skeleton_source':'scenes/rigs/human_medium_rig_v1.tscn',
          'shared_skeleton_sha256':p.sha('scenes/rigs/human_medium_rig_v1.tscn'),'bones':bones,'origin':[524,GROUND],'body_height':1340,
          'attachments':attachments,'draw_order':ORDER,'source_canvas':[1024,1536],
          'arrow_nock_source':[282,725],'bow_string_local_anchors':[[-54,-575],[-125,515]],'new_bones':['bow_socket','arrow_socket','quiver_socket']}
    p.save(DATA,data)
    anims={}
    def new(name,length,times,loop=False):
        a={'length':length,'loop':loop,'times':times,'poses':[]};anims[name]=a
        for t in times:a['poses'].append({'rotations':{n:0. for n in bones},'pelvis_offset':[0,0],'hip_offsets':{'near':[0,0],'far':[0,0]},
            'shoulder_offsets':{'near':[0,0],'far':[0,0]},'visual_rotation':0.,'visual_offset':[0,0],
            'bow_draw_point':[-91.45,0],'arrow_visible':False,'arrow_rotation':0.})
        return a
    def fk(pose):
        transforms={}
        for n,rec in bones.items():
            off=vec(rec['local_position'])
            if n=='pelvis':off+=pose['pelvis_offset']
            for side in ['near','far']:
                if n=='leg_'+side+'_thigh':off+=pose['hip_offsets'][side]
                if n=='arm_'+side+'_upper':off+=pose['shoulder_offsets'][side]
            pr,pp=transforms[rec['parent']] if rec['parent'] else (np.eye(2),vec([0,0]))
            transforms[n]=(pr@rotation(pose['rotations'][n]),pp+pr@off)
        return transforms
    a=new('idle',1.6,[i*.2 for i in range(9)],True)
    for i,pose in enumerate(a['poses']):
        phase=i/8*2*math.pi;v=math.sin(phase)
        pose['pelvis_offset']=[.6*v,2*v]
        pose['rotations'].update(torso=.25*v,head=-.22*v,arm_near_upper=.5*v,hand_near=.2*v,arm_far_upper=-.22*v,cape_root=.3*math.sin(phase-.4),quiver_socket=.15*math.sin(phase-.25))
    a['poses'][-1]=json.loads(json.dumps(a['poses'][0]))
    # Regenerate native weights from this retargeted unit before material-floor
    # evaluation. The source textures and shared skeleton are never rewritten.
    from build_cretan_archer_local_skinning import main as build_skinning
    build_skinning()
    from cretan_archer_walk_v2 import author_walk
    from cretan_archer_attack_v2 import author_attack
    from cretan_archer_death_v2 import author_death
    anims['walk'], contacts = author_walk(data)
    p.save('resources/cretan_archer_walk_contacts.json', contacts)
    anims['attack_01'] = author_attack(data)
    a=new('hit',.3,[0,.075,.15,.225,.3])
    for pose,f in zip(a['poses'],[0,1,-.25,.1,0]):
        pose['rotations'].update(torso=-4*f,head=1*f,arm_far_upper=2*f,cape_root=2*f)
    anims['death'] = author_death(data)
    p.save(ANIMS,anims)
    p.verify_frozen()
    print(json.dumps({'bones':len(bones),'animations':list(anims),'walk_stride':STRIDE,
                      'parts_or_shared_rig_modified':False}))

if __name__=='__main__':main()
