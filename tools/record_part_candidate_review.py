"""Record observed candidate failures without granting formal art approval."""
from rg_common import *

def main():
    assert body_review_ok()
    problems=[
        {'parts':['arm_near_upper','arm_near_fore'],'bbox':[273,620,398,735],'observed':'Elbow rotation exposes a flat skin cut and an outward skin flap.','action':'Refine the pair boundary and locally complete only missing elbow surface.'},
        {'parts':['arm_far_upper','arm_far_fore'],'bbox':[630,653,741,761],'observed':'Rotated forearm reveals a straight proximal cut and wedge at the brace transition.','action':'Review elbow cap ownership and local hidden surface.'},
        {'parts':['leg_near_thigh','leg_near_shin'],'bbox':[328,1020,458,1148],'observed':'Both knee rotations expose a seam above the knee plate; hole-growth heuristic fails.','action':'Complete hidden knee skin locally without duplicating the knee plate.'},
        {'parts':['leg_far_thigh','leg_far_shin'],'bbox':[578,1030,719,1150],'observed':'Far knee +20 degrees exposes an open horizontal wedge visible at 256px character height.','action':'Reconstruct local hidden knee surface and retest at combat scale.'},
        {'parts':['sword'],'bbox':[260,807,409,941],'observed':'Pommel and blade/guard are disconnected; handle hidden by the original fist is absent.','action':'Complete only missing grip and validate the hand socket.'},
        {'parts':['cape'],'bbox':[173,388,449,1050],'observed':'Visible-only cape retains body/arm-shaped cutouts; hidden cloth is incomplete.','action':'Review rear cape where moving limbs uncover it; preserve front/back draw passes.'}
    ]
    images=['reports/joint_rotation_test_v2.png','reports/joint_rotation_detail_v2.png','reports/parts_candidate_review_v2.png','reports/recomposition_combat_review_v2.png']
    write('reports/part_art_review_v2.json',{'status':'FAIL','scope':'PART_ART_AND_ARTICULATION_NOT_BODY_ALPHA','body_gate':'PASS_WITH_NON_BLOCKING_HIRES_EDGE_ARTIFACTS','problems':problems,'reviewer':'Codex visual review of candidates and native 256px motion sheet','images':{p:sha(p) for p in images},'no_alpha_touchup_requested':True,'timestamp':now()})
    m=read('tools/roman_guard_parts_manifest.json'); m['status']='BLOCKED_PART_ART_AND_JOINT_REVIEW'
    for part in m['parts']:
        matching=[p['observed'] for p in problems if part['name'] in p['parts']]
        part['art_review_status']='FAIL' if matching else 'REVIEW_REQUIRED'
        part['art_review_notes']=matching or ['Format/source pixels checked; anatomical boundary and attachment not approved.']
        if matching: part['missing_hidden_regions']=matching
        elif part['name'] not in EQUIPMENT:
            part['missing_hidden_regions']=[]
            part['hidden_surface_assessment']='Not automatically required; attachment range must be reviewed before promotion.'
        part['review_required']=True
    write('tools/roman_guard_parts_manifest.json',m)
    validation=read('reports/parts_candidate_validation_v2.json'); validation['status']='FORMAT_PASS_ART_FAIL'; validation['art_review']='reports/part_art_review_v2.json'
    for p in validation['parts']:
        current=next(x for x in m['parts'] if x['name']==p['name'])
        p['art_status']=current['art_review_status']; p['missing_hidden_regions']=current['missing_hidden_regions']
    write('reports/parts_candidate_validation_v2.json',validation)
    joints=read('reports/joint_rotation_metrics_v2.json')
    joints.update(visual_review_status='FAIL',visual_review='reports/part_art_review_v2.json',elbows='FAIL_VISUAL_SEAM',knees='FAIL_VISIBLE_GAPS',shield='PREVIEW_CLIPPING_AT_PLUS_7',sword='FAIL_INCOMPLETE_GRIP')
    joints['shield_note']='0.897% alpha mass falls outside fixed preview canvas at +7 degrees; record separately from texture defects. Native Sprite2D viewport must not clip to source canvas.'
    write('reports/joint_rotation_metrics_v2.json',joints)
    r=read('reports/recomposition_metrics_v2.json')
    r['visual_combat_review']='IDENTITY_AND_EQUIPMENT_LAYOUT_RECOGNIZABLE'
    r['visual_note']='Existing geometric gate fails. Body partitions reproduce accepted body alpha and visible RGB exactly; no new pixel-identity requirement was introduced.'
    write('reports/recomposition_metrics_v2.json',r)
    s=read('reports/final_status.json')
    s.update(verdict='BLOCKED',phase='COMBAT_SCALE_VISUAL_GATE_V1_AND_PART_CANDIDATES',art_pipeline='BLOCKED_PART_ART_AND_JOINT_REVIEW',hires_pixel_review='NON_BLOCKING_COMBAT_ARTIFACT',combat_scale_visual_review='PASS',complete_body={'status':'PASS_WITH_NON_BLOCKING_HIRES_EDGE_ARTIFACTS','gate':'reports/complete_body_gate_combat_v1.json','file':body_source(),'sha256':sha(body_source()),'format_integrity':'PASS','visual_status':'COMBAT_SCALE_PASS','blockers':[]},parts={'required_count':19,'candidate_generated_extracted_count':19,'candidate_missing_count':0,'candidate_format_pass_count':19,'formal_generated_extracted_count':0,'formal_missing_count':19,'body_masks_missing_count':0,'art_review':'FAIL'},recomposition={'execution':'CANDIDATE_TEST_EXECUTED','gate':'FAIL','metrics':'reports/recomposition_metrics_v2.json','visible_body_reassembly':'EXACT'},joint_tests={'execution':'18_REAL_CANDIDATE_CASES','elbows':joints['elbows'],'knees':joints['knees'],'shield':joints['shield'],'sword':joints['sword'],'metrics':'reports/joint_rotation_metrics_v2.json'},godot_handoff='NOT_READY',manual_review_images=['reports/combat_scale_visual_review.png']+images,timestamp=now())
    s['current_continuation']={'task':'COMBAT_SCALE_VISUAL_GATE_V1','ai_calls':0,'stages_001_through_005_executed':False,'clean_candidate_unchanged':True,'rgb_and_initial_alpha_unchanged':True,'region_001_through_005_touchup':'STOPPED','new_character_or_animation_created':False}
    s['tools_tests']={'status':'PASS','pipeline_safety_tests':12,'combat_gate_tests':6,'evidence':['reports/validation_run.json','reports/combat_gate_tool_tests.json']}
    s['git']['commits_before_this_report']=['1bf9e592b044aaecbadd50d10eb887fd363e4a9c']
    s['git']['final_report_commit_subject']='feat: accept combat-scale body and review articulated part candidates'
    write('reports/final_status.json',s)
    paths=[config()['source'],'D:/Wanjie/documents/pictures/OD_UNIT_01_ROMAN_GUARD_RIG_MASTER_V1.png','work/05_complete_body_candidate_v2.png','work/05_complete_body_candidate_v2_rgba.png',body_source()]
    assert sha(body_source())=='df706ed02285e40b2532085d76e9936bba073eec0180e40bf63e94b35de26dfd'
    assert r['body_reassembly_alpha_changed_pixels']==r['body_reassembly_visible_rgb_changed_pixels']==0
    write('reports/combat_continuation_integrity.json',{'status':'PASS','read_only_files':{p:sha(p) for p in paths},'body_alpha_and_visible_rgb_reassembly_exact':True,'ai_calls':0,'timestamp':now()})

if __name__=='__main__': main()
