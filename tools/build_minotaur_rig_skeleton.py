"""Large biped structural rig only; formal assembly waits for part approval."""
from pathlib import Path
import json,math
ROOT=Path(__file__).resolve().parents[1]
SPEC=[('pelvis','',[474,716]),('torso','pelvis',[474,640]),('neck','torso',[549,369]),('head','neck',[566,321]),('shoulder_near','torso',[328,413]),('arm_near_upper','torso',[298,529]),('arm_near_fore','arm_near_upper',[250,666]),('hand_near','arm_near_fore',[275,832]),('axe_support_socket','hand_near',[279,887]),('shoulder_far','torso',[624,500]),('arm_far_upper','torso',[621,590]),('arm_far_fore','arm_far_upper',[674,765]),('hand_far','arm_far_fore',[778,850]),('axe_socket','hand_far',[821,862]),('cape_root','torso',[321,358]),('cape_mid','cape_root',[218,734]),('cape_tip','cape_mid',[111,1102]),('leg_near_thigh','pelvis',[367,963]),('knee_near','leg_near_thigh',[375,1085]),('leg_near_shin','knee_near',[375,1085]),('foot_near','leg_near_shin',[296,1360]),('leg_far_thigh','pelvis',[566,967]),('knee_far','leg_far_thigh',[618,1103]),('leg_far_shin','knee_far',[618,1103]),('foot_far','leg_far_shin',[614,1365])]
# Hip centers lie under the skirt, above the first visible thigh pixels.
# A mask edge at y963 is not an anatomical hip pivot.
ANATOMICAL_HIPS={'leg_near_thigh':[367,870],'leg_far_thigh':[566,875]}
SPEC=[(name,parent,ANATOMICAL_HIPS.get(name,pivot)) for name,parent,pivot in SPEC]

def main():
 bones={};text=['[gd_scene format=3]','[node name="Skeleton2D" type="Skeleton2D"]']
 for name,parent,pivot in SPEC:
  prev=bones[parent]['pivot'] if parent else [0,0];local=[pivot[i]-prev[i] for i in range(2)];path=(bones[parent]['path']+'/' if parent else '')+name
  children=[v for n,p,v in SPEC if p==name and v!=pivot];delta=[children[0][i]-pivot[i] for i in range(2)] if children else [0,30];length=max(8,math.hypot(*delta));angle=math.atan2(delta[1],delta[0]);bones[name]={'parent':parent,'pivot':pivot,'local_position':local,'path':path,'length':length,'bone_angle':angle}
  text += [f'[node name="{name}" type="Bone2D" parent="{bones[parent]["path"] if parent else "."}"]',f'position = Vector2({local[0]}, {local[1]})',f'rest = Transform2D(1, 0, 0, 1, {local[0]}, {local[1]})','auto_calculate_length_and_angle = false',f'length = {length}',f'bone_angle = {angle}']
 out=ROOT/'scenes/rigs/biped_large_rig_v1.tscn';out.parent.mkdir(parents=True,exist_ok=True);out.write_text('\n\n'.join(text)+'\n',encoding='utf-8')
 data={'id':'BIPED_LARGE_RIG_V1','unit_id':'OD_UNIT_04_MINOTAUR_BREAKER','status':'STRUCTURAL_CANDIDATE','origin':[486,1485],'canvas':[1024,1536],'body_height':1435,'display_heights':[360,288],'bones':bones,'axe_grips':{'primary_source':[821,862],'support_source':[803,1012]},'note':'Source-measured large proportions. Not copied/scaled from human medium skeleton. Knee art can remain with shin until motion proves separate plate necessary.'};(ROOT/'resources/minotaur_breaker_rig_v1.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8');print('Large native bones:',len(bones))
if __name__=='__main__':main()
