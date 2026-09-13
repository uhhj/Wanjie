"""Import actual local part edits without replacing approved body or formal assets."""
import argparse, shutil
from pathlib import Path
import numpy as np
from PIL import Image
import cretan_archer_pipeline as p

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--job',required=True);parser.add_argument('--result',required=True);parser.add_argument('--tool-id',required=True)
    args=parser.parse_args();p.verify_frozen()
    if not p.valid_external_body():raise ValueError('APPROVED_BODY_CHANGED')
    jobs=p.load(p.REPORT+'parts_v1/local_completion_jobs.json')
    job=next((j for j in jobs if j['id']==args.job),None)
    if not job:raise ValueError('UNKNOWN_JOB')
    for field,digest in [('input_file','input_sha256'),('mask','mask_sha256'),('body_reference','body_reference_sha256')]:
        if p.sha(job[field])!=job[digest]:raise ValueError('STALE_JOB_'+field)
    result=p.safe_work_input(args.result);output=p.ROOT/job['output_file']
    if output.exists():raise ValueError('NEVER_OVERWRITE_EXISTING_RESULT')
    with Image.open(result) as im:
        if im.format!='PNG' or im.mode!='RGBA' or im.size!=(1024,1536):raise ValueError('REQUIRE_RGBA_SAME_CANVAS_PNG')
        b=np.array(im)
    a=np.array(Image.open(p.ROOT/job['input_file']));mask=np.array(Image.open(p.ROOT/job['mask']))>0
    outside=int(np.any(a[~mask]!=b[~mask],axis=1).sum())
    if outside:raise ValueError(f'OUTSIDE_PART_MASK_CHANGED: {outside}')
    if b[:,:,3].min()!=0 or b[:,:,3].max()!=255:raise ValueError('TRUE_ALPHA_AND_OPAQUE_PIXELS_REQUIRED')
    shutil.copy2(result,output)
    p.save(p.REPORT+'parts_v1/'+job['id']+'_import.json',{
        **job,'status':'IMPORTED_VISUAL_REVIEW_REQUIRED','actual_external_tool':args.tool_id,
        'output_sha256':p.sha(job['output_file']),'outside_mask_changed_pixels':outside,
        'import_timestamp':p.now(),'model_called_by_script':False,'formal_approval':False})
    print('Imported without altering frozen Body; visual/structural review required before promotion.')

if __name__=='__main__':
    try:main()
    except (ValueError,FileNotFoundError) as e:print(str(e));raise SystemExit(2)
