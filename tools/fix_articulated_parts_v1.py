"""Repartition only eight joint parts using approved body pixels. No inpainting."""
from rg_common import *
from PIL import ImageFilter

JOINTS=[
 ('near_elbow','arm_near_upper','arm_near_fore',(332,671),84,(0,1)),
 ('far_elbow','arm_far_upper','arm_far_fore',(680,695),82,(.55,.835)),
 ('near_knee','leg_near_thigh','leg_near_shin',(389,1079),110,(-.25,.968)),
 ('far_knee','leg_far_thigh','leg_far_shin',(640,1083),112,(.1,.995))]
BASELINE='reports/articulated_fix_baseline_v1.json'

def baseline():
    if (ROOT/BASELINE).exists(): return read(BASELINE)
    m=read('tools/roman_guard_parts_manifest.json')
    files=[body_source(),config()['source']]
    for p in m['parts']: files += [p['candidate_file'],p['mask']]
    data={'manifest':m,'pivots':read('assets/units/odyssey/roman_guard/roman_guard_pivots.json'),'file_hashes':{p:sha(p) for p in files},'timestamp':now()}
    write(BASELINE,data); return data

def main():
    assert body_review_ok()
    b=baseline(); source=rgba(body_source()); pixels=np.array(source); alpha=pixels[:,:,3]
    assert sha(body_source())==b['file_hashes'][body_source()]
    m=read('tools/roman_guard_parts_manifest.json'); old={p['name']:p for p in b['manifest']['parts']}
    yy,xx=np.indices(alpha.shape); records=[]; panels=[]
    piv=read('assets/units/odyssey/roman_guard/roman_guard_pivots.json')
    for key,parent,child,point,diameter,direction in JOINTS:
        pm=np.array(mask(old[parent]['mask']))>0; cm=np.array(mask(old[child]['mask']))>0; union=pm|cm
        x,y=point; axis=np.array(direction,float); axis/=np.linalg.norm(axis)
        along=(xx-x)*axis[0]+(yy-y)*axis[1]
        across=(xx-x)*axis[1]-(yy-y)*axis[0]
        roi=(abs(along)<=diameter*.85)&(abs(across)<=diameter*.8)
        half=diameter*.16
        # Replace the entire local ownership region, not a disconnected overlap strip.
        npart=pm.copy(); cpart=cm.copy()
        npart[roi]=union[roi]&(along[roi]<=half)
        cpart[roi]=union[roi]&(along[roi]>=-half)
        # One owner for partially transparent outer pixels preserves the rest-pose matte.
        fractional=roi&(alpha<255)&(alpha>0)
        npart[fractional]=union[fractional]&(along[fractional]<0)
        cpart[fractional]=union[fractional]&(along[fractional]>=0)
        overlap=npart&cpart&(alpha>0)
        local=overlap&roi
        span=float(along[local].max()-along[local].min()+1)
        for name,mp in [(parent,npart),(child,cpart)]:
            path=f'work/masks/parts/{name}_jointfix_v1.png'; cp=f'work/candidates/parts/{name}_jointfix_v1.png'
            Image.fromarray(mp.astype(np.uint8)*255).save(ROOT/path)
            alpha_extract(source,mask(path)).save(ROOT/cp)
            p=next(p for p in m['parts'] if p['name']==name)
            p.update(mask=path,candidate_file=cp,mask_sha256=sha(path),candidate_sha256=sha(cp),candidate_source_sha256=sha(body_source()),candidate_mask_sha256=sha(path),status='CANDIDATE_REVIEW_REQUIRED',mask_status='JOINT_OVERLAP_REVIEW_REQUIRED',review_required=True)
        piv['joints'][key].update(position=list(point),diameter_hint_px=diameter,overlap_target_fraction=.32,overlap_hint_px=round(diameter*.32),axis=axis.tolist(),review_required=True)
        piv['parts'][child]['position']=list(point)
        next(p for p in m['parts'] if p['name']==child)['pivot_hint']['position']=list(point)
        cy,cx=np.where((pm!=npart)|(cm!=cpart))
        records.append({'joint':key,'parent':parent,'child':child,'pivot':list(point),'diameter_px':diameter,'overlap_pixel_area':int(local.sum()),'overlap_axis_span_px':span,'approximate_overlap_percent':span/diameter*100,'changed_mask_region':[int(cx.min()),int(cy.min()),int(cx.max()+1),int(cy.max()+1)],'source_pixels_only':True})
        pic=preview(source); arr=np.array(pic)
        for mp,color in [(npart,[255,70,80]),(cpart,[25,145,255])]:
            mi=Image.fromarray(mp.astype(np.uint8)*255)
            edge=(np.array(mi.filter(ImageFilter.MaxFilter(3)))>0)&~mp
            arr[edge]=color
        arr[overlap]=(arr[overlap]*.35+np.array([0,255,100])*.65).astype(np.uint8)
        pic=Image.fromarray(arr); d=ImageDraw.Draw(pic);d.ellipse((x-6,y-6,x+6,y+6),fill='yellow',outline='black',width=2);d.line((x-12,y,x+12,y),fill='black',width=2);d.line((x,y-12,x,y+12),fill='black',width=2)
        panels.append((f'{key} {point} / {span/diameter*100:.1f}%',pic.crop((x-150,y-150,x+150,y+150))))
    write('tools/roman_guard_parts_manifest.json',m)
    write('assets/units/odyssey/roman_guard/roman_guard_pivots.json',piv)
    write('reports/joint_overlap_metrics_v3.json',{'status':'REVIEW_REQUIRED','joints':records,'body_sha256':sha(body_source()),'only_eight_parts_changed':True,'timestamp':now()})
    sheet(panels,'reports/joint_pivot_review_v3.png',2,(380,320))
    for path,digest in b['file_hashes'].items(): assert sha(path)==digest, path+' original modified'

if __name__=='__main__': main()
