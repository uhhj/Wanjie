"""Cretan Archer resumable art gates. No image-model calls or placeholder parts.

Sources and Roman Guard are immutable. Import external local edits sequentially;
only an explicit, hash-bound visual review can unlock each subsequent stage.
"""
import argparse, hashlib, json, shutil
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
SOURCE='art_source/odyssey/cretan_archer/'
WORK='work/cretan_archer/'
REPORT='reports/cretan_archer/'
MASTER=SOURCE+'OD_UNIT_02_CRETAN_ARCHER_RIG_MASTER_V1.png'
BODY=WORK+'04_complete_body_rgba.png'
PARTS=['head','torso','pelvis','arm_near_upper','arm_near_fore','hand_near','arm_far_upper','arm_far_fore','hand_far','leg_near_thigh','leg_near_shin','foot_near','leg_far_thigh','leg_far_shin','foot_far','bow','bow_string','quiver','cloak','arrow_single']
STAGES=[('001_remove_bow',MASTER,WORK+'01_no_bow.png'),('002_remove_quiver',WORK+'01_no_bow.png',WORK+'02_no_bow_no_quiver.png'),('003_remove_cloak',WORK+'02_no_bow_no_quiver.png',WORK+'03_complete_body_base.png')]
CHECKS=['no_bow','no_quiver','no_cloak','both_hands_complete','both_legs_complete','garment_continuity','neck_shoulders_consistent','no_unapproved_helmet_or_armor','identity_consistent','no_visible_combat_scale_halo','no_internal_alpha_holes','ground_shadow_excluded']

def load(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def save(p,obj):
    path=ROOT/p;path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def font(size):return ImageFont.truetype('C:/Windows/Fonts/arial.ttf',size)
def safe_work_input(value):
    p=Path(value).resolve()
    if not p.is_relative_to(Path('D:/Wanjie').resolve()):raise ValueError('Imported assets must reside under D:/Wanjie')
    return p
def verify_frozen():
    manifest=load(SOURCE+'source_manifest.json')
    for entry in manifest['files']:
        if sha(entry['file'])!=entry['sha256']:raise ValueError('FROZEN_SOURCE_CHANGED: '+entry['file'])
    for path,digest in load(REPORT+'roman_guard_freeze_baseline.json')['files'].items():
        if sha(path)!=digest:raise ValueError('ROMAN_GUARD_CHANGED: '+path)
    return Image.open(ROOT/MASTER).size
def composite(im,kind):
    if kind=='checker':
        yy,xx=np.indices((im.height,im.width));v=np.where((xx//24+yy//24)%2,205,240).astype('uint8')
        bg=Image.fromarray(np.stack([v,v,v,np.full_like(v,255)],2))
    else:bg=Image.new('RGBA',im.size,kind)
    bg.alpha_composite(im.convert('RGBA'));return bg.convert('RGB')
def stage_record(i):
    name,input_file,output=STAGES[i]
    return {'id':name,'input_file':input_file,'input_sha256':sha(input_file) if (ROOT/input_file).exists() else None,'mask':WORK+'masks/'+name+'.png','mask_sha256':sha(WORK+'masks/'+name+'.png'),'prompt':WORK+'prompts/'+name+'.txt','prompt_text':(ROOT/WORK/'prompts'/f'{name}.txt').read_text(encoding='utf-8'),'output_file':output,'output_sha256':sha(output) if (ROOT/output).exists() else None,'status':'EXTERNAL_LOCAL_INPAINT_REQUIRED','model_tool_identifier':None,'model_call_executed':False,'timestamp':now()}
def stage_signature(i):
    name,input_file,output=STAGES[i]
    return {'input_sha256':sha(input_file),'output_sha256':sha(output),
            'mask_sha256':sha(WORK+'masks/'+name+'.png'),
            'prompt_sha256':sha(WORK+'prompts/'+name+'.txt')}

def valid_import(i):
    name,input_file,output=STAGES[i];p=REPORT+'ai_jobs/'+name+'.json'
    if not all((ROOT/f).exists() for f in [p,input_file,output]):return False
    job=load(p)
    return job.get('status')=='IMPORTED_VISUAL_REVIEW_REQUIRED' and all(job.get(k)==v for k,v in stage_signature(i).items())

def valid_review(i):
    name,_,_=STAGES[i];p=REPORT+'ai_jobs/'+name+'_review.json'
    if not valid_import(i) or not (ROOT/p).exists():return False
    review=load(p)
    return review.get('status')=='PASS' and all(review.get(k)==v for k,v in stage_signature(i).items()) and (i==0 or valid_review(i-1))

def valid_matte():
    p=REPORT+'matte_import.json'
    if not (ROOT/p).exists() or not (ROOT/BODY).exists():return False
    job=load(p)
    return valid_review(2) and job.get('input_sha256')==sha(STAGES[2][2]) and job.get('output_sha256')==sha(BODY)

def valid_external_body():
    """An explicit user-approved replacement has separate provenance, never fake jobs."""
    try:
        record=load(REPORT+'approved_body_baseline.json')
        valid=(record.get('status')=='USER_APPROVED' and bool(record.get('user_acceptance'))
                and record.get('input_sha256')==sha(record['input_file'])
                and record.get('output_file')==BODY and record.get('output_sha256')==sha(BODY)
                and record.get('rgb_changed_pixels')==0)
        if not valid:return False
        source=np.array(Image.open(ROOT/record['input_file']))
        output=np.array(Image.open(ROOT/BODY))
        expected=source.copy();expected[expected[:,:,3]==254,3]=255
        return bool(np.array_equal(expected,output))
    except (KeyError,FileNotFoundError,ValueError):return False

def prepare():
    size=verify_frozen();source=Image.open(ROOT/MASTER).convert('RGBA')
    for folder in [WORK+'masks',WORK+'prompts',WORK+'raw',REPORT+'ai_jobs']:
        (ROOT/folder).mkdir(parents=True,exist_ok=True)
    # Draft polygons are traced from this exact Rig Master. White = editable.
    # Exclusions lock visible head identity and the existing bow-holding fingers.
    masks=[]
    for i in range(3):
        m=Image.new('L',size,0);d=ImageDraw.Draw(m)
        if i==0:
            d.line([(842,36),(812,89),(801,139),(803,188),(817,239),(836,291),(849,340),(865,400),(878,455),(880,505),(877,550),(866,593),(852,643),(843,693),(841,765),(837,824),(840,881),(841,919),(829,962),(817,1005),(799,1048),(778,1090),(759,1132),(741,1174),(730,1213),(727,1255),(730,1300),(739,1347),(754,1395)],fill=255,width=50,joint='curve')
            d.line([(801,142),(718,1285)],fill=255,width=12)
            d.polygon([(780,688),(796,674),(822,674),(846,691),(866,691),(884,701),(882,741),(866,753),(832,756),(803,745),(785,731)],fill=0)
        elif i==1:
            d.polygon([(231,190),(359,182),(379,243),(398,291),(395,341),(362,444),(341,509),(317,512),(298,460),(283,387),(264,338),(254,281)],fill=255)
        else:
            d.polygon([(482,302),(447,299),(411,307),(380,324),(356,348),(338,372),(331,411),(336,450),(329,480),(317,523),(323,547),(341,559),(355,541),(365,510),(389,460),(413,420),(439,383),(462,377),(500,410),(535,449),(563,476),(600,493),(625,488),(643,466),(652,442),(648,415),(629,395),(628,373),(607,353),(575,355),(526,332)],fill=255)
            d.polygon([(376,420),(404,416),(431,427),(456,448),(467,478),(472,506),(458,532),(448,530),(428,517),(400,508),(374,505),(354,512),(350,493),(367,458)],fill=0)
            d.polygon([(401,534),(415,533),(426,562),(427,590),(418,625),(408,627),(400,589)],fill=255)
        d.rectangle((380,100,645,305),fill=0)
        path=ROOT/WORK/'masks'/f'{STAGES[i][0]}.png'
        if path.exists():
            # Rerunning preparation never replaces reviewed/manual mask changes.
            m=Image.open(path).convert('L')
        else:m.save(path)
        masks.append(m)
    prompts=[
        '仅移除该图中木弓、握柄上露出的弓体和弓弦。只在白色mask内局部编辑；保留持弓手已可见的手指、手腕、护腕。弓弦穿过手臂的细区域按周围原有皮革/皮肤补齐，不新增装备。不得改变头部、衣服、姿势、人体比例。',
        '仅移除背后的箭袋及袋中箭束。白色mask以外保持逐像素不变。按当前已可见轮廓恢复少量披布边缘及必要背景，不改变头发、红色头巾和头巾飘带，不创造新甲片。',
        '仅移除橄榄绿色披布、肩部披肩和属于披肩的圆形扣饰。仅在白色mask内补齐被挡住的肩部、颈肩过渡、现有棕色皮甲上缘与象牙白/红边短袖结构。严格延续现有皮甲和衣料，不加高领甲、头盔、肩甲或其他重甲。保留可见袖口、手臂、脸、发型、头巾与胸甲主体。']
    common='\n唯一编辑底图是本阶段input，唯一人体像素来源为RIG_MASTER的派生链。DESIGN用于身份约束；CODEX和WALK_REFERENCE不得用于补人体或提取像素。不能重新生成整个人物。输出1024x1536同画布真实透明RGBA PNG；不能画棋盘格或烘焙黑底；完整保留未编辑区域。只允许局部INPAINT/REMOVE/COMPLETE。\n'
    overview=Image.new('RGB',(1050,580),'#eeeeee');draw=ImageDraw.Draw(overview)
    for i,(m,prompt) in enumerate(zip(masks,prompts)):
        name=STAGES[i][0];p=ROOT/WORK/'prompts'/f'{name}.txt'
        if not p.exists():p.write_text(prompt+common,encoding='utf-8')
        base=composite(source,'#999999').convert('RGBA');tint=Image.new('RGBA',size,(255,35,120,0));tint.putalpha(m.point(lambda x:round(x*.48)));base.alpha_composite(tint)
        base.thumbnail((330,510));overview.paste(base.convert('RGB'),(i*350+10,42))
        draw.text((i*350+10,8),name,font=font(16),fill='black')
        draw.text((i*350+10,550),'DRAFT - local mask review required',font=font(14),fill='#9b2222')
        job_path=REPORT+'ai_jobs/'+name+'.json'
        if not (ROOT/job_path).exists():save(job_path,stage_record(i))
    overview.save(ROOT/REPORT/'occlusion_mask_review.png')
    save(REPORT+'mask_manifest.json',{'canvas':list(size),'convention':'L PNG; white=editable; black=protected','status':'DRAFT_REVIEW_REQUIRED','masks':[{'file':WORK+'masks/'+s[0]+'.png','sha256':sha(WORK+'masks/'+s[0]+'.png'),'editable_pixels':int((np.array(m)>0).sum()),'review_required':True} for s,m in zip(STAGES,masks)],'review_notes':['Bow mask protects visible gripping fingers; inspect tiny grip/finger islands before external edit.','Quiver/hair boundary must preserve headband tails.','Cloak mask protects visible ivory sleeves; inspect sleeve seam and leather chest upper edge.','Masks B/C are drafts anchored to the unchanged source; recheck against each approved predecessor before use.']})
    print('Prepared 3 real draft masks and prompts; image edits NOT_RUN')

def reference_reviews():
    verify_frozen();entries=load(SOURCE+'source_manifest.json')['files']
    sheet=Image.new('RGB',(1500,520),'#eeeeee');d=ImageDraw.Draw(sheet)
    for i,e in enumerate(entries):
        im=Image.open(ROOT/e['file']).convert('RGBA');preview=composite(im,'#c5c5c5');preview.thumbnail((280,420))
        sheet.paste(preview,(i*300+10,40));d.text((i*300+10,10),e['role'],font=font(18),fill='black')
        d.text((i*300+10,490),'PRODUCTION SOURCE' if e['production_pixels_allowed'] else 'REFERENCE ONLY',font=font(14),fill='black')
    sheet.save(ROOT/REPORT/'source_role_review.png')
    ref=Image.open(ROOT/next(e['file'] for e in entries if e['role']=='WALK_REFERENCE'))
    sheet=Image.new('RGB',(1400,880),'#eeeeee');d=ImageDraw.Draw(sheet)
    # Overlapping context crops intentionally keep the feet, not isolated sprites.
    for i,center in enumerate([150,425,700,975,1250,1525,1800,2050]):
        box=(max(0,center-190),75,min(ref.width,center+195),660)
        crop=ref.crop(box);crop.thumbnail((335,365));x=(i%4)*350+8;y=(i//4)*420+38
        sheet.paste(crop,(x,y));d.text((x,y-28),f'Reference cue {i} / MOTION ONLY',font=font(16),fill='black')
    d.text((10,850),'Context crops only. Passing and full alternating cycle must be authored and tested in the real rig.',font=font(17),fill='#a02020')
    sheet.save(ROOT/REPORT/'walk_reference_pose_review.png')
    print('Source-role and motion-only reference reviews generated; no Godot poses claimed')

def import_stage(i,result,tool_id):
    verify_frozen();name,input_file,output=STAGES[i]
    if i and not valid_review(i-1):raise ValueError('PREVIOUS_STAGE_NOT_APPROVED')
    if (ROOT/output).exists():raise ValueError('Output already exists; create a reviewed new version, never overwrite')
    incoming=safe_work_input(result)
    with Image.open(incoming) as im:raw=im.copy();file_format=im.format
    src=Image.open(ROOT/input_file).convert('RGBA');m=np.array(Image.open(ROOT/WORK/'masks'/f'{name}.png').convert('L'))>0
    if file_format!='PNG' or raw.mode!='RGBA' or raw.size!=src.size or raw.getchannel('A').getextrema()[0]!=0:raise ValueError('REQUIRE_SAME_CANVAS_TRUE_RGBA_PNG')
    # Locality is verified, not manufactured by silently pasting onto the source.
    a=np.array(src);b=np.array(raw);changes=int(np.any(a[~m]!=b[~m],axis=1).sum())
    if changes:raise ValueError(f'OUTSIDE_MASK_CHANGED: {changes} pixels; reject and return to local editor')
    shutil.copy2(incoming,ROOT/output)
    job=stage_record(i);job.update(stage_signature(i));job.update(status='IMPORTED_VISUAL_REVIEW_REQUIRED',model_tool_identifier=tool_id,external_result_path=str(incoming),outside_mask_changed_pixels=changes,model_call_executed=False)
    save(REPORT+'ai_jobs/'+name+'.json',job)
    review=Image.new('RGB',(1024,790),'#eeeeee');d=ImageDraw.Draw(review)
    for x,im,title in [(0,src,'Approved input'),(512,raw,'External local edit - REVIEW')]:
        preview=composite(im,'white');preview.thumbnail((512,768));review.paste(preview,(x,22));d.text((x+8,3),title,font=font(16),fill='black')
    review.save(ROOT/REPORT/(name+'_review.png'))
    print('Imported exact external file; visual review still required')

def review_stage(i,decision,notes):
    verify_frozen();name,_,output=STAGES[i]
    if not valid_import(i) or (i and not valid_review(i-1)):raise ValueError('IMPORTED_PROVENANCE_MISSING_OR_STALE')
    if not notes.strip():raise ValueError('Review needs observed findings')
    save(REPORT+'ai_jobs/'+name+'_review.json',{'status':decision,**stage_signature(i),'notes':notes,'timestamp':now()})
    print('Recorded hash-bound external visual review')

def import_matte(result):
    """Apply a separately reviewed grayscale alpha; never change the RGB artwork."""
    verify_frozen()
    if not valid_review(2):raise ValueError('COMPLETE_BODY_EDIT_CHAIN_NOT_APPROVED')
    if (ROOT/BODY).exists():raise ValueError('Matte output already exists; never overwrite')
    incoming=safe_work_input(result);source=Image.open(ROOT/STAGES[2][2]).convert('RGBA')
    with Image.open(incoming) as matte:
        if matte.format!='PNG' or matte.mode!='L' or matte.size!=source.size:raise ValueError('MATTE_REQUIRES_SAME_CANVAS_L_PNG')
        alpha=np.array(matte)
    old=np.array(source.getchannel('A')).astype(np.int16)
    if alpha.min()!=0 or alpha.max()!=255:raise ValueError('MATTE_REQUIRES_TRUE_TRANSPARENT_AND_OPAQUE_PIXELS')
    increased=alpha.astype(np.int16)>old
    if np.any(increased & ~((old==254)&(alpha==255))):raise ValueError('MATTE_CANNOT_INVENT_FOREGROUND')
    output=source.copy();output.putalpha(Image.fromarray(alpha));output.save(ROOT/BODY)
    save(REPORT+'matte_import.json',{'status':'VISUAL_REVIEW_REQUIRED','input_file':STAGES[2][2],
         'input_sha256':sha(STAGES[2][2]),'alpha_file':str(incoming),'alpha_sha256':sha(incoming),
         'output_file':BODY,'output_sha256':sha(BODY),'rgb_changed_pixels':0,
         'alpha_changed_pixels':int(np.count_nonzero(alpha!=old)),
         'alpha_254_to_255_pixels':int(np.count_nonzero(increased)),
         'method':'Apply reviewed alpha only; remove ground shadow, optionally normalize 254 to 255; no generative edit',
         'timestamp':now()})
    print('Imported matte as a new derivative; RGB preserved; combat-scale visual review required')

def body_reviews():
    verify_frozen();path=BODY
    if not (ROOT/path).exists():raise ValueError('COMPLETE_BODY_MISSING; import stages sequentially')
    im=Image.open(ROOT/path).convert('RGBA');bbox=im.getchannel('A').getbbox()
    if not bbox:raise ValueError('EMPTY_BODY')
    source=Image.open(ROOT/MASTER).convert('RGBA');out=Image.new('RGB',(1024,810),'#eeeeee');d=ImageDraw.Draw(out)
    for x,img,label in [(0,source,'Rig Master - immutable'),(512,im,'Complete Body candidate')]:
        preview=composite(img,'white');preview.thumbnail((512,768));out.paste(preview,(x,30));d.text((x+8,6),label,font=font(18),fill='black')
    out.save(ROOT/REPORT/'complete_body_review.png')
    out=Image.new('RGB',(990,980),'#eeeeee');d=ImageDraw.Draw(out)
    for row,height in enumerate([256,192,128]):
        scaled=im.resize((round(im.width*height/(bbox[3]-bbox[1])),round(im.height*height/(bbox[3]-bbox[1]))),Image.Resampling.LANCZOS)
        for col,bg in enumerate(['white','#808080','checker']):
            x=col*330;y=row*320;d.text((x+10,y+5),f'{height}px / {bg}',font=font(16),fill='black');out.paste(composite(scaled,bg),(x+60,y+35))
    out.save(ROOT/REPORT/'combat_scale_visual_review.png')
    save(REPORT+'body_review_request.json',{'input_file':path,'input_sha256':sha(path),'checks':{k:None for k in CHECKS},'notes':'','instruction':'Record actual visual findings; booleans are never inferred from format checks.'})
    print('Actual candidate reviews generated; visual decision required')

def gate(review_file=None):
    size=verify_frozen();path=BODY;issues=[];fmt={};visual=False
    exists=(ROOT/path).exists()
    if not exists:issues.append('Complete Body has not been produced; external local inpaint required')
    else:
        with Image.open(ROOT/path) as im:
            fmt={'format':im.format,'mode':im.mode,'dimensions':list(im.size)}
            if im.format!='PNG' or im.mode!='RGBA' or im.size!=size:issues.append('PNG/RGBA/same-canvas check failed')
            if im.mode=='RGBA':
                a=np.array(im.getchannel('A'));bbox=im.getchannel('A').getbbox();fmt.update(alpha_min=int(a.min()),alpha_max=int(a.max()),transparent_pixels=int((a==0).sum()),opaque_pixels=int((a==255).sum()),fractional_pixels=int(((a>0)&(a<255)).sum()),bbox=bbox)
                if a.min()!=0 or a.max()!=255 or (a==0).sum()<100 or (a==255).sum()<100 or not bbox:issues.append('True-alpha/opaque-foreground gate failed; source max254 is not silently promoted')
                if bbox and (bbox[0]==0 or bbox[1]==0 or bbox[2]==im.width or bbox[3]==im.height):issues.append('Foreground touches canvas boundary')
        if not valid_external_body():
            if not all(valid_review(i) for i in range(3)):issues.append('One or more edit stages lack a current PASS review')
            if not valid_matte():issues.append('Matte derivative provenance missing or stale')
        if review_file:
            review=json.loads(Path(review_file).read_text(encoding='utf-8-sig'))
            visual=review.get('input_sha256')==sha(path) and all(review.get('checks',{}).get(k) is True for k in CHECKS) and bool(review.get('notes','').strip())
        if not visual:issues.append('Complete Body/combat-scale visual review missing, stale or incomplete')
    result={'status':'PASS' if not issues else 'NOT_RUN' if not exists else 'FAIL','input_file':path,'input_sha256':sha(path) if exists else None,'provenance':'EXPLICIT_USER_APPROVED_EXTERNAL_BASELINE' if valid_external_body() else 'SEQUENTIAL_LOCAL_EDIT_CHAIN','format_checks':fmt,'visual_pass':visual,'remaining_issues':issues}
    save(REPORT+'complete_body_gate.json',result)
    save(REPORT+'pipeline_status.json',{'verdict':'BODY_PASS_DOWNSTREAM_NOT_RUN' if not issues else 'PASS_WITH_IMAGE_EDIT_MANUAL_STEP_REQUIRED' if not exists else 'BLOCKED_COMPLETE_BODY_REVIEW','complete_body':result['status'],'parts':{'required':len(PARTS),'generated':0,'approved':0,'status':'NOT_RUN'},'recomposition':'NOT_RUN','joint_tests':'NOT_RUN','animations':{n:'NOT_RUN' for n in ['idle','walk','attack_01','hit','death']},'attack_release':'NOT_RUN','twenty_unit_smoke':'NOT_RUN','human_medium_rig_reuse':'PLANNED_NOT_PROVEN','godot_handoff':'NOT_READY','note':'Manual-step verdict covers prepared art handoff, not successful native-rig production.'})
    print(json.dumps(result,ensure_ascii=True));return 0 if not issues else 2

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','reference-reviews','import-stage','review-stage','import-matte','body-reviews','gate','verify-frozen']);p.add_argument('--stage',type=int,choices=[1,2,3]);p.add_argument('--result');p.add_argument('--tool-id');p.add_argument('--decision',choices=['PASS','FAIL']);p.add_argument('--notes',default='');p.add_argument('--review-file');a=p.parse_args()
    try:
        if a.action=='prepare':prepare()
        elif a.action=='reference-reviews':reference_reviews()
        elif a.action=='import-stage':
            if not a.stage or not a.result or not a.tool_id:raise ValueError('Require --stage --result --tool-id')
            import_stage(a.stage-1,a.result,a.tool_id)
        elif a.action=='review-stage':
            if not a.stage or not a.decision:raise ValueError('Require --stage --decision --notes')
            review_stage(a.stage-1,a.decision,a.notes)
        elif a.action=='body-reviews':body_reviews()
        elif a.action=='import-matte':
            if not a.result:raise ValueError('Require --result pointing to reviewed alpha L PNG')
            import_matte(a.result)
        elif a.action=='gate':return gate(a.review_file)
        else:verify_frozen();print('Five source files and Roman Guard frozen hashes PASS')
        return 0
    except (ValueError,FileNotFoundError) as error:print(str(error));return 2

if __name__=='__main__':raise SystemExit(main())
