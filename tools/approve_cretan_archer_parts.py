"""Promote only a complete, hash-bound, visually reviewed twenty-part set."""
import argparse,json,shutil
import numpy as np
from PIL import Image
import cretan_archer_pipeline as p
import build_cretan_archer_parts as b
from review_cretan_archer_repaired_parts import ORDER,OUT,REPORT

def main(review_file):
    p.verify_frozen();assert p.valid_external_body()
    review=p.load(review_file);metrics=p.load(REPORT+'metrics.json')
    assert review['approved_body_sha256']==p.sha(p.BODY)
    assert review['status']=='PASS' and all(review['checks'].values()) and review['notes']
    candidates={r['name']:r for r in metrics['parts']}
    assert set(candidates)==set(p.PARTS)==set(review['part_sha256'])
    body_repairs={r['part']:r for r in p.load(p.REPORT+'self_repair/body/repair_jobs.json')}
    manifest=p.load('tools/cretan_archer_parts_manifest.json')
    pivot={n:xy for n,xy in b.PIVOTS.items()};pivot.update(bow_string=[844,725],arrow_single=[282,725])
    validations=[]
    for entry in manifest['parts']:
        n=entry['name'];source=candidates[n]['file'];digest=p.sha(source)
        assert digest==candidates[n]['sha256']==review['part_sha256'][n],f'STALE_PART_REVIEW: {n}'
        with Image.open(p.ROOT/source) as im:
            a=np.array(im);assert im.format=='PNG' and im.mode=='RGBA' and im.size==(1024,1536)
            alpha=a[:,:,3];bbox=im.getchannel('A').getbbox()
            assert alpha.min()==0 and alpha.max()>=240 and (alpha==0).sum()>100 and (alpha>128).sum()>100
            assert bbox and bbox[0]>0 and bbox[1]>0 and bbox[2]<1024 and bbox[3]<1536
            if n in b.POLYGONS:
                base=np.array(Image.open(p.ROOT/p.WORK/'self_repair/ownership'/(n+'.png')))
                visible=base[:,:,3]>0;assert np.array_equal(a[visible],base[visible]),f'SOURCE_PIXELS_CHANGED: {n}'
            mask_file=p.WORK+'masks/approved_parts/'+n+'.png'
            (p.ROOT/mask_file).parent.mkdir(parents=True,exist_ok=True);im.getchannel('A').save(p.ROOT/mask_file)
        dst=p.ROOT/entry['file'];dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p.ROOT/source,dst)
        ai=n in body_repairs or n in ['bow','quiver','cloak','arrow_single']
        for obsolete in ['candidate_sha256','source_origin']:entry.pop(obsolete,None)
        entry.update(status='PASS',candidate_file=source,sha256=digest,ai_completed=ai,review_required=False,
          hidden_completion=ai and n!='arrow_single',pivot_hint=pivot[n],mask=mask_file,mask_sha256=p.sha(mask_file),
          rest_visible=n!='arrow_single',visual_review=review_file,
          source_origin=('Approved Body visible pixels + scoped generated hidden material' if n in body_repairs else
              'Approved Body source pixel extraction' if n in b.POLYGONS else
              'Deterministic controllable string geometry using source-observed attachment points' if n=='bow_string' else
              'Generated isolated full arrow matching frozen equipment reference' if n=='arrow_single' else
              'Frozen Rig Master visible pixels + scoped generated hidden equipment completion'))
        if n in body_repairs:entry['repair_record']=p.REPORT+'self_repair/body/repair_jobs.json'
        validations.append({'name':n,'sha256':digest,'rgba_same_canvas':True,'transparent_pixels':int((alpha==0).sum()),'foreground_pixels':int((alpha>128).sum()),'bbox':bbox})
    manifest.update(status='PASS',draw_order=ORDER,approved_review=review_file,part_count=20)
    p.save('tools/cretan_archer_parts_manifest.json',manifest)
    p.save('assets/units/odyssey/cretan_archer/cretan_archer_pivots.json',{'canvas':[1024,1536],'coordinate_space':'source_canvas_pixels','pivots':pivot,
       'bow_string_attachment_points':[[790,150],[719,1240]],'bow_grip':[844,725],'arrow_nock':[282,725],'arrow_tip':[958,725],
       'rest_ground_origin':[524,1460],'note':'Source anchors reviewed in combat-scale part tests; unit bone offsets are stored separately for native animation.'})
    p.save(p.REPORT+'parts_gate.json',{'status':'PASS','required':20,'approved':20,'missing':0,'review':review_file,'parts':validations})
    state=p.load(p.REPORT+'pipeline_status.json');state.update(verdict='PART_REPAIR_PASS_NATIVE_VALIDATION_PENDING',
        parts={'required':20,'generated':20,'approved':20,'missing':0,'status':'PASS'},
        recomposition='PASS_COMBAT_SCALE',joint_tests='PASS_LOCAL_ARTICULATION_256_192',godot_handoff='READY',
        note='Twenty repaired assets passed combat-scale review. Native scenes/animation/event/stress require their separate tests; not yet declared supported.')
    p.save(p.REPORT+'pipeline_status.json',state);p.verify_frozen()
    print('PASS: 20 genuine RGBA same-canvas parts promoted with current review hashes')
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--review-file',required=True);args=parser.parse_args();main(args.review_file)
