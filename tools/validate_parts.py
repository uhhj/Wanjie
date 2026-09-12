"""Gate formal parts by names, provenance, canvas, alpha, mask and art reviews."""
import argparse,json
from rg_common import *
from sword_completion import validate_completion
def validate():
    errors=[]; generated=[]; missing=[]; info=[]
    try: check_source()
    except (ValueError,FileNotFoundError) as e: errors.append(str(e))
    m=read('tools/roman_guard_parts_manifest.json')
    required=PARTS+(['knee_near'] if m.get('articulation_layout')=='NEAR_KNEE_V1' else [])
    if sorted(x['name'] for x in m['parts'])!=sorted(required): errors.append('Manifest must contain the core parts and explicitly configured knee attachment')
    if m.get('required_count')!=len(required):errors.append('Required part count mismatch')
    if m.get('canvas_width')!=config()['canvas'][0] or m.get('canvas_height')!=config()['canvas'][1]: errors.append('Manifest canvas mismatch')
    if not body_review_ok(): errors.append('Complete body art review FAIL or missing/stale')
    for p in m['parts']:
        name=p['name']; entry={'name':name,'file':p['file']}
        if not (ROOT/p['file']).is_file(): missing.append(name); entry['status']='MISSING'; info.append(entry); continue
        generated.append(name)
        try:
            im=rgba(p['file']); a=np.array(im)[:,:,3]
            if not a.any() or a.min()!=0: raise ValueError('Part must contain real pixels AND fully transparent background')
            if p.get('sha256')!=sha(p['file']): raise ValueError('Formal part hash absent or stale')
            if p.get('status')!='ART_APPROVED' or p.get('review_required') is not False: raise ValueError('Part art approval missing')
            if not review_ok('part:'+name,p['file']): raise ValueError('Per-part review hash absent or stale')
            if not review_ok('mask:'+name,p['mask']): raise ValueError('Per-mask review hash absent or stale')
            if p.get('candidate_source_sha256')!=sha(p['source']): raise ValueError('Source lineage stale')
            if p.get('mask_sha256')!=sha(p['mask']) or p.get('candidate_mask_sha256')!=sha(p['mask']): raise ValueError('Mask lineage stale')
            if p.get('missing_hidden_regions'): raise ValueError('Hidden-region completion unresolved')
            expected=config()['source'] if name in EQUIPMENT else body_source()
            if p['source']!=expected: raise ValueError('Unauthorized part source')
            if p.get('production_method')=='FROZEN_SWORD_WITH_AI_GRIP_COMPLETION':
                validate_completion(p,p['file'])
            elif not np.array_equal(np.array(im),np.array(alpha_extract(rgba(p['source']),mask(p['mask'])))):
                raise ValueError('Formal part contains pixels outside approved source/mask extraction')
            pivot=p.get('pivot_hint',{}).get('position')
            if not pivot or not(0<=pivot[0]<im.width and 0<=pivot[1]<im.height): raise ValueError('Pivot missing/outside canvas')
            entry.update(status='PASS',bbox=list(im.getchannel('A').getbbox()),sha256=sha(p['file']))
        except (ValueError,FileNotFoundError) as e: entry.update(status='FAIL',reason=str(e)); errors.append(name+': '+str(e))
        info.append(entry)
    if missing: errors.append('Missing formal parts: '+', '.join(missing))
    return {'status':'PASS' if not errors else 'FAIL','required_count':len(required),'generated_formal_count':len(generated),'missing_count':len(missing),'missing':missing,'errors':errors,'parts':info,'timestamp':now()}
def main():
    argparse.ArgumentParser(description=__doc__).parse_args(); r=validate(); write('reports/parts_validation.json',r); print(json.dumps(r,indent=2)); return 0 if r['status']=='PASS' else 2
if __name__=='__main__': raise SystemExit(main())
