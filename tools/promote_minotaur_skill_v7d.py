"""Skill V4 promotion; attack V4 and the four other clips stay locked."""
from pathlib import Path
import hashlib,json,subprocess,shutil
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'reports/minotaur_breaker'
BASE="73a332d"
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    capture=read(R/'actions_v4_capture_manifest.json');review=read(R/'skill_v7d_visual_review.json')
    assert review['status']=='PASS' and review['artifact_inputs']==capture['artifact_inputs']
    assert capture['inputs_unchanged_during_capture']
    assert len(capture['frames'])==128 and len({(f['animation'],f['height'],f['frame']) for f in capture['frames']})==128
    assert capture['events_attack_skill']=={'attack_01':[1,0],'skill_01':[0,1]}
    for file,digest in capture['artifact_inputs'].items():assert sha(ROOT/file.removeprefix('res://'))==digest,file
    for f in capture['frames']:assert sha(ROOT/f['path'].removeprefix('res://'))==f['sha256']
    for name in ['skill_v7d_test','attack_v4_test','candidate_ik_reach','candidate_format_validation']:assert read(R/(name+'.json'))['status']=='PASS'
    previous=json.loads(subprocess.check_output(['git','show',BASE+':resources/minotaur_breaker_animations_v1.json'],cwd=ROOT))
    current=read(ROOT/'resources/minotaur_breaker_animation_candidates.json')
    for name in ['idle','walk','attack_01','hit','death']:assert previous[name]==current[name],name
    for path in ['resources/minotaur_breaker_rig_v1.json','resources/minotaur_breaker_skinning_candidates.json']:
        assert (ROOT/path).read_bytes()==subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)
    for p in read(ROOT/'tools/minotaur_breaker_parts_manifest.json')['parts']:
        assert sha(ROOT/p['file'])==p['sha256']
        assert sha(ROOT/p['compiled_texture'])==p['compiled_sha256']
        assert sha(ROOT/'work/minotaur_breaker/candidates/native_parts'/Path(p['compiled_texture']).name)==p['compiled_sha256']
    candidate=ROOT/'work/minotaur_breaker/candidates/minotaur_breaker_candidate.tscn'
    target=ROOT/'scenes/units/odyssey/minotaur_breaker/minotaur_breaker_rig.tscn'
    text=candidate.read_text(encoding='utf-8').replace('res://work/minotaur_breaker/candidates/native_parts/','res://resources/minotaur_breaker_textures/').replace('name="MinotaurBreakerCandidate"','name="MinotaurBreaker"').replace('autoplay = false','autoplay = true')
    target.write_text(text,encoding='utf-8')
    shutil.copy2(ROOT/'resources/minotaur_breaker_animation_candidates.json',ROOT/'resources/minotaur_breaker_animations_v1.json')
    report={'status':'PROMOTED_PENDING_FORMAL_TEST','base_commit':BASE,'changed_clips':['skill_01'],'unchanged_clips':['idle','walk','attack_01','hit','death'],'unchanged_parts':21,'unchanged_rest_rig':True,'carry':'Small-motion carry with shoulder pin, user-selected option D','formal_scene_sha256':sha(target)}
    (R/'skill_v7d_promotion.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
if __name__=='__main__':main()
