"""Promote only reviewed V2 animation data; reject changed art or other clips."""
from pathlib import Path
import hashlib, json, shutil, subprocess

ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'reports/minotaur_breaker'
BASE='6cffbe2673e1bcbeae61dfd9e275a2adf43be989'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
    capture=read(R/'actions_v2_capture_manifest.json')
    review=read(R/'actions_v2_visual_review.json')
    assert review['status']=='PASS' and review['artifact_inputs']==capture['artifact_inputs']
    assert capture['inputs_unchanged_during_capture']
    assert len(capture['frames'])==128
    assert len({(f['animation'],f['height'],f['frame']) for f in capture['frames']})==128
    for path,digest in capture['artifact_inputs'].items(): assert sha(ROOT/path.removeprefix('res://'))==digest,path
    for frame in capture['frames']: assert sha(ROOT/frame['path'].removeprefix('res://'))==frame['sha256']
    assert read(R/'actions_v2_test.json')['status']=='PASS'
    assert read(R/'candidate_ik_reach.json')['status']=='PASS'
    assert read(R/'candidate_format_validation.json')['status']=='PASS'
    old=json.loads(subprocess.check_output(['git','show',BASE+':resources/minotaur_breaker_animations_v1.json'],cwd=ROOT))
    new=read(ROOT/'resources/minotaur_breaker_animation_candidates.json')
    for name in ['idle','walk','hit','death']: assert old[name]==new[name],name
    protected=['resources/minotaur_breaker_rig_v1.json','resources/minotaur_breaker_skinning_candidates.json']
    for path in protected:
        assert (ROOT/path).read_bytes()==subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT),path
    parts=read(ROOT/'tools/minotaur_breaker_parts_manifest.json')['parts']
    for part in parts:
        assert sha(ROOT/part['file'])==part['sha256']
        assert sha(ROOT/part['compiled_texture'])==part['compiled_sha256']
        assert sha(ROOT/'work/minotaur_breaker/candidates/native_parts'/Path(part['compiled_texture']).name)==part['compiled_sha256']
    candidate=ROOT/'work/minotaur_breaker/candidates/minotaur_breaker_candidate.tscn'
    formal=ROOT/'scenes/units/odyssey/minotaur_breaker/minotaur_breaker_rig.tscn'
    text=candidate.read_text(encoding='utf-8').replace('res://work/minotaur_breaker/candidates/native_parts/','res://resources/minotaur_breaker_textures/').replace('name="MinotaurBreakerCandidate"','name="MinotaurBreaker"').replace('autoplay = false','autoplay = true')
    formal.write_text(text,encoding='utf-8')
    shutil.copy2(ROOT/'resources/minotaur_breaker_animation_candidates.json',ROOT/'resources/minotaur_breaker_animations_v1.json')
    write(R/'actions_v2_promotion.json',{'status':'PROMOTED_PENDING_FORMAL_TEST','base_commit':BASE,'candidate_scene_sha256':sha(candidate),'formal_scene_sha256':sha(formal),'unchanged_clips':['idle','walk','hit','death'],'unchanged_parts':len(parts),'unchanged_rest_rig':True,'changed_clips':['attack_01','skill_01']})
    print('V2 actions promoted; 21 textures, rest rig, weights and other four clips unchanged.')
if __name__=='__main__': main()
