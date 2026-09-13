"""Assemble real repaired candidates and render combat-scale asset gates."""
import json, math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
import cretan_archer_pipeline as p
import build_cretan_archer_parts as b

OUT=p.WORK+'self_repair/repaired_parts/'
REPORT=p.REPORT+'self_repair/assembled/'
ORDER=['quiver','leg_far_thigh','leg_far_shin','foot_far','arm_far_upper','arm_far_fore',
       'leg_near_thigh','leg_near_shin','foot_near','pelvis','torso','cloak','head',
       'arm_near_upper','arm_near_fore','hand_near','bow_string','bow','hand_far','arrow_single']
HEIGHT=1340

def compose(parts,arrow=False):
    out=Image.new('RGBA',(1024,1536))
    for name in ORDER:
        if name in parts and (name!='arrow_single' or arrow):out.alpha_composite(parts[name])
    return out

def sheet(items,path,heights=(256,192),backgrounds=('white','#808080','#436b90')):
    columns=len(items)*len(backgrounds);cw=224;rh=[h+54 for h in heights]
    out=Image.new('RGB',(columns*cw,sum(rh)),'#eeeeee');d=ImageDraw.Draw(out);y=0
    for h,rowh in zip(heights,rh):
        for i,(name,im) in enumerate(items):
            v=im.resize((round(1024*h/HEIGHT),round(1536*h/HEIGHT)),Image.Resampling.LANCZOS)
            for j,bg in enumerate(backgrounds):
                x=(i*len(backgrounds)+j)*cw
                d.text((x+5,y+3),f'{name} | {h}px',font=p.font(13),fill='black')
                out.paste(p.composite(v,bg),(x+10,y+20))
        y+=rowh
    out.save(p.ROOT/path)

def main():
    p.verify_frozen();assert p.valid_external_body()
    (p.ROOT/REPORT).mkdir(parents=True,exist_ok=True)
    parts={n:Image.open(p.ROOT/OUT/(n+'.png')).convert('RGBA') for n in b.POLYGONS}
    source={
      'bow':'equipment_bow_arrow/bow_full_candidate.png',
      'arrow_single':'equipment_bow_arrow/arrow_single_candidate.png',
      'quiver':'equipment_quiver_cloak/quiver_completed_same_canvas.png',
      'cloak':'equipment_quiver_cloak/cloak_completed_same_canvas.png'}
    for n,file in source.items():parts[n]=Image.open(p.ROOT/p.WORK/'self_repair'/file).convert('RGBA')
    # Controllable string is a native straight-line asset with source-observed
    # attachment points. No hand, bow wood, or whole-character pixels copied.
    scale=4;st=Image.new('RGBA',(1024*scale,1536*scale))
    ImageDraw.Draw(st).line([(790*scale,150*scale),(719*scale,1240*scale)],fill=(66,48,29,255),width=8)
    parts['bow_string']=st.resize((1024,1536),Image.Resampling.LANCZOS)
    for n,im in parts.items():im.save(p.ROOT/OUT/(n+'.png'))
    rest=compose(parts);rest.save(p.ROOT/REPORT/'recomposed.png')
    reference=Image.open(p.ROOT/p.BODY).convert('RGBA')
    # Compare approved Body + finished equipment to the actual part assembly;
    # old Master is also shown, with accepted Body identity differences noted.
    ref=Image.new('RGBA',reference.size);ref.alpha_composite(parts['quiver']);ref.alpha_composite(reference)
    for n in ['cloak','bow_string','bow']:ref.alpha_composite(parts[n])
    ref.alpha_composite(parts['hand_far'])
    ref.save(p.ROOT/REPORT/'approved_body_equipment_reference.png')
    sheet([('Master',Image.open(p.ROOT/p.MASTER)),('Approved + gear',ref),('20-part rest',rest)],REPORT+'recomposition_combat_review.png',backgrounds=('white',))
    sheet([('Repaired unit',rest)],REPORT+'multibackground_review.png')
    diff=np.abs(np.array(ref).astype(int)-np.array(rest).astype(int))
    Image.fromarray(np.clip(diff[:,:,:3]*4,0,255).astype('uint8')).save(p.ROOT/REPORT/'recomposition_diff.png')
    metrics={'status':'RENDERED_REVIEW_REQUIRED','parts_present':len(parts),'draw_order':ORDER,
             'approved_body_sha256':p.sha(p.BODY),'same_canvas':True,'arrow_visible_at_rest':False,
             'comparison':'Approved Body plus same equipment; differences diagnostic, not pixel gate',
             'changed_rgba_pixels':int(np.any(diff,axis=2).sum()),'parts':[]}
    for n,im in parts.items():
        a=np.array(im);assert im.size==(1024,1536) and im.mode=='RGBA' and a[:,:,3].min()==0 and a[:,:,3].max()>0
        metrics['parts'].append({'name':n,'file':OUT+n+'.png','sha256':p.sha(OUT+n+'.png'),'alpha_min':int(a[:,:,3].min()),'alpha_max':int(a[:,:,3].max()),'foreground_pixels':int((a[:,:,3]>0).sum())})
    # Bow stays on wrist/hand chain during shoulder and elbow tests.
    tests={
     'near_elbow':(['arm_near_fore','hand_near'],b.PIVOTS['arm_near_fore']),
     'far_elbow':(['arm_far_fore','hand_far','bow','bow_string'],b.PIVOTS['arm_far_fore']),
     'near_knee':(['leg_near_shin','foot_near'],b.PIVOTS['leg_near_shin']),
     'far_knee':(['leg_far_shin','foot_far'],b.PIVOTS['leg_far_shin']),
     'near_shoulder':(['arm_near_upper','arm_near_fore','hand_near'],b.PIVOTS['arm_near_upper']),
     'far_shoulder':(['arm_far_upper','arm_far_fore','hand_far','bow','bow_string'],b.PIVOTS['arm_far_upper']),
     'quiver':(['quiver'],b.PIVOTS['quiver']),
     'bow_grip':(['bow','bow_string'],b.PIVOTS['bow'])}
    for label,(chain,pivot) in tests.items():
        angles=[-4,0,4] if label in ['quiver','bow_grip'] else [-20,0,20]
        items=[]
        for angle in angles:
            trial=parts.copy()
            for name in chain:trial[name]=parts[name].rotate(angle,Image.Resampling.BICUBIC,center=pivot)
            frame=compose(trial);items.append((label+f' {angle:+}',frame))
            frame.save(p.ROOT/REPORT/f'{label}_{angle:+}.png')
        sheet(items,REPORT+label+'_combat_review.png',backgrounds=('white',))
    p.save(REPORT+'metrics.json',metrics)
    print(json.dumps({'parts':len(parts),'report':REPORT,'formal_promotion':False}))

if __name__=='__main__':main()
