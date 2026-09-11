import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from rg_common import *

source=check_source(); src=np.array(source); allowed=np.zeros(src.shape[:2],bool); rows=[]; mask_items=[]
for stage in config()['stages']:
    inp=rgba(stage['input']); out=rgba(stage['output']); a=np.array(mask(stage['mask']))>0; allowed|=a
    before=np.array(inp); after=np.array(out)
    rows.append({'id':stage['id'],'input_sha256':sha(stage['input']),'output_sha256':sha(stage['output']),'output_mode':out.mode,'output_canvas':list(out.size),'allowed_mask_pixels':int(a.sum()),'changed_protected_pixels':int(np.any(before[~a]!=after[~a],axis=1).sum()),'changed_editable_pixels':int(np.any(before[a]!=after[a],axis=1).sum())})
    overlay=Image.new('RGBA',inp.size,(0,140,255)); overlay.putalpha(mask(stage['mask']).point(lambda x:round(x*.42)))
    mask_items.append((stage['id']+' | final composite mask',Image.alpha_composite(inp,overlay)))
sheet(mask_items,'reports/occlusion_mask_review.png',3,(341,512))
body=np.array(rgba('work/03_complete_body_base.png'))
identity={'helmet_crest_roi':[350,0,700,338],'visible_face_roi':[570,265,636,360]}
identity_result={}
for name,(x0,y0,x1,y1) in identity.items(): identity_result[name]={'rect':identity[name],'changed_rgba_pixels':int(np.any(src[y0:y1,x0:x1]!=body[y0:y1,x0:x1],axis=2).sum())}
write('reports/complete_body_integrity.json',{'source_sha256':sha(config()['source']),'candidate_sha256':sha('work/03_complete_body_base.png'),'stages':rows,'unchanged_region_changed_rgba_pixels':int(np.any(src[~allowed]!=body[~allowed],axis=1).sum()),'identity_roi_checks':identity_result,'numerical_integrity_status':'PASS' if all(r['changed_protected_pixels']==0 for r in rows) else 'FAIL','complete_body_art_status':'FAIL','note':'Pixel protection does not establish plausible hidden anatomy or approve new collar design. All local visual defects are retained in art review.','timestamp':now()})
m=read('tools/roman_guard_parts_manifest.json'); audits=[]
for p in m['parts']:
    if not (ROOT/p['candidate_file']).exists(): continue
    im=rgba(p['candidate_file']); arr=np.array(im); positive=arr[:,:,3]>0
    audits.append({'part':p['name'],'file':p['candidate_file'],'sha256':sha(p['candidate_file']),'source':p['source'],'source_sha256':sha(p['source']),'canvas':list(im.size),'mode':im.mode,'alpha_extrema':list(im.getchannel('A').getextrema()),'nontransparent_pixels':int(positive.sum()),'source_rgb_identical_on_visible_pixels':bool(np.array_equal(arr[positive,:3],np.array(rgba(p['source']))[positive,:3])),'formal':False,'review_required':True})
write('reports/candidate_export_audit.json',{'required_core_parts':19,'candidate_count':len(audits),'formal_count':0,'candidates':audits,'timestamp':now()})
for folder in ['assets/units/odyssey/roman_guard/parts','work/masks/parts','work/imports']:
    (ROOT/folder).mkdir(parents=True,exist_ok=True); (ROOT/folder/'.gitkeep').touch()
# Preserve a complete immutable snapshot of this run's job metadata.
for s in config()['stages']:
    j=read('reports/ai_jobs/'+s['id']+'.json'); write('reports/ai_jobs/history/'+s['id']+'_'+j['output_sha256'][:16]+'.json',j)
print(json.dumps({'protected_changes':rows,'identity':identity_result,'equipment_candidates':len(audits)},indent=2))
