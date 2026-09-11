import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from rg_common import *

joints={
 'near_shoulder':([388,510],120),'near_elbow':([333,675],84),'near_wrist':([330,832],62),
 'far_shoulder':([630,576],100),'far_elbow':([675,682],82),'far_wrist':([729,784],66),
 'near_hip':([428,977],112),'near_knee':([405,1101],102),'near_ankle':([333,1340],78),
 'far_hip':([612,975],110),'far_knee':([672,1100],100),'far_ankle':([656,1338],80)}
hints={
 'head':('neck',[538,373]),'helmet':('head',[537,290]),'torso':('waist',[533,695]),'pelvis':('pelvis',[530,967]),
 'arm_near_upper':('near_shoulder',joints['near_shoulder'][0]),'arm_near_fore':('near_elbow',joints['near_elbow'][0]),'hand_near':('near_wrist',joints['near_wrist'][0]),
 'arm_far_upper':('far_shoulder',joints['far_shoulder'][0]),'arm_far_fore':('far_elbow',joints['far_elbow'][0]),'hand_far':('far_wrist',joints['far_wrist'][0]),
 'leg_near_thigh':('near_hip',joints['near_hip'][0]),'leg_near_shin':('near_knee',joints['near_knee'][0]),'foot_near':('near_ankle',joints['near_ankle'][0]),
 'leg_far_thigh':('far_hip',joints['far_hip'][0]),'leg_far_shin':('far_knee',joints['far_knee'][0]),'foot_far':('far_ankle',joints['far_ankle'][0]),
 'shield':('shield_grip',[744,821]),'sword':('sword_grip',[328,867]),'cape':('cape_attachment',[508,415])}
parts=[]
for name in PARTS:
    anchor,pos=hints[name]; equip=name in EQUIPMENT
    parts.append({'name':name,'file':f'assets/units/odyssey/roman_guard/parts/{name}.png','candidate_file':f'work/candidates/parts/{name}.png','source':config()['source'] if equip else 'work/03_complete_body_base.png','ai_completed':False,'review_required':True,'status':'MASK_REVIEW_REQUIRED' if equip else 'BLOCKED_BODY_REVIEW','mask':f"work/masks/{'equipment' if equip else 'parts'}/{name}.png",'mask_sha256':None,'mask_status':'DRAFT' if equip else 'NOT_CREATED_NO_RELIABLE_BOUNDARY','pivot_hint':{'anchor':anchor,'position':pos,'coordinate_space':'source canvas pixels, top-left origin','confidence':'initial_visual_hint_only','review_required':True},'missing_hidden_regions':([] if name=='shield' else ['Handle section hidden by gripping fingers; do not synthesize by cutting neighboring skin pixels.'] if name=='sword' else ['Cape behind torso/arm/leg; continuous rear silhouette and attachment need completion.'] if name=='cape' else ['Evaluate only after complete body passes; anatomical hidden joint surfaces and 20-30% overlap not established.'])})
# Exact source alpha supplies the equipment outer contour. The shield's right
# envelope is widened only into otherwise empty source canvas (no other body there).
m=mask('work/masks/equipment/shield.png'); d=ImageDraw.Draw(m); d.rectangle((780,400,1023,1300),fill=255); m.save(ROOT/'work/masks/equipment/shield.png')
front=Image.new('L',(1024,1536)); d=ImageDraw.Draw(front)
for poly in read('tools/occlusion_masks.json')['polygons']['cape'][1:]: d.polygon([tuple(p) for p in poly],fill=255)
front.save(ROOT/'work/masks/cape_front_region.png'); Image.fromarray(255-np.array(front)).save(ROOT/'work/masks/cape_back_region.png')
for p in parts:
    if (ROOT/p['mask']).exists(): p['mask_sha256']=sha(p['mask'])
order=['cape','leg_far_thigh','leg_far_shin','foot_far','arm_far_upper','arm_far_fore','hand_far','leg_near_thigh','leg_near_shin','foot_near','pelvis','torso','cape','head','helmet','arm_near_upper','arm_near_fore','sword','hand_near','shield']
passes=[]; count=0
for name in order:
    draw={'part':name}
    if name=='cape': draw['clip_mask']='work/masks/cape_back_region.png' if count==0 else 'work/masks/cape_front_region.png'; count+=1
    passes.append(draw)
write('tools/roman_guard_parts_manifest.json',{'unit_id':'OD_UNIT_01_ROMAN_GUARD','version':'RIG_ASSET_V1','source_id':'OD_UNIT_01_ROMAN_GUARD_RIG_MASTER_V1','canvas_width':1024,'canvas_height':1536,'alpha_required':True,'required_count':19,'status':'BLOCKED_BODY_REVIEW','draw_passes_review_required':True,'draw_passes':passes,'draw_order_note':'Cape is one core texture but two clipped native Sprite2D draws: back before torso, front collar after torso. Clip masks partition the texture without overlap. Sword is drawn before gripping near hand. No new unit or third-party plugin.','parts':parts})
write('assets/units/odyssey/roman_guard/roman_guard_pivots.json',{'unit_id':'OD_UNIT_01_ROMAN_GUARD','canvas':[1024,1536],'status':'INITIAL_HINTS_REVIEW_REQUIRED','coordinate_space':'pixels from top-left; near=viewer-left sword side, far=viewer-right shield side','parts':{n:{'anchor':v[0],'position':v[1],'review_required':True} for n,v in hints.items()},'joints':{n:{'position':v[0],'diameter_hint_px':v[1],'overlap_target_fraction':.25,'overlap_hint_px':round(v[1]*.25),'review_required':True} for n,v in joints.items()},'warning':'Coordinates are source-derived initial suggestions, not measured skeletal centers. Adjust only after reviewing full-body masks and rotation contacts.'})
reviews=read('reports/art_reviews.json')
reviews['003_remove_cape']={'status':'FAIL','file':'work/03_complete_body_base.png','sha256':sha('work/03_complete_body_base.png'),'reviewer':'Codex visual inspection','notes':'Cape removal candidate reviewed at full canvas and neck/shoulder detail. AI introduced a raised collar whose design is not established by visible source armor; edge matte and source-to-completion continuity require correction. Not approved.','timestamp':now()}
reviews['complete_body']={'status':'FAIL','file':'work/03_complete_body_base.png','sha256':sha('work/03_complete_body_base.png'),'reviewer':'Codex visual inspection','notes':'STOP_ART_PIPELINE. Double hands/legs exist and equipment is removed, but diagonal skirt folds/color seam and local matte artifacts remain. The added raised collar requires correction to conservative continuation of the visible source design. Do not split this body or use it in Godot.','timestamp':now()}
write('reports/art_reviews.json',reviews)
cap=read('reports/image_edit_capabilities.json'); cap.update(verified_call_status='THREE_REAL_CALLS_RETURNED_RGB_WITH_BAKED_CHECKERBOARD',reliable_native_mask_inpainting_verified=False,standalone_api_key_configured=False,local_repository='D:/Wanjie/documents/uhhj',git='Initialized new local repository on user request; no remote created.',manual_step_reason='Tool exists and was called, but did not return true alpha and reference guidance did not preserve local continuity sufficiently for production.'); write('reports/image_edit_capabilities.json',cap)
for stage in config()['stages']:
    job=read('reports/ai_jobs/'+stage['id']+'.json'); invocation=read('reports/ai_jobs/'+stage['id'][:3]+'_tool_invocation.json')
    invocation.update(status='RETURNED_REAL_IMAGE',output_file=job['raw_output'],output_sha256=job['raw_output_sha256'],input_sha256=job['input_sha256'],finished_utc=job['timestamp'],raw_mode='RGB')
    if stage['id'].startswith('001'): guide='work/masks/001_tool_guide.png'
    elif stage['id'].startswith('003'): guide='work/masks/003_tool_guide.png'; invocation['referenced_image_paths'][1]=guide
    else: guide=stage['mask']
    invocation['guide_sha256']=sha(guide)
    write('reports/ai_jobs/'+stage['id'][:3]+'_tool_invocation.json',invocation)
    job['actual_tool_invocation']=f"reports/ai_jobs/{stage['id'][:3]}_tool_invocation.json"
    job['actual_tool_prompt']=invocation['prompt']; job['art_review_status']=reviews.get(stage['id'],{}).get('status'); write('reports/ai_jobs/'+stage['id']+'.json',job)
print('19-part manifest, pivot hints, explicit failed art gates and tool provenance saved')
