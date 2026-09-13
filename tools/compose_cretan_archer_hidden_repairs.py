"""Composite actual generated hidden-region patches; freeze all approved Body pixels.

Raw model outputs are RGB with a baked checkerboard and are NOT formal assets.
This script uses traced patch geometry, matches it to the source canvas, retains
source-owned visible pixels, and records every derived edit. No native mask claim.
"""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
import cretan_archer_pipeline as p
import build_cretan_archer_parts as b

RAW=p.WORK+'self_repair/body/'
BASE=p.WORK+'self_repair/ownership/'
OUT=p.WORK+'self_repair/repaired_parts/'
R=p.REPORT+'self_repair/body/'

def polygon(points,size):
    im=Image.new('L',size);ImageDraw.Draw(im).polygon(points,fill=255);return im

def fit(raw,box,outsize=(1024,1536),rawbox=None):
    """Explicit raw-to-source mapping; only sampled patch interiors are admitted."""
    x0,y0,x1,y1=box
    if rawbox:raw=raw.crop(rawbox)
    raw=raw.resize((x1-x0,y1-y0),Image.Resampling.LANCZOS)
    out=Image.new('RGBA',outsize);out.paste(raw,(x0,y0));return np.array(out)

def repair_checker_fringe(layer,use,name):
    """Extrapolate real adjacent generated material into two inspected fringes.

    The tool baked a gray checker into RGB. Traced geometry and all existing
    approved pixels stay locked: only newly added hidden-patch RGB is eligible.
    Neutral bright pixels are classified only inside the two reviewed narrow
    regions, never throughout the character. Donors come from the same real
    generated image and the same row, just inside its cloth/leather edge.
    """
    specs={'pelvis':((360,755,425,900),1,'cream tunic cloth'),
           'torso':((630,470,663,570),-1,'brown leather torso edge')}
    if name not in specs:return layer,None
    box,direction,material=specs[name]
    rgb=layer[:,:,:3].astype(np.int16)
    region=np.zeros(use.shape,bool);x0,y0,x1,y1=box;region[y0:y1,x0:x1]=True
    neutral=(rgb[:,:,0]-rgb[:,:,2]<18)&(np.abs(rgb[:,:,0]-rgb[:,:,1])<14)&(rgb.mean(2)>90)
    fringe=use&region&neutral
    fixed=layer.copy();donors=[]
    for y,x in zip(*np.where(fringe)):
        candidates=[]
        # Prefer same-row local material. +/-2 rows are a fallback around folds.
        for dy in (0,-1,1,-2,2):
            yy=y+dy
            if not 0<=yy<layer.shape[0]:continue
            for distance in range(2,65):
                xx=x+direction*distance
                if not 0<=xx<layer.shape[1] or layer[yy,xx,3]<240:continue
                r,g,b=map(int,layer[yy,xx,:3])
                good=(r-b>=22 and r>=145 and g>=120 and b>=85 and r-g<55) if name=='pelvis' else (r-b>=20 and r>=65 and r-g>=4)
                if good:
                    candidates.append((abs(dy)*8+distance,yy,xx));break
        if not candidates:raise RuntimeError(f'No real {material} donor at {name} {x},{y}')
        _,yy,xx=min(candidates)
        fixed[y,x,:3]=layer[yy,xx,:3];donors.append([int(x),int(y),int(xx),int(yy)])
    changed=np.any(fixed[:,:,:3]!=layer[:,:,:3],axis=2)
    assert not np.any(changed&~use)
    assert np.array_equal(fixed[:,:,3],layer[:,:,3])
    Image.fromarray(changed.astype('uint8')*255).save(p.ROOT/R/(name+'_checker_rgb_correction_mask.png'))
    record={'status':'APPLIED_TO_ADDED_HIDDEN_PATCH_ONLY','material':material,
        'reviewed_region':list(box),'changed_rgb_pixels':int(changed.sum()),
        'approved_source_rgba_changed':0,'alpha_changed_pixels':0,'geometry_mask_changed':False,
        'method':'Restricted neutral checker classification; nearest same-row real generated material sampled inward; no new AI call',
        'classification':'R-B <18, abs(R-G)<14, mean RGB >90; only actual added pixels inside reviewed ROI',
        'correction_mask':R+name+'_checker_rgb_correction_mask.png',
        'donor_map':R+name+'_checker_rgb_donors.json'}
    p.save(record['donor_map'],{'columns':['target_x','target_y','donor_x','donor_y'],'donors':donors})
    return fixed,record

def main():
    p.verify_frozen();assert p.valid_external_body()
    for folder in [OUT,R]:(p.ROOT/folder).mkdir(parents=True,exist_ok=True)
    records=[];parts={n:Image.open(p.ROOT/BASE/(n+'.png')).convert('RGBA') for n in b.POLYGONS}
    # A traced silhouette excludes the generator's checkerboard. It is only used
    # where no original garment pixel exists inside the explicit repair mask.
    g=Image.open(p.ROOT/RAW/'pelvis_generated_raw.png').convert('RGBA')
    contour=[(394,122),(853,120),(881,172),(921,288),(941,478),(978,637),(1008,850),(986,875),(992,1058),(922,1092),(825,1103),(722,1111),(635,1113),(606,1133),(505,1105),(447,1135),(377,1060),(319,1052),(290,1090),(221,1051),(180,1037),(209,926),(240,813),(265,679),(286,565),(313,459),(323,358),(343,310),(369,239),(378,166)]
    g.putalpha(polygon(contour,g.size))
    layer=fit(g,(360,612,675,979),rawbox=(176,121,1010,1139))
    configs={'pelvis':(layer,polygon([(350,765),(430,761),(455,813),(455,922),(359,953),(343,888)],(1024,1536)),'pelvis_generated_raw.png')}
    # Hidden thighs are matte-bounded interior skin samples, not copies of cloth.
    # Existing visible skin remains the exact approved Body pixels.
    for name,file,box,rawbox,points in [
      ('leg_near_thigh','near_thigh_generated_raw.png',(401,805,521,1009),(555,176,820,650),[(419,805),(484,805),(504,830),(514,924),(521,978),(490,1009),(399,1009),(404,925),(402,836)]),
      ('leg_far_thigh','far_thigh_generated_raw.png',(513,805,643,1000),(548,316,794,778),[(531,805),(595,805),(617,834),(634,923),(643,979),(618,1000),(518,1000),(513,918),(515,837)])]:
        raw=Image.open(p.ROOT/RAW/file).convert('RGBA');configs[name]=(fit(raw,box,rawbox=rawbox),polygon(points,(1024,1536)),file)
    g=Image.open(p.ROOT/RAW/'torso_generated_raw.png').convert('RGBA')
    g.putalpha(polygon([(302,200),(338,165),(392,127),(470,127),(558,178),(614,229),(677,263),(796,277),(812,230),(841,236),(886,314),(934,445),(955,538),(942,692),(940,910),(958,1090),(389,1121),(397,1066),(417,982),(418,917),(398,804),(385,682),(363,557),(373,401),(350,292)],g.size))
    layer=fit(g,(377,334,660,666),rawbox=(302,125,960,1121))
    torso_mask=polygon([(382,351),(442,349),(498,415),(503,504),(457,567),(419,597),(398,544),(392,447)],(1024,1536))
    ImageDraw.Draw(torso_mask).polygon([(601,378),(646,410),(669,528),(646,568),(614,549),(600,464)],fill=255)
    configs['torso']=(layer,torso_mask,'torso_generated_raw.png')
    approved_silhouette=np.array(Image.open(p.ROOT/p.BODY))[:,:,3]>16
    for name,(layer,mask,file) in configs.items():
        source=np.array(parts[name]);allowed=np.array(mask)>0
        # Existing source material wins. This produces a hidden underpainting,
        # never a replacement of visible original character design.
        use=allowed&approved_silhouette&(source[:,:,3]==0)&(layer[:,:,3]>0)
        layer,checker_correction=repair_checker_fringe(layer,use,name)
        result=source.copy();result[use]=layer[use];result[use,3]=255
        parts[name]=Image.fromarray(result)
        Image.fromarray(use.astype('uint8')*255).save(p.ROOT/R/(name+'_actual_edit_mask.png'))
        outside_changed=int(np.any(result[~allowed]!=source[~allowed],axis=1).sum())
        assert outside_changed==0
        assert np.array_equal(result[source[:,:,3]>0],source[source[:,:,3]>0])
        records.append({'part':name,'base_file':BASE+name+'.png','base_sha256':p.sha(BASE+name+'.png'),
            'raw_generation':RAW+file,'raw_sha256':p.sha(RAW+file),'actual_edit_mask':R+name+'_actual_edit_mask.png',
            'generated_hidden_pixels_added':int(use.sum()),'visible_source_rgba_changed':0,'outside_allowed_mask_changed':outside_changed,
            'tool':'image_gen.imagegen','model_identifier':'not exposed','raw_mode':'RGB','native_mask_parameter':False,
            'method':'Actual generated hidden material + explicit source-canvas mapping and traced patch matte; all pre-existing visible source pixels locked',
            'checker_rgb_correction':checker_correction})
    for name,im in parts.items():im.save(p.ROOT/OUT/(name+'.png'))
    for record in records:record.update(output_file=OUT+record['part']+'.png',output_sha256=p.sha(OUT+record['part']+'.png'))
    p.save(R+'repair_jobs.json',records)
    b.tiles([(n,parts[n]) for n in configs],R+'repaired_part_review.png',cols=4)
    reconstructed=b.compose(parts);reconstructed.save(p.ROOT/R/'body_recomposed.png')
    b.tiles([('Approved Body',Image.open(p.ROOT/p.BODY).convert('RGBA')),('Repaired rest',reconstructed)],R+'rest_review_256.png',cols=2)
    items=[]
    chains={'near_elbow':['arm_near_fore','hand_near'],'far_elbow':['arm_far_fore','hand_far'],
            'near_knee':['leg_near_shin','foot_near'],'far_knee':['leg_far_shin','foot_far'],
            'near_hip':['leg_near_thigh','leg_near_shin','foot_near'],'far_hip':['leg_far_thigh','leg_far_shin','foot_far'],
            'near_shoulder':['arm_near_upper','arm_near_fore','hand_near'],'far_shoulder':['arm_far_upper','arm_far_fore','hand_far']}
    for joint,children in chains.items():
        for angle in [-20,0,20]:
            trial=parts.copy()
            for child in children:trial[child]=trial[child].rotate(angle,Image.Resampling.BICUBIC,center=b.PIVOTS[children[0]])
            frame=b.compose(trial);frame.save(p.ROOT/R/f'{joint}_{angle:+d}.png');items.append((joint+f' {angle:+d}',frame))
    for height in [256,192]:b.tiles(items,R+f'joint_review_{height}.png',cols=3,height=height)
    for page in [0,1]:b.tiles(items[page*12:(page+1)*12],R+f'joint_review_256_page{page}.png',cols=3,height=256)
    p.verify_frozen();print(json.dumps({'body_parts':len(parts),'generated_repairs':records,'source_body_unchanged':True}))

if __name__=='__main__':main()
