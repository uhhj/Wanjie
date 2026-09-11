"""Manage REAL reference-guided tool jobs. This is NOT a fake image API client.
The image_gen.imagegen tool is available in Codex, not as a local Python callable.
prepare prints the inputs for that tool. import-result validates and composites
its real output with a hard protected region. RGB outputs need an explicit matte.
"""
import argparse,shutil,json
from rg_common import *
def stage_for(name):
    for s in config()['stages']:
        if s['id']==name: return s
    raise ValueError('Unknown stage')
def prepare(s):
    check_source(); rgba(s['input']); mask(s['mask'])
    previous=config()['stages'].index(s)
    if previous:
        prev=config()['stages'][previous-1]
        r=read('reports/art_reviews.json').get(prev['id'],{}) if (ROOT/'reports/art_reviews.json').exists() else {}
        intermediate=(r.get('status')=='REVIEWED_INTERMEDIATE_WITH_ISSUES' and r.get('sha256')==sha(prev['output']) and bool(r.get('notes')))
        if not review_ok(prev['id'],prev['output']) and not intermediate: raise ValueError('Previous AI stage requires a hash-bound review. Only PASS can unlock formal body extraction.')
    j=read('reports/ai_jobs/'+s['id']+'.json')
    j.update(input_sha256=sha(s['input']),mask_sha256=sha(s['mask']),prompt_text=(ROOT/s['prompt']).read_text(encoding='utf-8'),status='READY_FOR_REAL_TOOL_CALL',timestamp=now())
    write('reports/ai_jobs/'+s['id']+'.json',j)
    return j
def archive_outputs(s):
    check_source(); start=config()['stages'].index(s); archived=[]
    for current in config()['stages'][start:]:
        p=(ROOT/current['output']).resolve()
        if not p.is_relative_to(ROOT.resolve()) or p==(ROOT/config()['source']).resolve(): raise ValueError('Refusing archive outside project / source')
        if not p.exists(): continue
        stamp=sha(current['output'])[:16]; folder=ROOT/'reports/ai_jobs/archive'/current['id']/stamp; folder.mkdir(parents=True,exist_ok=True)
        for record in [f"reports/ai_jobs/{current['id']}.json",f"reports/ai_jobs/{current['id'][:3]}_tool_invocation.json",'reports/art_reviews.json',current['mask'],current['prompt']]:
            if (ROOT/record).exists(): shutil.copy2(ROOT/record,folder/Path(record).name)
        target=ROOT/'work/archive'/current['id']/(stamp+'.png'); target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists(): raise ValueError('Archive already exists; inspect it before changing current stage')
        shutil.move(str(p),str(target)); archived.append(str(target.relative_to(ROOT)))
    return {'archived':archived,'note':'Downstream reviews no longer match available outputs; rerun stages sequentially.'}
def import_result(s,path,matte=None,matte_review_note=None,tool_identifier=None):
    j=prepare(s)
    with Image.open(path) as opened: raw=opened.copy()
    if list(raw.size)!=config()['canvas']: raise ValueError('Result canvas mismatch. Do not stretch or auto-register it.')
    if (ROOT/s['output']).exists(): raise ValueError('Stage output already exists; archive/version it before reimporting')
    if matte:
        if not matte_review_note: raise ValueError('A traced matte needs a review note, not silent background conversion')
        m=mask(matte); edited=raw.convert('RGBA'); edited.putalpha(m)
        j.update(matte=matte,matte_sha256=sha(matte),matte_review_note=matte_review_note)
    else:
        if raw.mode!='RGBA' or raw.getchannel('A').getextrema()[0]!=0:
            raise ValueError('RAW_OUTPUT_NOT_TRANSPARENT: RGB/opaque output needs an independently reviewed matte')
        edited=raw.copy()
    src=rgba(s['input']); allowed=np.array(mask(s['mask']))>0
    out=np.array(src); edit=np.array(edited)
    out[allowed]=edit[allowed]; out[allowed & (out[:,:,3]==0),:3]=0
    result=Image.fromarray(out); result.save(ROOT/s['output'])
    raw_rel='work/raw/'+s['id']+'.png'
    incoming_hash=hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if (ROOT/raw_rel).exists() and sha(raw_rel)!=incoming_hash: raw_rel='work/raw/'+s['id']+'_'+incoming_hash[:16]+'.png'
    if Path(path).resolve()!=(ROOT/raw_rel).resolve(): shutil.copy2(path,ROOT/raw_rel)
    src_a=np.array(src); raw_a=np.array(raw.convert('RGBA'))
    protected_changes=int(np.any(src_a[~allowed]!=out[~allowed],axis=1).sum())
    assert protected_changes==0
    j.update(status='IMPORTED_REVIEW_REQUIRED',raw_output=raw_rel,raw_output_sha256=sha(raw_rel),raw_mode=raw.mode,output_sha256=sha(s['output']),protected_changed_pixels=protected_changes,raw_protected_rgb_mean_absolute_error=float(np.abs(src_a[~allowed,:3].astype(float)-raw_a[~allowed,:3]).mean()),timestamp=now())
    if tool_identifier:
        j.update(model_tool_identifier=tool_identifier,execution_mode='EXTERNAL_RESULT_IMPORT',actual_tool_invocation=None,actual_tool_prompt=j['prompt_text'],call_executed_by_this_script=False)
    write('reports/ai_jobs/'+s['id']+'.json',j)
    write('reports/ai_jobs/history/'+s['id']+'_'+j['output_sha256'][:16]+'.json',j)
    sheet([('Input',src),('Constrained result - REVIEW',result)],'reports/'+s['id']+'_review.png')
    return j
def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('action',choices=['prepare','import-result','archive']); p.add_argument('stage'); p.add_argument('--result'); p.add_argument('--matte'); p.add_argument('--matte-review-note'); p.add_argument('--tool-identifier'); a=p.parse_args()
    try:
        s=stage_for(a.stage)
        if a.action=='import-result' and not a.result: raise ValueError('--result is required')
        result=prepare(s) if a.action=='prepare' else archive_outputs(s) if a.action=='archive' else import_result(s,a.result,a.matte,a.matte_review_note,a.tool_identifier)
        print(json.dumps(result,ensure_ascii=False,indent=2)); return 0
    except (ValueError,FileNotFoundError) as e: print(str(e)); return 2
if __name__=='__main__': raise SystemExit(main())
