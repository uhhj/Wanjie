"""Composite formal parts in explicit draw passes and measure against frozen source."""
import argparse,json
from PIL import ImageFilter
from rg_common import *
from validate_parts import validate
def render_config_digest(manifest):
    payload={'passes':manifest['draw_passes'],'clip_masks':{d['clip_mask']:sha(d['clip_mask']) for d in manifest['draw_passes'] if d.get('clip_mask')}}
    return hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
def compose(images,passes):
    out=Image.new('RGBA',tuple(config()['canvas']))
    for draw in passes:
        im=images[draw['part']]
        if draw.get('clip_mask'): im=alpha_extract(im,mask(draw['clip_mask']))
        out=Image.alpha_composite(out,im)
    return out
def comparison(source,result):
    s=np.array(source).astype(float); r=np.array(result).astype(float); sa=s[:,:,3]>32; ra=r[:,:,3]>32
    union=sa|ra; inter=sa&ra
    premul_s=s[:,:,:3]*s[:,:,3:4]/255; premul_r=r[:,:,:3]*r[:,:,3:4]/255
    difference=np.abs(premul_s-premul_r)
    sb=source.getchannel('A').point(lambda x:255 if x>32 else 0).getbbox(); rb=result.getchannel('A').point(lambda x:255 if x>32 else 0).getbbox()
    def centroid(a):
        ys,xs=np.where(a); return np.array([xs.mean(),ys.mean()]) if len(xs) else np.array([float('inf')]*2)
    silhouettes=float(inter.sum()/max(1,union.sum())); centroid_delta=float(np.linalg.norm(centroid(sa)-centroid(ra)))
    bbox_delta=max(abs(x-y) for x,y in zip(sb,rb)) if sb and rb else float('inf')
    boundary=np.array(Image.fromarray(ra.astype(np.uint8)*255).filter(ImageFilter.MaxFilter(7)))>0
    source_boundary=sa & ~ (np.array(Image.fromarray(sa.astype(np.uint8)*255).filter(ImageFilter.MinFilter(3)))>0)
    outline_recall=float((source_boundary&boundary).sum()/max(1,source_boundary.sum()))
    allowed=np.zeros(sa.shape,bool)
    for stage in config()['stages']: allowed |= np.array(mask(stage['mask']))>0
    stable=union & ~allowed
    stable_mae=float(difference[stable].mean()) if stable.any() else None
    metrics={'silhouette_iou':silhouettes,'source_bbox':sb,'result_bbox':rb,'max_bbox_deviation_px':bbox_delta,'centroid_deviation_px':centroid_delta,'source_outline_within_3px_fraction':outline_recall,'premultiplied_rgb_mae_union':float(difference[union].mean()) if union.any() else None,'protected_visible_rgb_mae':stable_mae,'changed_alpha_pixels':int((sa!=ra).sum()),'note':'No registration/resizing. AI regions still count in silhouette and total error; only protected-region diagnostic excludes them.'}
    thresholds={'silhouette_iou_min':0.985,'bbox_deviation_px_max':8,'centroid_deviation_px_max':5,'outline_recall_min':0.99,'protected_rgb_mae_max':12}
    passed=silhouettes>=.985 and bbox_delta<=8 and centroid_delta<=5 and outline_recall>=.99 and stable_mae is not None and stable_mae<=12
    heat=np.clip(difference*4,0,255).astype(np.uint8); heat[sa&~ra]=[255,40,150]; heat[ra&~sa]=[20,210,255]
    return metrics,thresholds,passed,Image.fromarray(heat)
def main():
    if config().get('asset_gate_policy')=='COMBAT_RIG_V3':
        from combat_rig_gate import audit
        report=audit('recomposition');write('reports/recomposition_metrics.json',report)
        print(report['status']);return 0 if report['status']=='PASS' else 2
    argparse.ArgumentParser(description=__doc__).parse_args(); v=validate()
    if v['status']!='PASS':
        write('reports/recomposition_metrics.json',{'status':'NOT_RUN','reason':'Formal parts gate failed','parts_validation':v,'images_generated':False,'godot_handoff':'NOT_READY','timestamp':now()}); print('NOT_RUN: formal parts gate failed'); return 2
    m=read('tools/roman_guard_parts_manifest.json'); images={p['name']:rgba(p['file']) for p in m['parts']}
    passes=m['draw_passes']
    if set(d['part'] for d in passes)!=set(PARTS): raise ValueError('Draw passes must include all 19 required parts')
    result=compose(images,passes); path='reports/roman_guard_recomposed.png'; result.save(ROOT/path)
    metrics,thresholds,passed,heat=comparison(check_source(),result); heat.save(ROOT/'reports/recomposition_diff.png')
    approved=review_ok('recomposition',path)
    write('reports/recomposition_metrics.json',{'status':'PASS' if passed and approved else 'REVIEW_REQUIRED' if passed else 'FAIL','automatic_checks_passed':passed,'visual_review_passed':approved,'metrics':metrics,'thresholds':thresholds,'output_sha256':sha(path),'part_hashes':{p['name']:sha(p['file']) for p in m['parts']},'render_config_sha256':render_config_digest(m),'timestamp':now()})
    print('PASS' if passed and approved else 'REVIEW_REQUIRED' if passed else 'FAIL'); return 0 if passed and approved else 2
if __name__=='__main__': raise SystemExit(main())
