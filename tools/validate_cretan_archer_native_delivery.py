"""Fail-closed final Archer delivery check against current art and native inputs."""
import json
from pathlib import Path
import cretan_archer_pipeline as p

N=p.REPORT+'native/'
NAMES=['idle','walk','attack_01','hit','death']

def main():
    errors=[]
    def check(ok,message):
        if not ok:errors.append(message)
    def current_hashes(record,label):
        hashes=record.get('artifact_inputs',{})
        check(bool(hashes),label+': missing artifact hashes')
        for path,digest in hashes.items():
            local=path.replace('res://','')
            check((p.ROOT/local).is_file() and p.sha(local)==digest,label+': stale '+path)
    p.verify_frozen();check(p.valid_external_body(),'Approved Body provenance changed')
    check(p.load(p.REPORT+'complete_body_gate.json')['status']=='PASS','Complete Body gate not PASS')
    m=p.load('tools/cretan_archer_parts_manifest.json');check(m['status']=='PASS' and len(m['parts'])==20,'Formal part set not PASS')
    for part in m['parts']:
        check(part['status']=='PASS' and p.sha(part['file'])==part['sha256'],'Missing/stale formal part '+part['name'])
    art=p.load(m['approved_review']);check(art['status']=='PASS' and all(art['checks'].values()),'Asset visual gate failed')
    for part in m['parts']:check(art['part_sha256'][part['name']]==part['sha256'],'Stale asset review '+part['name'])
    test=p.load(N+'headless_tests.json');capture=p.load(N+'capture_manifest.json');smoke=p.load(N+'smoke_20_walk.json')
    visual=p.load(N+'visual_gate.json');lab=p.load(N+'rig_lab_startup.json')
    for label,record,valid in [('headless',test,'PASS'),('capture',capture,'PASS'),('smoke',smoke,'COMPLETED'),('lab',lab,'PASS')]:
        check(record['status']==valid,label+' did not pass');current_hashes(record,label)
        engine=record['engine'];check([engine['major'],engine['minor'],engine['patch'],engine['status']]==[4,7,2,'stable'],label+': wrong engine')
    check(test['attack_release_count']==1 and test['observed_release_events_two_plays']==2 and test['method_key_count']==1,'Event must be exactly once per playback')
    check(not capture['clipped_frames'] and capture['frames_per_animation_per_scale']==16,'Incomplete/clipped GPU captures')
    check(capture['display_server']!='headless' and smoke['display_server']!='headless','GPU evidence cannot be headless FPS/frames')
    for frame in capture['frames']:
        check(p.sha(frame['path'].replace('res://',''))==frame['sha256'],'Stale native frame '+frame['path'])
    check(smoke['units']==20 and smoke['measured_seconds']>=20 and smoke['rendered_frames']>0 and smoke['viewport']==[1920,1080],'Incomplete desktop smoke')
    check(lab['dropdown_animation_count']==5 and lab['attack_release_observed']==1,'Incomplete Rig Lab controls/event check')
    check(lab['display_server']!='headless' and p.sha(lab['screenshot'].replace('res://',''))==lab['screenshot_sha256'],'Missing/stale actual Rig Lab screenshot')
    check(visual['status']=='PASS' and set(visual['animations'])==set(NAMES),'Native visual gate not PASS')
    check(visual['capture_manifest_sha256']==p.sha(N+'capture_manifest.json'),'Stale native visual review')
    for name in NAMES:
        check(visual['animations'][name]['256px']=='PASS' and visual['animations'][name]['192px']=='PASS','Animation visual FAIL '+name)
    data=p.load('resources/cretan_archer_rig_v1.json')
    check(data['shared_skeleton_sha256']==p.sha(data['shared_skeleton_source']),'Shared family source changed')
    check(len(data['bones'])==26 and data['new_bones']==['bow_socket','arrow_socket','quiver_socket'],'Unexpected rig replacement or extensions')
    check(test['bone_count']==26,'Native reused bone count wrong')
    verdict='CRETAN_ARCHER_NATIVE_RIG_REUSE_SUPPORTED' if not errors else 'BLOCKED_NATIVE_VALIDATION'
    result={'verdict':verdict,'status':'PASS' if not errors else 'FAIL','errors':errors,'complete_body':'PASS',
            'parts':'20/20 PASS','rig_family':'HUMAN_MEDIUM_RIG_V1','native_bones':26,'reused_bones':23,'new_sockets':3,
            'animations':visual['animations'],'attack_release_count':test['attack_release_count'],
            'headless':test['status'],'rig_lab':lab['status'],'foot_slide':test['foot_slide'],'twenty_unit_smoke':smoke['status'],
            'desktop_fps':smoke['fps'],'renderer':smoke['renderer'],'mobile_performance_claimed':False,
            'flags':visual.get('non_blocking_flags',[]),'capture_manifest_sha256':p.sha(N+'capture_manifest.json'),
            'formal_manifest_sha256':p.sha('tools/cretan_archer_parts_manifest.json'),'timestamp':p.now()}
    p.save(N+'delivery_gate.json',result)
    state=p.load(p.REPORT+'pipeline_status.json');state.update(verdict=verdict,
          animations={n:'PASS' if not errors else 'SEE_NATIVE_GATE' for n in NAMES},attack_release='PASS_EXACTLY_ONCE' if test['status']=='PASS' else 'FAIL',
          twenty_unit_smoke=smoke['status'],human_medium_rig_reuse='SUPPORTED' if not errors else 'VALIDATION_PENDING',
          godot_handoff='READY' if not errors else 'NOT_READY',native_gate=result['status'],note='Art and native evidence checked independently against current SHA; desktop-only smoke; no third unit or combat system.')
    p.save(p.REPORT+'pipeline_status.json',state)
    print(json.dumps({k:v for k,v in result.items() if k not in ['foot_slide','animations']},ensure_ascii=False));return 0 if not errors else 2

if __name__=='__main__':raise SystemExit(main())
