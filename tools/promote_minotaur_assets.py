"""Fail-closed promotion: explicit art review plus current native evidence required."""
from pathlib import Path
import hashlib,json,shutil
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'reports/minotaur_breaker';W=ROOT/'work/minotaur_breaker'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 review=read(R/'production_art_review.json')
 assert review['status']=='PASS', 'Explicit visual art review required'
 assert set(review['animations'])=={'idle','walk','attack_01','skill_01','hit','death'}
 assert all(v=='PASS' for v in review['animations'].values()), 'Animation visual failures remain'
 capture=read(R/'capture_manifest.json')
 assert capture['inputs_unchanged_during_capture']
 assert len(capture['frames'])==192 and len({(f['animation'],f['height'],f['frame']) for f in capture['frames']})==192
 for file,digest in capture['artifact_inputs'].items():assert sha(ROOT/file.removeprefix('res://'))==digest, 'Stale capture input '+file
 for frame in capture['frames']:assert sha(ROOT/frame['path'].removeprefix('res://'))==frame['sha256'], 'Stale captured frame'
 assert review['artifact_inputs']==capture['artifact_inputs'], 'Art review belongs to another build'
 for name in ['candidate_format_validation','motion_contract_test','lab_smoke','structure_test']:
  assert read(R/(name+'.json'))['status']=='PASS', name+' has not passed'
 assert read(R/'candidate_ik_reach.json')['status']=='PASS', 'Unreachable poses remain'
 source=read(ROOT/'art_source/odyssey/minotaur_breaker/source_manifest.json')
 for item in source['files']:assert sha(ROOT/item['file'])==item['sha256']
 parts=read(W/'candidates/manifest.json')['parts'];assert len(parts)==21
 rig=read(ROOT/'resources/minotaur_breaker_rig_v1.json')
 formal=ROOT/'assets/units/odyssey/minotaur_breaker/parts';formal.mkdir(parents=True,exist_ok=True)
 compiled=ROOT/'resources/minotaur_breaker_textures';compiled.mkdir(exist_ok=True)
 output=[]
 completed=np.any(np.array(Image.open(W/'01_complete_body_rgba_v2.png'))!=np.array(Image.open(W/'00_rig_master_rgba.png')),axis=2)
 for part in parts:
  name=part['name'];origin=ROOT/part['file'];assert sha(origin)==part['sha256']
  target=formal/(name+'.png');shutil.copy2(origin,target)
  binary=W/'candidates/native_parts'/(name+'.res');shutil.copy2(binary,compiled/binary.name)
  bone=rig['attachments'].get(name,name)
  sources={'arm_far_upper':['work/minotaur_breaker/raw/003_far_upper_arm.png'],'axe':['work/minotaur_breaker/00_rig_master_rgba.png','work/minotaur_breaker/raw/002_axe_grip.png'],'cape':['work/minotaur_breaker/00_rig_master_rgba.png','work/minotaur_breaker/raw/004_cape.png']}.get(name,['work/minotaur_breaker/raw/005_knee_support.png'] if name.endswith('_support') else ['work/minotaur_breaker/01_complete_body_rgba_v2.png'])
  ai_completed=name in ['arm_far_upper','axe','cape'] or name.endswith('_support') or bool(np.any(completed&(np.array(Image.open(origin))[:,:,3]>0)))
  output.append({'name':name,'file':target.relative_to(ROOT).as_posix(),'sha256':sha(target),'status':'PASS','source':sources,'ai_completed':ai_completed,'review_required':False,'pivot_hint':rig['bones'][bone]['pivot'],'compiled_texture':(compiled/binary.name).relative_to(ROOT).as_posix(),'compiled_sha256':sha(compiled/binary.name)})
 scene=W/'candidates/minotaur_breaker_candidate.tscn';text=scene.read_text(encoding='utf-8')
 assert text.count('res://work/minotaur_breaker/candidates/native_parts/')==21
 text=text.replace('res://work/minotaur_breaker/candidates/native_parts/','res://resources/minotaur_breaker_textures/')
 text=text.replace('name="MinotaurBreakerCandidate"','name="MinotaurBreaker"').replace('autoplay = false','autoplay = true')
 target=ROOT/'scenes/units/odyssey/minotaur_breaker/minotaur_breaker_rig.tscn';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text,encoding='utf-8')
 write(ROOT/'tools/minotaur_breaker_parts_manifest.json',{'unit_id':source['unit_id'],'version':'RIG_ASSET_V1','status':'PASS','core_parts':19,'hidden_joint_supports':2,'canvas_width':1024,'canvas_height':1536,'alpha_required':True,'parts':output,'draw_order':rig['draw_order'],'review':'reports/minotaur_breaker/production_art_review.json'})
 write(formal.parent/'minotaur_breaker_pivots.json',{'unit_id':source['unit_id'],'origin':rig['origin'],'bones':rig['bones'],'grips':rig['axe_grips']})
 approved=dict(rig);approved['status']='PASS';approved['approved_candidate_sha256']=sha(ROOT/'resources/minotaur_breaker_rig_v1.json');write(ROOT/'resources/minotaur_breaker_rig_approved_v1.json',approved)
 shutil.copy2(ROOT/'resources/minotaur_breaker_animation_candidates.json',ROOT/'resources/minotaur_breaker_animations_v1.json')
 shutil.copy2(ROOT/'resources/minotaur_breaker_skinning_candidates.json',ROOT/'resources/minotaur_breaker_skinning_v1.json')
 write(R/'approved_candidate_capture.json',capture)
 write(R/'promotion_record.json',{'status':'PROMOTED_AWAITING_FORMAL_RUNTIME_REGRESSION','candidate_scene_sha256':sha(scene),'formal_scene_sha256':sha(target),'candidate_capture':'approved_candidate_capture.json','changed_semantics':['root display name','autoplay enabled by default','compiled textures relocated without byte changes'],'damage_constants_added':False})
 print('Promoted 19 core PNGs + 2 knee support PNGs and native scene; final runtime regression still required.')
if __name__=='__main__':main()
