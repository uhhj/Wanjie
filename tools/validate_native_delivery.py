"""Validate native evidence and explicit visual reviews; never infer an art approval."""
import subprocess
from rg_common import *

def main():
    errors=[]
    def check(value,message):
        if not value:errors.append(message)
    baseline=read('reports/native_rig_v2/frozen_asset_baseline.json')
    committed=json.loads(subprocess.check_output(['git','show','3f3b1dd:reports/native_rig_v2/frozen_asset_baseline.json'],cwd=ROOT))
    check(baseline==committed,'Frozen baseline changed')
    for p,digest in committed['files'].items():check(sha(p)==digest,'Changed formal asset: '+p)
    check(sha(committed['body_file'])==committed['body_sha256'],'Complete Body changed')
    check(sha('assets/units/odyssey/roman_guard/near_knee_skinning_v1.json')==committed['near_knee_mesh_sha256'],'Approved near knee weights changed')
    check(read('reports/final_status.json')['verdict']=='PASS','Asset gate is not PASS')
    headless=read('reports/native_rig_v2/headless_tests.json');lab=read('reports/native_rig_v2/rig_lab_tests.json');stress=read('reports/native_rig_v2/stress_results.json')
    check(headless['status']=='PASS','Native tests failed');check(lab['status']=='PASS','Lab tests failed')
    check(headless['attack_hit_count']==1,'Attack event count mismatch')
    check(headless['bone_count']==23 and headless['polygon_count']==4,'Native bone/mesh counts differ')
    check(headless['runtime_support_drift_at_256px']<1,'Visible runtime foot slide')
    check(headless['engine']['string'].startswith('4.7.2-stable'),'Wrong engine')
    for name in ['editor_import.log','headless_tests.log','rig_lab_tests.log']:
        raw=(ROOT/'reports/native_rig_v2'/name).read_bytes()
        log=raw.decode('utf-16' if raw.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8',errors='replace')
        check('ERROR:' not in log and 'SCRIPT ERROR' not in log,'Engine error in '+name)
    for count in [20,50]:
        rows=[r for r in stress['results'] if r['units']==count]
        check(len(rows)==5 and all(r['fps']>0 and r['viewport']==[1920,1080] for r in rows),f'Incomplete {count}-unit desktop stress evidence')
    original=np.array(rgba('reports/roman_guard_recomposed_v3.png'))
    native=np.array(rgba('reports/native_rig_v2/rest_pose_native.png'))
    check(original.shape==native.shape,'Rest canvas mismatch')
    a=original[:,:,3]>32;b=native[:,:,3]>32;union=a|b
    iou=float((a&b).sum()/max(1,union.sum()))
    check(iou>.9999,'Rest silhouette moved')
    difference=np.abs(original.astype(int)-native.astype(int))
    rest={'status':'PASS' if iou>.9999 else 'FAIL','alpha_threshold':32,'silhouette_iou':iou,'rgba_mae_foreground_union':float(difference[union].mean()),'reference_sha256':sha('reports/roman_guard_recomposed_v3.png'),'native_sha256':sha('reports/native_rig_v2/rest_pose_native.png')}
    write('reports/native_rig_v2/rest_pose_metrics.json',rest)
    Image.fromarray(np.clip(difference[:,:,:3]*8,0,255).astype('uint8')).save(ROOT/'reports/native_rig_v2/rest_pose_diff_x8.png')
    anims=read('resources/roman_guard_animations_v1.json')
    for part in ['arm_near_upper','arm_far_upper','foot_far']:
        mesh=read(f'resources/{part}_local_skinning.json')
        check(mesh['texture_sha256']==sha(mesh['texture_file']),'Local skinning uses stale pixels')
        weights=np.array(mesh['moving_weights'])+np.array(mesh['stationary_weights'])
        check(np.allclose(weights,1),'Non-normalized skinning weights')
    review_path=ROOT/'reports/native_rig_v2/visual_approval.json'
    review=read(str(review_path)) if review_path.exists() else {'animations':{}}
    statuses={}
    for name in ['idle','walk','attack_01','hit','death']:
        entry=review['animations'].get(name,{})
        sheet=f'reports/animations/{name}_combat_review.png'
        valid=entry.get('status')=='PASS' and entry.get('sheet_sha256')==sha(sheet) and review.get('animation_source_sha256')==sha('resources/roman_guard_animations_v1.json')
        statuses[name]='PASS' if valid else 'VISUAL_REVIEW_REQUIRED'
    technical='PASS' if not errors else 'FAIL'
    all_pass=technical=='PASS' and all(s=='PASS' for s in statuses.values())
    gate={'task':'ROMAN_GUARD_NATIVE_RIG_VERTICAL_SLICE_V2','verdict':'ROMAN_GUARD_NATIVE_RIG_VERTICAL_SLICE_SUPPORTED' if all_pass else ('PENDING_VISUAL_REVIEW' if not errors else 'BLOCKED_TECHNICAL_VALIDATION'),'native_rig_pipeline':'SUPPORTED' if all_pass else 'NOT_YET_APPROVED','technical_status':technical,'errors':errors,'assets':{'core':19,'attachment':1,'unchanged':not any('changed' in e.lower() for e in errors)},'rig':{'bones':23,'sprite_nodes':20,'polygon_nodes':4,'active_art_draws':21},'animations':statuses,'attack_hit_count':headless['attack_hit_count'],'walk_support_drift_256px':headless['runtime_support_drift_at_256px'],'rest':rest,'stress':stress['results'],'godot':read('reports/native_rig_v2/engine_manifest.json'),'source_animation_sha256':sha('resources/roman_guard_animations_v1.json'),'flags':['NON_BLOCKING_COMBAT_ARTIFACT: five frozen HIRES alpha findings','Small rigid cape motion; cape_mid/tip reserved, not simulated cloth','Death stress measurement represents held corpses after warm-up','Desktop baseline only; GPU GeForce GTX 1650'],'visual_approval_file':'reports/native_rig_v2/visual_approval.json'}
    gate['visual_acceptance_level']=review.get('acceptance_level','UNSPECIFIED')
    polish_path=ROOT/'reports/walk_polish_v1/walk_polish_metrics.json'
    if polish_path.exists():
        polish=read(str(polish_path))
        if polish.get('animation_source_sha256')==sha('resources/roman_guard_animations_v1.json'):
            gate['walk_keyframe_polish']=polish
            gate['flags'].append('Walk-only keyframe polish verified; FPS table is the prior desktop baseline, not remeasured for this keyframe update')
    if review.get('acceptance_level')=='PROVISIONAL_COMBAT_ACCEPTANCE_WITH_QUALITY_RESERVATIONS':
        gate['flags'].insert(0,'PROVISIONAL_COMBAT_ACCEPTANCE: user accepted with 将就了吧; usable prototype, animation polish remains below final-quality expectation')
    write('reports/native_rig_v2/native_gate_v2.json',gate)
    print(gate['verdict'],technical,statuses)
    for e in errors:print('ERROR',e)
    return 1 if errors else 0

if __name__=='__main__':raise SystemExit(main())
