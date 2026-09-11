"""Hierarchical full-canvas joint previews, overlap diagnostics and art gate."""
import argparse, math, json
from collections import deque
from rg_common import *
from validate_parts import validate
from recompose_roman_guard import compose,render_config_digest
def transform(im,pivot,angle,translation=(0,0)):
    # Pillow uses positive counter-clockwise angles, with a fixed source-space pivot.
    # Zero rotation preserves bytes exactly; all descendants receive the same transform.
    if angle==0 and tuple(translation)==(0,0): return im.copy()
    return im.rotate(angle,Image.Resampling.BICUBIC,center=tuple(pivot),translate=tuple(translation),expand=False)
def enclosed_holes(a):
    h,w=a.shape; bg=~a; seen=np.zeros(a.shape,bool); q=deque()
    for y in range(h):
        for x in (0,w-1):
            if bg[y,x] and not seen[y,x]: seen[y,x]=True; q.append((x,y))
    for x in range(w):
        for y in (0,h-1):
            if bg[y,x] and not seen[y,x]: seen[y,x]=True; q.append((x,y))
    while q:
        x,y=q.popleft()
        for nx,ny in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
            if 0<=nx<w and 0<=ny<h and bg[ny,nx] and not seen[ny,nx]: seen[ny,nx]=True; q.append((nx,ny))
    return int((bg&~seen).sum())
def joint_diagnostic(fixed,rest,moving,pivot,diameter,axis=None,check_rest_overlap=False):
    x,y=pivot; r=diameter*.65
    yy,xx=np.indices(np.array(fixed).shape[:2]); disc=(xx-x)**2+(yy-y)**2<=r*r
    fa=np.array(fixed)[:,:,3]>32; ra=np.array(rest)[:,:,3]>32; ma=np.array(moving)[:,:,3]>32
    inter=int((fa&ma&disc).sum()); rest_union=fa|ra; current_union=fa|ma
    lost=int((rest_union&~current_union&disc).sum())
    expected=int((rest_union&disc).sum()); fraction=lost/max(1,expected)
    x0,y0=max(0,int(x-r)),max(0,int(y-r)); x1,y1=min(fixed.width,int(x+r+1)),min(fixed.height,int(y+r+1))
    hole_growth=enclosed_holes(current_union[y0:y1,x0:x1])-enclosed_holes(rest_union[y0:y1,x0:x1])
    # Coverage change can reflect legitimate silhouette movement, so visual review is mandatory.
    projection_fraction=None
    if axis is not None:
        py,px=np.where(fa&ma&disc); direction=np.array(axis,dtype=float); direction/=max(1e-9,float(np.linalg.norm(direction)))
        projected=px*direction[0]+py*direction[1]
        projection_fraction=float((projected.max()-projected.min()+1)/diameter) if len(projected) else 0.0
    passed=inter>=max(8,round(diameter*.2)) and fraction<=.2 and hole_growth<=12
    if check_rest_overlap: passed=passed and projection_fraction is not None and .20<=projection_fraction<=.30
    return {'automatic_status':'PASS' if passed else 'FAIL','overlap_pixels':inter,'overlap_axis_span_fraction_of_joint_diameter':projection_fraction,'rest_overlap_requirement_checked':check_rest_overlap,'local_coverage_loss_fraction':fraction,'enclosed_hole_growth_pixels':hole_growth,'note':'Heuristic only; open wedges and armor continuity require the contact-sheet visual review.'}
def main():
    argparse.ArgumentParser(description=__doc__).parse_args(); validation=validate()
    if validation['status']!='PASS':
        write('reports/joint_rotation_metrics.json',{'status':'NOT_RUN','reason':'Formal parts gate failed','elbows':'NOT_RUN','knees':'NOT_RUN','shield':'NOT_RUN','sword':'NOT_RUN','images_generated':False,'timestamp':now()}); print('NOT_RUN: formal parts gate failed'); return 2
    manifest=read('tools/roman_guard_parts_manifest.json'); images={p['name']:rgba(p['file']) for p in manifest['parts']}; pivots=read('assets/units/odyssey/roman_guard/roman_guard_pivots.json')
    items=[]; results=[]
    cases=[('near elbow','near_elbow','arm_near_upper','arm_near_fore',['arm_near_fore','hand_near','sword']),('far elbow','far_elbow','arm_far_upper','arm_far_fore',['arm_far_fore','hand_far','shield']),('near knee','near_knee','leg_near_thigh','leg_near_shin',['leg_near_shin','foot_near']),('far knee','far_knee','leg_far_thigh','leg_far_shin',['leg_far_shin','foot_far'])]
    for title,key,proximal,distal,descendants in cases:
        hint=pivots['joints'][key]; pivot=hint['position']
        for angle in [-20,0,20]:
            changed={**images}
            for part in descendants: changed[part]=transform(images[part],pivot,angle)
            parent_pivot=pivots['parts'][proximal]['position']; axis=[pivot[0]-parent_pivot[0],pivot[1]-parent_pivot[1]]
            diagnostic=joint_diagnostic(images[proximal],images[distal],changed[distal],pivot,hint['diameter_hint_px'],axis,angle==0)
            frame=compose(changed,manifest['draw_passes']); items.append((f'{title} {angle:+d} deg | '+diagnostic['automatic_status'],frame))
            results.append({'joint':key,'angle_deg':angle,'moved_parts':descendants,**diagnostic})
    for part,cases in [('shield',[(-7,(-8,0)),(0,(0,0)),(7,(8,-5))]),('sword',[(0,(0,0)),(20,(18,-5)),(30,(25,-7))])]:
        pivot=pivots['parts'][part]['position']
        for angle,translation in cases:
            changed={**images}; changed[part]=transform(images[part],pivot,angle,translation)
            items.append((f'{part} {angle:+d} deg / move {translation}',compose(changed,manifest['draw_passes'])))
            # Detect actual clipping by comparing a padded transformed image, not bbox alone.
            pad=max(config()['canvas']); large=Image.new('RGBA',(images[part].width+2*pad,images[part].height+2*pad)); large.paste(images[part],(pad,pad))
            moved=transform(large,(pivot[0]+pad,pivot[1]+pad),angle,translation); alpha=np.array(moved)[:,:,3].astype(float)
            cropped=alpha[pad:pad+images[part].height,pad:pad+images[part].width]
            clipped=float(alpha.sum()-cropped.sum())/max(1,float(alpha.sum()))
            results.append({'joint':part,'angle_deg':angle,'translation_px':translation,'moved_parts':[part],'clipped_alpha_fraction':clipped,'automatic_status':'PASS' if clipped<.001 else 'FAIL','note':'Independent socket motion shown; grip/armor overlap requires visual review.'})
    path='reports/joint_rotation_test.png'; sheet(items,path,3,(341,512))
    auto=all(r['automatic_status']=='PASS' for r in results); visual=review_ok('joint_rotation',path)
    write('reports/joint_rotation_metrics.json',{'status':'PASS' if auto and visual else 'REVIEW_REQUIRED' if auto else 'FAIL','automatic_checks_passed':auto,'visual_review_passed':visual,'output_sha256':sha(path),'part_hashes':{p['name']:sha(p['file']) for p in manifest['parts']},'render_config_sha256':render_config_digest(manifest),'pivot_config_sha256':sha('assets/units/odyssey/roman_guard/roman_guard_pivots.json'),'tests':results,'timestamp':now()})
    print('PASS' if auto and visual else 'REVIEW_REQUIRED' if auto else 'FAIL'); return 0 if auto and visual else 2
if __name__=='__main__': raise SystemExit(main())
