"""VISIBLE PIXELS FIRST extraction. No hidden geometry or content is synthesized."""
import argparse, shutil
from rg_common import *
def extract(name,promote=False):
    check_source(); manifest=read('tools/roman_guard_parts_manifest.json'); p=next(x for x in manifest['parts'] if x['name']==name)
    if p.get('production_method')=='FROZEN_SWORD_WITH_AI_GRIP_COMPLETION':
        if not promote: raise ValueError('Use recorded sword completion recipe; visible-only extraction would discard the grip')
        from sword_completion import validate_completion
        validate_completion(p,p['candidate_file'])
    if name not in EQUIPMENT and not body_review_ok():
        raise ValueError('STOP_ART_PIPELINE: rejected body cannot be split')
    if promote and not body_review_ok():
        raise ValueError('Formal promotion blocked until the complete body passes')
    source=rgba(p['source']); m=mask(p['mask'])
    if p.get('mask_sha256')!=sha(p['mask']): raise ValueError('Mask changed: update review provenance before extraction')
    output=alpha_extract(source,m)
    if not output.getchannel('A').getbbox(): raise ValueError('No real source pixels in mask')
    candidate=p['candidate_file']; target=ROOT/candidate
    if promote:
        if not review_ok('mask:'+name,p['mask']): raise ValueError('Mask requires its own hash-bound visual PASS')
        if not target.exists() or not review_ok('part:'+name,candidate): raise ValueError('Candidate requires hash-bound art PASS before promotion')
        if p.get('candidate_source_sha256')!=sha(p['source']) or p.get('candidate_mask_sha256')!=sha(p['mask']): raise ValueError('Candidate source/mask provenance is stale')
        if p.get('missing_hidden_regions'): raise ValueError('Hidden regions still unresolved: '+str(p['missing_hidden_regions']))
        dst=ROOT/p['file']
        if dst.exists() and sha(p['file'])!=sha(candidate): raise ValueError('Do not overwrite a different formal part')
        shutil.copy2(target,dst); p.update(status='ART_APPROVED',review_required=False,sha256=sha(p['file']))
    else:
        if target.exists(): raise ValueError('Candidate exists; archive/version before re-extraction')
        output.save(target); completed=False
        if name not in EQUIPMENT:
            changed=np.any(np.array(source)!=np.array(check_source()),axis=2)
            completed=bool(np.any(changed&(np.array(output)[:,:,3]>0)))
        p.update(status='CANDIDATE_REVIEW_REQUIRED',candidate_sha256=sha(candidate),candidate_source_sha256=sha(p['source']),candidate_mask_sha256=sha(p['mask']),review_required=True,ai_completed=completed)
    write('tools/roman_guard_parts_manifest.json',manifest)
    return p
def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('parts',nargs='+',choices=PARTS); p.add_argument('--promote',action='store_true'); a=p.parse_args()
    try:
        for name in a.parts:
            result=extract(name,a.promote); print(name+': '+result['status'])
        return 0
    except (ValueError,FileNotFoundError) as e: print(str(e)); return 2
if __name__=='__main__': raise SystemExit(main())
