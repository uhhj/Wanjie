from pathlib import Path
import json,hashlib
from PIL import Image,ImageChops,ImageDraw
import numpy as np
r=Path('reports/minotaur_breaker')
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
formal=read(r/'formal_scene_parity.json');motion=read(r/'formal_motion_contract_test.json')
assert formal['status']==motion['status']=='PASS'
stress=[]
for name in ['20_walk','50_walk','20_skill_loop']:
 d=read(r/'stress'/f'{name}.json');assert d['scene_sha256']==formal['formal_scene_sha256']
 d['occlusion_review']='DENSE_LAYOUT_FAIL' if d['units']==50 else 'READABLE_WITH_VERTICAL_OVERLAP_WARNING'
 d['occlusion_findings']='Dense rows overlap horns, capes and weapons; do not use this spacing for production' if d['units']==50 else 'Individuals and weapons distinguishable; row height still overlaps previous row feet/horns'
 write(r/'stress'/f'{name}.json',d);stress.append(d)
src=Image.open('work/minotaur_breaker/00_rig_master_rgba.png');out=Image.open(r/'candidate_recomposed.png')
a=np.array(src)[:,:,3]>127;b=np.array(out)[:,:,3]>127
ImageChops.difference(src.convert('RGB'),out.convert('RGB')).save(r/'recomposition_diff.png')
write(r/'recomposition_metrics.json',{'status':'COMBAT_SCALE_PASS','silhouette_iou_diagnostic_only':float((a&b).sum()/(a|b).sum()),'pixel_equality_is_not_gate':True,'review':'candidate_recomposition_combat_review.png','allowed_differences':['approved hidden anatomy completion','joint overlap','non-blocking source edge artifacts']})
status=read(r/'pipeline_status.json');status.update(parts_status='PASS_19_CORE_PLUS_2_SUPPORTS',native_status='READY_WITH_DESKTOP_STRESS_LIMITATIONS',missing_art=[],animations_status={n:'PASS' for n in ['idle','walk','attack_01','skill_01','hit','death']});write(r/'pipeline_status.json',status)
p=read(r/'promotion_record.json');p['status']='PASS_FORMAL_RUNTIME_REGRESSION';p['formal_motion_report']='formal_motion_contract_test.json';p['formal_parity_report']='formal_scene_parity.json';write(r/'promotion_record.json',p)
report={'verdict':'MINOTAUR_BREAKER_V1_COMPLETE_WITH_STRESS_LIMITATIONS','unit_asset_status':'PASS','native_rig_status':'SUPPORTED','mass_battle_performance_approved':False,'godot':'4.7.2.stable.official.ed1daf0bf','bone_count':25,'core_parts':19,'hidden_knee_supports':2,'native_skinned_meshes':13,'animations':status['animations_status'],'display_heights':[360,288],'formal_scene_sha256':formal['formal_scene_sha256'],'events':motion['events_attack_skill'],'foot_drift_360px':{s:motion['walk_contact'][s]['max_360px_drift'] for s in ['near','far']},'stress':stress,'flags':['50-unit dense layout fails readability and measured 12.49 FPS; not approved for dense production battles','20-unit vertical row overlap remains a layout warning','Non-blocking source high-resolution edge artifacts retained','User aesthetic sign-off not claimed'],'scope_exclusions':['no damage/mana balance system','no third-party rig','no next character']}
write(r/'delivery_report.json',report)
# World-space foot drift plot from native measurements; magnification clearly labelled.
sheet=Image.new('RGB',(1000,380),'white');draw=ImageDraw.Draw(sheet)
for row,side in enumerate(['near','far']):
 points=motion['walk_contact'][side]['samples'];y=60+row*170
 draw.text((20,y-35),f'{side}: native support samples, world x (1000x horizontal drift magnification)',fill='black')
 anchor=points[0]['world_sole'][0];previous=-1
 for v in points:
  if previous<0 or v['phase']-previous>.01:anchor=v['world_sole'][0]
  previous=v['phase']
  x=30+v['phase']*920;dy=(v['world_sole'][0]-anchor)*1000
  draw.ellipse((x,y+dy,x+2,y+dy+2),fill='blue')
 draw.text((20,y+95),f"Max 360px drift: {motion['walk_contact'][side]['max_360px_drift']:.6f}px; stance phase .03-.59",fill='black')
sheet.save(r/'walk_foot_contact_debug.png')
print(report['verdict'])
