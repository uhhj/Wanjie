"""Combat-scale V3 gates bind visual approval to current source, parts and evidence."""
from rg_common import *
from recompose_roman_guard import render_config_digest

ANCHORS={'character_identity','overall_silhouette','head_anchor','shoulder_anchors','hip_anchors','knee_anchors','foot_ground_line','shield_default_position','sword_default_position','overall_proportions'}
def audit(section='all'):
    errors=[]
    try:
        m=read('tools/roman_guard_parts_manifest.json');r=read('reports/articulated_render_manifest_v3.json');g=read('reports/combat_rig_gate_v3.json')
        if not body_review_ok():errors.append('Complete body combat acceptance stale/missing')
        if g.get('policy')!='COMBAT_RIG_V3' or not g.get('reviewer') or not g.get('notes'):errors.append('Scoped visual review missing')
        if g['render_manifest_sha256']!=sha('reports/articulated_render_manifest_v3.json'):errors.append('Render manifest changed')
        if r['body_sha256']!=sha(body_source()):errors.append('Body source changed')
        if r['part_hashes']!={p['name']:sha(p['file']) for p in m['parts']}:errors.append('Formal parts differ from reviewed render')
        if g['mask_hashes']!={p['name']:sha(p['mask']) for p in m['parts']}:errors.append('Part masks differ from review')
        if r['pivot_sha256']!=sha('assets/units/odyssey/roman_guard/roman_guard_pivots.json'):errors.append('Pivot hints changed')
        if r['render_config_sha256']!=render_config_digest(m):errors.append('Draw order or clip masks changed')
        for file,digest in {**r['review_images'],**r['full_frames'],**g['extra_evidence']}.items():
            if sha(file)!=digest:errors.append('Evidence changed: '+file)
        expected={(j,a) for j in ['near_elbow','far_elbow','near_knee','far_knee'] for a in [-20,0,20]}
        if {(t['joint'],t['angle']) for t in r['tests']}!=expected or len(r['tests'])!=12:errors.append('Joint motion cases incomplete')
        if section in ['all','joints']:
            checks=g['joints']['combat_checks']
            if set(checks)!={j for j,a in expected} or any(set(v)!={'256','192'} or set(v.values())!={'PASS'} for v in checks.values()):errors.append('Joint combat review not PASS')
        if section in ['all','recomposition']:
            checks=g['recomposition']['combat_checks']
            if set(checks)!={'256','192'} or any(set(v)!=ANCHORS or set(v.values())!={'PASS'} for v in checks.values()):errors.append('Recomposition combat review not PASS')
        if section=='all':
            if g['shield']['status']!='PASS' or g['full_sword']['status']!='PASS':errors.append('Shield / full sword not PASS')
            if g['parts_structural']!={n:'PASS' for n in PARTS}:errors.append('Not all 19 parts structurally approved')
    except (FileNotFoundError,KeyError,ValueError,TypeError) as e:errors.append(str(e))
    return {'status':'PASS' if not errors else 'FAIL','policy':'COMBAT_RIG_V3','section':section,'errors':errors,'timestamp':now()}
