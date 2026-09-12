"""Fail closed. Only a current complete asset package can be handed to native Godot rigging."""
from rg_common import *
from validate_parts import validate
from recompose_roman_guard import render_config_digest
def main():
    if config().get('asset_gate_policy')=='COMBAT_RIG_V3':
        from combat_rig_gate import audit
        parts=validate();review=audit();errors=parts['errors']+review['errors']
        result={'status':'READY' if not errors else 'NOT_READY','policy':'COMBAT_RIG_V3','required_engine':'Godot 4.7.2 Stable','rig_id':'HUMAN_MEDIUM_RIG_V1','native_nodes':['Skeleton2D','Bone2D'],'third_party_skeleton_plugins':False,'parts_structurally_approved':parts['generated_formal_count'] if parts['status']=='PASS' else 0,'errors':errors,'scope':'Asset handoff approval, not a claim that Godot scenes or animations have been built','timestamp':now()}
        write('reports/godot_handoff.json',result);print(result['status']);return 0 if not errors else 2
    parts=validate(); errors=list(parts['errors']); m=read('tools/roman_guard_parts_manifest.json')
    hashes={p['name']:sha(p['file']) for p in m['parts'] if (ROOT/p['file']).exists()}
    for report,path in [('reports/recomposition_metrics.json','reports/roman_guard_recomposed.png'),('reports/joint_rotation_metrics.json','reports/joint_rotation_test.png')]:
        if not (ROOT/report).exists(): errors.append(report+' missing'); continue
        data=read(report)
        if data.get('status')!='PASS': errors.append(report+' is not PASS')
        if data.get('part_hashes')!=hashes: errors.append(report+' does not match current part hashes')
        if data.get('render_config_sha256')!=render_config_digest(m): errors.append(report+' draw order / clip masks changed')
        if not (ROOT/path).exists() or data.get('output_sha256')!=sha(path): errors.append(path+' absent or stale')
        if 'joint_rotation' in report and data.get('pivot_config_sha256')!=sha('assets/units/odyssey/roman_guard/roman_guard_pivots.json'): errors.append('Joint test pivot configuration changed')
    pivots=read('assets/units/odyssey/roman_guard/roman_guard_pivots.json')
    for p in m['parts']:
        if p.get('pivot_hint',{}).get('position')!=pivots['parts'][p['name']]['position']: errors.append(p['name']+': manifest and preview pivot hints differ')
    # Initial pivot hints may be adjusted in Godot; the current rotation review
    # must match those exact hints, without requiring final in-engine placement.
    ready=not errors
    write('reports/godot_handoff.json',{'status':'READY' if ready else 'NOT_READY','required_engine':'Godot 4.7.2 Stable','rig_id':'HUMAN_MEDIUM_RIG_V1','native_nodes':['Skeleton2D','Bone2D'],'animations':['idle','walk','attack_01','hit','death'],'third_party_skeleton_plugins':False,'errors':errors,'timestamp':now()})
    print('READY' if ready else 'NOT_READY'); return 0 if ready else 2
if __name__=='__main__': raise SystemExit(main())
