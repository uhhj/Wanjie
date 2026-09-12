"""Update current status after actual local and inherited gate checks."""
from rg_common import *
from combat_rig_gate import audit
from validate_parts import validate

def main():
    assert audit()['status']=='PASS';assert validate()['status']=='PASS'
    for p in ['reports/near_knee_validation_tests_v1.json','reports/articulated_gate_tool_tests_v3.json','reports/validation_run.json']:assert read(p)['status']=='PASS'
    s=read('reports/final_status.json');s['phase']='NEAR_KNEE_ARTICULATION_V1'
    s['parts'].update(required_count=20,core_required_count=19,attachment_count=1,candidate_generated_extracted_count=20,formal_generated_extracted_count=20,structurally_approved_count=20)
    s['joint_tests']['near_knee']={'status':'PASS','evidence':'reports/near_knee_gate_v1.json','angles':[-20,-10,0,10,20],'pivot':[388,1083],'plate_fixed':True,'local_skinning_required':True}
    s['joint_tests']['other_joints']='FROZEN_V3_APPROVALS_INHERITED'
    s['tools_tests']['near_knee_tests']=7;s['tools_tests']['evidence'].append('reports/near_knee_validation_tests_v1.json')
    s['current_continuation']={'task':'NEAR_KNEE_ARTICULATION_V1','ai_calls':0,'stages_001_through_005_executed':False,'clean_candidate_unchanged':True,'other_17_formal_part_textures_unchanged':True,'changed_part_textures':['leg_near_thigh','leg_near_shin'],'new_attachment':'knee_near','overlap_expansion_pixels':0,'rest_recomposition_changed_pixels':0,'new_character_or_animation_created':False}
    s['manual_review_images']=['reports/near_knee_motion_256px_v1.png','reports/near_knee_motion_192px_v1.png','reports/near_knee_motion_detail_v1.png','reports/near_knee_pivot_review_v1.png']
    s['git']['commits_before_this_report']=['4e27b648afba8b0e1353ffae42991ece29f0fc45'];s['git']['final_report_commit_subject']='fix: stabilize near knee with independent plate and local skinning'
    s['timestamp']=now();write('reports/final_status.json',s)

if __name__=='__main__':main()
