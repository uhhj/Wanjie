"""Only near-knee plate ownership and articulation. No new painted pixels."""
from rg_common import *
from review_articulated_v3 import render, display, PAD
from PIL import ImageFilter
from near_knee_skinning import build_mesh, deform, vertices_at

BASE='reports/near_knee_baseline_v1.json'
PIVOT=(388,1083)
ANGLES=(-20,-10,0,10,20)
# Source-space trace of the existing outer plate (including its side hinge tab).
PLATE=[(350,1065),(356,1060),(366,1051),(380,1041),(393,1034),
       (407,1029),(422,1028),(435,1031),(444,1037),(450,1045),
       (454,1057),(456,1070),(454,1086),(450,1102),(443,1115),
       (432,1128),(418,1137),(406,1142),(394,1144),(390,1141),
       (380,1128),(372,1115),(365,1097),(350,1095),(352,1081)]

def baseline():
    if (ROOT/BASE).exists(): return read(BASE)
    m=read('tools/roman_guard_parts_manifest.json')
    files={body_source(),config()['source']}
    for p in m['parts']: files.update([p['file'],p['candidate_file'],p['mask']])
    b={'manifest':m,'pivots':read('assets/units/odyssey/roman_guard/roman_guard_pivots.json'),
       'file_hashes':{f:sha(f) for f in sorted(files)},'timestamp':now()}
    write(BASE,b);return b

def main():
    b=baseline();m=b['manifest'];parts={p['name']:p for p in m['parts']}
    source=rgba(body_source());a=np.array(source)[:,:,3];size=source.size
    selection=Image.new('L',size);ImageDraw.Draw(selection).polygon(PLATE,fill=255)
    plate=np.array(selection)>0
    pm=np.array(mask(parts['leg_near_thigh']['mask']))>0
    sm=np.array(mask(parts['leg_near_shin']['mask']))>0
    plate &= pm|sm
    new_masks={'leg_near_thigh':pm&~plate,'leg_near_shin':sm&~plate,'knee_near':plate}
    images={p['name']:rgba(p['file']) for p in m['parts']};files={}
    for name,mp in new_masks.items():
        path=f'work/masks/parts/{name}_articulation_v1.png'
        cp=f'work/candidates/parts/{name}_articulation_v1.png'
        Image.fromarray(mp.astype(np.uint8)*255).save(ROOT/path)
        images[name]=alpha_extract(source,mask(path));images[name].save(ROOT/cp)
        files[name]={'mask':path,'candidate_file':cp,'sha256':sha(cp),'mask_sha256':sha(path)}
    passes=[dict(d) for d in m['draw_passes']]
    passes.insert(next(i for i,d in enumerate(passes) if d['part']=='foot_near')+1,{'part':'knee_near'})
    bodypasses=[d for d in passes if d['part'] not in EQUIPMENT]
    mesh=build_mesh(images['leg_near_shin'],PIVOT,PLATE)
    mesh_path='assets/units/odyssey/roman_guard/near_knee_skinning_v1.json'
    write(mesh_path,mesh)
    frames=[];frame_files={};directory=ROOT/'reports/near_knee_articulation_v1';directory.mkdir(exist_ok=True)
    for angle in ANGLES:
        changes={'foot_near':(PIVOT,angle,(0,0))}
        posed={**images,'leg_near_shin':deform(images['leg_near_shin'],mesh,angle)}
        frame=render(posed,bodypasses,changes);frames.append(frame)
        path=f'reports/near_knee_articulation_v1/near_knee_{angle:+d}.png'
        frame.save(ROOT/path);frame_files[path]=sha(path)
    for height in (256,192):
        out=Image.new('RGB',(5*240,325),'#e8eaec');d=ImageDraw.Draw(out)
        for i,(angle,frame) in enumerate(zip(ANGLES,frames)):
            d.text((i*240+8,6),f'{angle:+d} deg / {height}px / plate 0',font=font(14),fill='black')
            tile=display(frame,height);out.paste(tile,(i*240+(240-tile.width)//2,35))
        out.save(ROOT/f'reports/near_knee_motion_{height}px_v1.png')
    # 2x local source pixels are diagnostic, not the combat acceptance scale.
    sheet([(f'{angle:+d} deg / fixed plate',f.crop((PAD+275,PAD+1000,PAD+485,PAD+1200)).resize((420,400))) for angle,f in zip(ANGLES,frames)],'reports/near_knee_motion_detail_v1.png',5,(420,400))
    review=preview(source);arr=np.array(review);old_overlap=pm&sm&(a>0)
    arr[old_overlap]=(arr[old_overlap]*.35+np.array([0,255,120])*.65).astype(np.uint8)
    edge=(np.array(selection.filter(ImageFilter.MaxFilter(3)))>0)&~plate;arr[edge]=[255,60,240]
    review=Image.fromarray(arr);d=ImageDraw.Draw(review)
    for point,color in [((389,1079),'red'),(PIVOT,'cyan')]:
        x,y=point;d.ellipse((x-3,y-3,x+3,y+3),fill=color);d.line((x-9,y,x+9,y),fill=color);d.line((x,y-9,x,y+9),fill=color)
    review.crop((280,990,475,1180)).resize((780,760)).save(ROOT/'reports/near_knee_pivot_review_v1.png')
    old_images={p['name']:rgba(p['file']) for p in m['parts']}
    rest_old=render(old_images,m['draw_passes']);rest=render(images,passes)
    rest.save(ROOT/'reports/near_knee_rest_recomposition_v1.png')
    axis=np.array(b['pivots']['joints']['near_knee']['axis']);yy,xx=np.indices(a.shape)
    def overlap(mp):
        proj=xx[mp]*axis[0]+yy[mp]*axis[1]
        return {'pixels':int(mp.sum()),'span_px':float(proj.max()-proj.min()+1),'percent':float((proj.max()-proj.min()+1)/110*100)}
    report={'status':'VISUAL_REVIEW_REQUIRED','pivot_old':[389,1079],'pivot_new':list(PIVOT),
            'pivot_basis':'Posterior knee hinge at proximal tibia/femur junction, behind patellar plate; visual estimate, not mask centroid.',
            'knee_near_binding':{'parent':'near_knee_socket','inherits_shin_rotation':False,'default_relative_rotation_deg':0,'independent_rotation_limit_hint_deg':[-3,3]},
            'coverage_overlap_before':overlap(old_overlap),'remaining_body_overlap':overlap(new_masks['leg_near_thigh']&new_masks['leg_near_shin']&(a>0)),
            'coverage_masks_unchanged':True,'coverage_added_pixels':int(((new_masks['leg_near_thigh']&~pm)|(new_masks['leg_near_shin']&~sm)).sum()),
            'plate_reassigned_pixels':int((plate&(a>0)).sum()),'rest_changed_pixels':int(np.any(np.array(rest)!=np.array(rest_old),axis=2).sum()),
            'body_sha256':sha(body_source()),'parts':files,'draw_passes':passes,'frames':frame_files,
            'skinning_file':mesh_path,'skinning_sha256':sha(mesh_path),
            'angles':list(ANGLES),'sizes':[256,192],'timestamp':now()}
    write('reports/near_knee_articulation_v1.json',report)
    print(json.dumps({k:report[k] for k in ['coverage_overlap_before','remaining_body_overlap','coverage_added_pixels','rest_changed_pixels']},indent=2))

if __name__=='__main__':main()
