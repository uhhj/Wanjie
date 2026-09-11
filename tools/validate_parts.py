"""Gate formal parts by names, provenance, canvas, alpha, mask and art reviews."""
import argparse,json
from rg_common import *
def validate():
    errors=[]; generated=[]; missing=[]; info=[]
    try: check_source()
    except (ValueError,FileNotFoundError) as e: errors.append(str(e))
    m=read('tools/roman_guard_parts_manifest.json')
    if sorted(x['name'] for x in m['parts'])!=sorted(PARTS): errors.append('Manifest must contain exactly the 19 distinct required parts')
    if m.get('canvas_width')!=config()['canvas'][0] or m.get('canvas_height')!=config()['canvas'][1]: errors.append('Manifest canvas mismatch')
    if not review_ok('complete_body','work/03_complete_body_base.png'): errors.append('Complete body art review FAIL or missing/stale')
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
            expected=config()['source'] if name in EQUIPMENT else 'work/03_complete_body_base.png'
            if p['source']!=expected: raise ValueError('Unauthorized part source')
            pivot=p.get('pivot_hint',{}).get('position')
            if not pivot or not(0<=pivot[0]<im.width and 0<=pivot[1]<im.height): raise ValueError('Pivot missing/outside canvas')
            entry.update(status='PASS',bbox=list(im.getchannel('A').getbbox()),sha256=sha(p['file']))
        except (ValueError,FileNotFoundError) as e: entry.update(status='FAIL',reason=str(e)); errors.append(name+': '+str(e))
        info.append(entry)
    if missing: errors.append('Missing formal parts: '+', '.join(missing))
    return {'status':'PASS' if not errors else 'FAIL','required_count':19,'generated_formal_count':len(generated),'missing_count':len(missing),'missing':missing,'errors':errors,'parts':info,'timestamp':now()}
def main():
    argparse.ArgumentParser(description=__doc__).parse_args(); r=validate(); write('reports/parts_validation.json',r); print(json.dumps(r,indent=2)); return 0 if r['status']=='PASS' else 2
if __name__=='__main__': raise SystemExit(main())
