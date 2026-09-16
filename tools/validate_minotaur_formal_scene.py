"""Verify that promotion changed only paths/name/autoplay, not approved motion or art."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 r=ROOT/'reports/minotaur_breaker';errors=[]
 candidate=ROOT/'work/minotaur_breaker/candidates/minotaur_breaker_candidate.tscn'
 formal=ROOT/'scenes/units/odyssey/minotaur_breaker/minotaur_breaker_rig.tscn'
 expected=candidate.read_text().replace('res://work/minotaur_breaker/candidates/native_parts/','res://resources/minotaur_breaker_textures/').replace('name="MinotaurBreakerCandidate"','name="MinotaurBreaker"').replace('autoplay = false','autoplay = true')
 if expected!=formal.read_text():errors.append('Scene differs beyond reviewed promotion substitutions')
 parts=json.loads((ROOT/'tools/minotaur_breaker_parts_manifest.json').read_text())['parts']
 for part in parts:
  if sha(ROOT/part['file'])!=part['sha256']:errors.append('PNG changed: '+part['name'])
  if sha(ROOT/part['compiled_texture'])!=part['compiled_sha256']:errors.append('Compiled texture changed: '+part['name'])
 for source,target in [('animation_candidates','animations_v1'),('skinning_candidates','skinning_v1')]:
  if sha(ROOT/f'resources/minotaur_breaker_{source}.json')!=sha(ROOT/f'resources/minotaur_breaker_{target}.json'):errors.append('Promoted data differs: '+target)
 report={'status':'PASS' if not errors else 'FAIL','formal_scene_sha256':sha(formal),'candidate_scene_sha256':sha(candidate),'scene_semantic_parity':not errors,'parts_checked':len(parts),'errors':errors}
 (r/'formal_scene_parity.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
 if errors:raise SystemExit(1)
if __name__=='__main__':main()
