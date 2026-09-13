"""Source-pixel-first candidate extraction, rest reconstruction and articulation review.

Candidate files are deliberately outside formal parts until structural review.
No hidden anatomy or equipment pixels are synthesized.
"""
import json, math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
import cretan_archer_pipeline as p

OUT=p.WORK+'candidates/parts/'
MASKS=p.WORK+'masks/parts/'
R=p.REPORT+'parts_v1/'
POLYGONS={
 'torso':[(400,328),(484,328),(626,357),(657,426),(638,570),(646,690),(419,690),(414,583),(431,555),(442,482),(411,414)],
 'pelvis':[(440,614),(630,614),(673,781),(675,1005),(351,1005),(354,922),(406,735)],
 'head':[(365,95),(665,95),(665,316),(581,354),(592,379),(561,382),(530,368),(488,342),(438,332),(365,332)],
 'leg_far_thigh':[(523,927),(657,932),(655,1077),(625,1149),(516,1149),(502,1061),(520,1010)],
 'leg_near_thigh':[(401,936),(523,947),(527,1002),(469,1102),(439,1148),(337,1148),(338,1090),(371,1024)],
 'leg_far_shin':[(510,1092),(640,1092),(652,1326),(622,1361),(525,1355),(513,1288),(489,1190)],
 'leg_near_shin':[(337,1088),(464,1104),(441,1198),(416,1288),(412,1370),(319,1370),(316,1220),(317,1154)],
 'foot_far':[(517,1327),(641,1327),(680,1350),(771,1385),(780,1455),(511,1455)],
 'foot_near':[(317,1328),(413,1328),(433,1391),(462,1420),(462,1470),(297,1470)],
 'arm_far_upper':[(609,394),(639,411),(676,518),(671,561),(716,601),(733,639),(698,683),(637,646),(614,586),(612,548)],
 'arm_far_fore':[(692,607),(718,605),(746,630),(796,674),(809,689),(803,736),(768,737),(704,705),(648,678),(675,642)],
 'hand_far':[(798,672),(846,667),(905,684),(907,779),(797,784),(774,740),(782,704)],
 'arm_near_upper':[(397,350),(436,352),(466,374),(495,421),(491,487),(471,529),(441,546),(430,566),(414,589),(424,661),(397,688),(329,669),(324,570),(346,522),(331,505),(341,453),(361,393)],
 'arm_near_fore':[(332,647),(426,647),(426,706),(425,797),(348,809),(328,726)],
 'hand_near':[(350,783),(412,781),(421,803),(427,822),(429,845),(444,858),(445,877),(438,882),(432,881),(432,894),(423,900),(412,895),(400,892),(392,887),(380,882),(366,874),(359,863),(352,842)]
}
PIVOTS={'pelvis':[524,638],'torso':[523,620],'head':[539,356],
 'arm_near_upper':[440,425],'arm_near_fore':[382,653],'hand_near':[388,789],
 'arm_far_upper':[631,473],'arm_far_fore':[704,645],'hand_far':[797,708],
 'leg_near_thigh':[455,839],'leg_near_shin':[399,1102],'foot_near':[368,1347],
 'leg_far_thigh':[563,839],'leg_far_shin':[568,1110],'foot_far':[576,1347],
 'bow':[844,725],'bow_string':[801,142],'quiver':[325,337],'cloak':[505,367],'arrow_single':None}
LINKS=[('torso','head','neck',70),('torso','pelvis','waist',145),
 ('torso','arm_near_upper','near_shoulder',100),('torso','arm_far_upper','far_shoulder',70),
 ('arm_near_upper','arm_near_fore','near_elbow',80),('arm_near_fore','hand_near','near_wrist',65),
 ('arm_far_upper','arm_far_fore','far_elbow',76),('arm_far_fore','hand_far','far_wrist',60),
 ('pelvis','leg_near_thigh','near_hip',110),('pelvis','leg_far_thigh','far_hip',100),
 ('leg_near_thigh','leg_near_shin','near_knee',100),('leg_near_shin','foot_near','near_ankle',76),
 ('leg_far_thigh','leg_far_shin','far_knee',95),('leg_far_shin','foot_far','far_ankle',78)]
ORDER=['cloak','quiver','arm_far_upper','arm_far_fore','hand_far','leg_far_thigh','leg_far_shin','foot_far','leg_near_thigh','leg_near_shin','foot_near','pelvis','torso','head','arm_near_upper','arm_near_fore','hand_near','bow','bow_string']

def poly(points,size):
    im=Image.new('L',size);ImageDraw.Draw(im).polygon(points,fill=255);return np.array(im)>0

def extract(im,mask):
    a=np.array(im);a[:,:,3]=np.where(mask,a[:,:,3],0);a[a[:,:,3]==0,:3]=0
    return Image.fromarray(a)

def compose(parts):
    im=Image.new('RGBA',(1024,1536))
    for name in ORDER:
        if name in parts:im.alpha_composite(parts[name])
    return im

def tiles(items,path,cols=4,height=256):
    tilew=230;tileh=height+78;sheet=Image.new('RGB',(tilew*cols,tileh*math.ceil(len(items)/cols)),'#eeeeee');d=ImageDraw.Draw(sheet)
    for i,(name,im) in enumerate(items):
        x=(i%cols)*tilew;y=(i//cols)*tileh
        v=im.resize((round(1024*height/1340),round(1536*height/1340)),Image.Resampling.LANCZOS)
        sheet.paste(p.composite(v,'white'),(x+8,y+35));d.text((x+5,y+8),name,font=p.font(14),fill='black')
    sheet.save(p.ROOT/path)

def build():
    p.verify_frozen()
    gate=p.load(p.REPORT+'complete_body_gate.json')
    assert p.valid_external_body() and gate['status']=='PASS' and gate['input_sha256']==p.sha(p.BODY)
    for folder in [OUT,MASKS,R]:(p.ROOT/folder).mkdir(parents=True,exist_ok=True)
    body=Image.open(p.ROOT/p.BODY).convert('RGBA');a=np.array(body);fg=a[:,:,3]>0;labels=np.zeros(fg.shape,np.uint8)
    names=list(POLYGONS)
    for i,name in enumerate(names,1):labels[poly(POLYGONS[name],body.size)&fg]=i
    # Anatomy owns overlapping polygon intersections; no nearest-part random fill.
    residual=fg&(labels==0);extract(body,residual).save(p.ROOT/R/'unassigned_pixels.png')
    masks={n:labels==i for i,n in enumerate(names,1)};yy,xx=np.indices(fg.shape);overlaps=[]
    for parent,child,name,diameter in LINKS:
        x,y=PIVOTS[child];axis=np.array(PIVOTS[child],float)-np.array(PIVOTS[parent],float)
        axis/=max(np.linalg.norm(axis),1)
        projection=(xx-x)*axis[0]+(yy-y)*axis[1]
        band=(masks[parent]|masks[child])&(a[:,:,3]>240)&((xx-x)**2+(yy-y)**2<=(diameter*.65)**2)&(abs(projection)<=diameter*.15)
        # Never make a disconnected "hip cap" from skirt pixels. Missing hidden
        # thigh geometry must be completed as art, not fabricated by overlap.
        missing_child=not bool((band&masks[child]).any())
        if missing_child:band[:]=False
        masks[parent]|=band;masks[child]|=band
        overlaps.append({'name':name,'parent':parent,'child':child,'pivot':PIVOTS[child],'diameter':diameter,'requested_axial_overlap_percent':30,'shared_source_pixels':int(band.sum()),'hidden_geometry_missing':missing_child,'new_hidden_pixels_created':0})
    parts={}
    for name,mask in masks.items():
        Image.fromarray(mask.astype('uint8')*255).save(p.ROOT/MASKS/(name+'.png'))
        parts[name]=extract(body,mask);parts[name].save(p.ROOT/OUT/(name+'.png'))
    p.save(R+'body_mask_definition.json',{'source':p.BODY,'sha256':p.sha(p.BODY),'polygons':POLYGONS,'pivots':PIVOTS,'overlaps':overlaps,'unassigned_pixels':int(residual.sum()),'unassigned_alpha_gt_16':int((residual&(a[:,:,3]>16)).sum()),'unassigned_alpha_max':int(a[:,:,3][residual].max()) if residual.any() else 0,'status':'CANDIDATES_REVIEW_REQUIRED','hidden_completion':False})
    colors=[(212,80,85),(65,151,215),(222,169,55),(143,87,184),(79,175,120)]
    overlay=p.composite(body,'#808080').convert('RGBA');d=ImageDraw.Draw(overlay)
    for i,name in enumerate(names):d.line(POLYGONS[name]+[POLYGONS[name][0]],fill=colors[i%5]+(255,),width=2)
    for name,(x,y) in [(n,xy) for n,xy in PIVOTS.items() if n in names]:
        d.ellipse((x-5,y-5,x+5,y+5),fill='yellow');d.text((x+7,y-6),name,font=p.font(13),fill='yellow')
    overlay.convert('RGB').save(p.ROOT/R/'body_mask_pivot_review.png')
    tiles([(n,parts[n]) for n in names],R+'body_part_contact_sheet.png',cols=5)
    recomposed=compose(parts);recomposed.save(p.ROOT/R/'body_recomposed.png')
    diff=np.abs(np.array(recomposed).astype(int)-a.astype(int));Image.fromarray(np.clip(diff[:,:,:3]*4,0,255).astype('uint8')).save(p.ROOT/R/'body_recomposition_diff.png')
    tiles([('Approved Body',body),('15-part body rest',recomposed)],R+'body_rest_combat_review.png',cols=2)
    # Equipment draft extraction: only visible Master pixels; hidden regions stay missing.
    master=Image.open(p.ROOT/p.MASTER).convert('RGBA')
    bowmask=np.array(Image.open(p.ROOT/p.WORK/'masks/001_remove_bow.png'))>0
    string=Image.new('L',master.size);sd=ImageDraw.Draw(string);sd.line([(801,142),(718,1285)],fill=255,width=5)
    # String section crossing arm/grip is not separable by color; leave it unfilled.
    sm=np.array(string)>0;sm[550:800,:]=False
    bowmask &= ~ (np.array(string)>0)
    bowmask[550:800,:740]=False
    cloakmask=np.array(Image.open(p.ROOT/p.WORK/'masks/003_remove_cloak.png'))>0
    cloakmask[520:,:]=False  # Detached context wedge is arm/skin, not cloak.
    eq={'bow':bowmask,'bow_string':sm,
        'quiver':np.array(Image.open(p.ROOT/p.WORK/'masks/002_remove_quiver.png'))>0,
        'cloak':cloakmask}
    for name,mask in eq.items():
        parts[name]=extract(master,mask);parts[name].save(p.ROOT/OUT/(name+'.png'))
        Image.fromarray(mask.astype('uint8')*255).save(p.ROOT/MASKS/(name+'.png'))
    tiles([(n,parts[n]) for n in eq],R+'equipment_visible_pixel_review.png',cols=4)
    full=compose(parts);full.save(p.ROOT/R/'recomposition_candidate.png')
    tiles([('Frozen Master',master),('Approved body + equipment',full)],R+'recomposition_combat_review.png',cols=2)
    # Rotate the distal chain together; test both signs, no patch covering holes.
    chain={'near_elbow':['arm_near_fore','hand_near'],'far_elbow':['arm_far_fore','hand_far'],
           'near_knee':['leg_near_shin','foot_near'],'far_knee':['leg_far_shin','foot_far']}
    items=[]
    for joint,children in chain.items():
        for angle in [-20,0,20]:
            trial={n:parts[n] for n in names}
            for n in children:trial[n]=trial[n].rotate(angle,Image.Resampling.BICUBIC,center=PIVOTS[children[0]])
            image=compose(trial);image.save(p.ROOT/R/f'{joint}_{angle:+d}.png');items.append((f'{joint} {angle:+d}',image))
    tiles(items,R+'joint_rotation_256.png',cols=3,height=256)
    tiles(items,R+'joint_rotation_192.png',cols=3,height=192)
    manifest=p.load('tools/cretan_archer_parts_manifest.json')
    for entry in manifest['parts']:
        name=entry['name'];entry['pivot_hint']=PIVOTS[name]
        if name in parts:
            entry.update(candidate_file=OUT+name+'.png',candidate_sha256=p.sha(OUT+name+'.png'),mask=MASKS+name+'.png',status='CANDIDATE_NOT_APPROVED',review_required=True,ai_completed=False,hidden_completion=False)
    manifest['status']='19_VISIBLE_PIXEL_CANDIDATES_NO_FORMAL_APPROVAL';p.save('tools/cretan_archer_parts_manifest.json',manifest)
    p.save(R+'extraction_metrics.json',{'body_source_sha256':p.sha(p.BODY),'body_candidates':15,'equipment_visible_candidates':4,'arrow_single':'MISSING_FULL_ARROW','formal_parts':0,'body_rest_max_rgba_difference':int(diff.max()),'body_rest_changed_pixels':int(np.any(diff,axis=2).sum()),'unassigned_alpha_gt_16':int((residual&(a[:,:,3]>16)).sum()),'partial_equipment':True,'joint_tests':'RENDERED_REVIEW_REQUIRED','godot_handoff':'NOT_READY'})
    print(json.dumps(p.load(R+'extraction_metrics.json')))

if __name__=='__main__':build()
