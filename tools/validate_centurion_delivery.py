"""Final artifact integrity and technical delivery gate; never fabricates art approval."""
import numpy as np
from PIL import Image,ImageDraw
import roman_centurion_pipeline as p
def main():
 p.verify();body=p.W+'03_complete_body_v2.png';assert p.sha(body)==p.read(p.R+'complete_body_gate_v2.json')['input_sha256']
 manifest=p.read('tools/roman_centurion_parts_manifest.json');assert manifest['status']=='PASS' and len(manifest['parts'])==21
 for part in manifest['parts']:
  assert p.sha(part['file'])==part['sha256'];im=Image.open(p.ROOT/part['file']);assert im.mode=='RGBA' and im.size==(1024,1536)
 scene='scenes/units/odyssey/roman_centurion/roman_centurion_rig.tscn';h=p.sha(scene)
 tests=p.read(p.R+'native/headless_tests.json');capture=p.read(p.R+'native/capture_manifest.json');stress=p.read(p.R+'native/stress_baseline.json')
 assert tests['status']=='PASS' and p.read(p.R+'native/rig_lab_tests.json')['status']=='PASS'
 assert tests['scene_sha256']==capture['scene_sha256']==stress['scene_sha256']==h
 assert len(capture['frames'])==192 and not any(row['clipped'] for row in capture['frames'])
 for row in capture['frames']:assert p.sha(row['file'].replace('res://',''))==row['sha256']
 for number in [20,50]:assert len([row for row in stress['records'] if row['units']==number])==4
 contacts=p.read(p.R+'native/walk_foot_contacts.json');sheet=Image.new('RGB',(1000,530),'white');d=ImageDraw.Draw(sheet)
 d.text((20,15),'Walk: fixed material-point world contact during stance',fill='black')
 d.text((20,36),f'Max interpolated drift at 256px: {tests["interpolated_support_drift_256px"]:.3f} px',fill='black')
 colors={'near':'#a13d31','far':'#246991'}
 for j,side in enumerate(['near','far']):
  y0=75+j*220;d.text((20,y0),side+' support intervals / world X',fill=colors[side]);d.line([(60,y0+180),(960,y0+180)],fill='gray')
  groups={}
  for row in contacts['samples']:
   if row['side']==side:groups.setdefault(row['support_id'],[]).append(row)
  for rows in groups.values():
   points=[(60+r['phase']*900,y0+160-(r['world'][0]-450)*.23) for r in rows]
   if len(points)>1:d.line(points,fill=colors[side],width=2)
  d.text((60,y0+185),'phase 0',fill='black');d.text((905,y0+185),'phase 1',fill='black')
 sheet.save(p.ROOT/p.R/'native/walk_foot_contact_debug.png')
 report={'status':'TECHNICAL_PASS','unit_id':'OD_UNIT_03_ROMAN_CENTURION','body_gate':'PASS','parts_gate':'PASS','parts_count':21,'bones':23,'sprites':21,'native_polygon_bindings':10,'animations':6,'headless':'PASS','rig_lab':'PASS','attack_hit':tests['attack_hit'],'command_release':tests['command_release'],'interpolated_foot_drift_256px':tests['interpolated_support_drift_256px'],'gpu_frames':192,'clipped_frames':0,'stress':stress['records'],'scene_sha256':h,'source_body_sha256':p.sha(body),'existing_units_and_sources_unchanged':True,'visual_approval':'See animation_visual_gate.json; technical pass does not confer user art approval'}
 p.save(p.R+'native/delivery_validation.json',report);print('TECHNICAL_PASS: immutable sources, 21 parts, 23 bones, 6 animations, 192 GPU frames, events and 20/50 unit benchmarks')
if __name__=='__main__':main()
