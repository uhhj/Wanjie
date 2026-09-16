"""Promote hash-bound, visually reviewed Centurion candidates only."""
import shutil
from datetime import datetime,timezone
import numpy as np
from PIL import Image
import build_centurion_parts as b
p=b.p
def main():
 p.verify();assert p.read(p.R+'complete_body_gate_v2.json')['input_sha256']==p.sha(b.B)
 m=p.read('tools/roman_centurion_parts_manifest.json');assert len(m['parts'])==21
 review=p.read(p.R+'parts_visual_review_v1.json')
 assert review['status']=='PASS' and review['body_sha256']==p.sha(b.B)
 assert review['candidate_hashes']=={e['name']:e['candidate_sha256'] for e in m['parts']},'Changed candidates require a fresh visual review'
 rows=[]
 for e in m['parts']:
  assert p.sha(e['candidate_file'])==e['candidate_sha256']
  im=Image.open(p.ROOT/e['candidate_file']);a=np.array(im)
  assert im.format=='PNG' and im.mode=='RGBA' and im.size==(1024,1536)
  assert a[:,:,3].min()==0 and a[:,:,3].max()>240 and im.getchannel('A').getbbox()
  dst=p.ROOT/e['file'];dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p.ROOT/e['candidate_file'],dst)
  e.update(status='PASS',review_required=False,sha256=p.sha(e['file']))
  rows.append({'name':e['name'],'sha256':e['sha256'],'bbox':im.getchannel('A').getbbox()})
 m['status']='PASS';p.save('tools/roman_centurion_parts_manifest.json',m)
 p.save('assets/units/odyssey/roman_centurion/roman_centurion_pivots.json',{'unit_id':m['unit_id'],'canvas':[1024,1536],'pivots':b.PIVOTS,'independent_knee_plates':True,'draw_order':b.ORDER})
 reports=['completed_recomposition_256.png','completed_recomposition_192.png','completed_joint_256.png','completed_joint_192.png','equipment_motion_256.png','sword_close_review.png','shoulder_motion_256.png','hip_motion_256.png']
 p.save(p.R+'parts_gate_v1.json',{'status':'PASS','part_count':21,'parts':rows,'body_sha256':p.sha(b.B),'review_method':'Agent visual review at 256/192 px plus format/provenance checks; not user approval','reports':{b.R+f:p.sha(b.R+f) for f in reports},'recomposition':'PASS_COMBAT_SCALE','elbows_knees':'PASS_PLUS_MINUS_20','equipment':'PASS','scope':'Rest and bounded articulation. Six full native animations require separate validation.','non_blocking':['Independent cape_front layer makes 21 parts rather than initial 20 estimate','Original high-resolution edge artifacts remain non-blocking'],'timestamp':datetime.now(timezone.utc).isoformat()})
 for number,name,input_name in [('005','sword_grip','sword_grip'),('006','hidden_legs','leg_hidden'),('007','hidden_cape','cape_hidden'),('008','hidden_torso_cape','torso_hidden')]:
  raw=p.W+'raw/'+number+'_'+name+'.png';prompt=p.W+'prompts/'+number+'_'+name+'.txt';inp=p.W+input_name+'_edit_input.png'
  p.save(p.R+'ai_jobs/'+number+'_'+name+'.json',{'tool':'built-in image_gen','input_file':inp,'input_sha256':p.sha(inp),'prompt_file':prompt,'prompt':(p.ROOT/prompt).read_text(encoding='utf-8'),'output_file':raw,'output_sha256':p.sha(raw),'status':'REJECTED_AS_FULL_ASSET' if number=='007' else 'LOCAL_PIXELS_USED_ONLY','recipe':b.R+'hidden_completion_recipes.json','notes':'Raw generator outputs are not formal parts. Deterministic masks preserve visible source pixels. Job 007 retained a gold pommel and was superseded by job 008.','timestamp':datetime.now(timezone.utc).isoformat()})
 status=p.read(p.R+'pipeline_status.json');status.update(status='PARTS_GATE_PASS',parts_generated=21,parts_approved=21,godot_handoff='READY_FOR_NATIVE_ANIMATION_VALIDATION',next_stage='NATIVE_RIG_AND_SIX_ANIMATIONS');p.save(p.R+'pipeline_status.json',status)
 print('21 formal parts PASS; native animation gate pending')
if __name__=='__main__':main()
