"""Full-resolution and native combat-scale joint/equipment/recomposition evidence."""
from rg_common import *
from recompose_roman_guard import comparison,render_config_digest
from generate_joint_rotation_test import transform
from fix_articulated_parts_v1 import JOINTS

PAD=256
def render(images,passes,changes=None):
    out=Image.new('RGBA',(config()['canvas'][0]+2*PAD,config()['canvas'][1]+2*PAD))
    for draw in passes:
        im=images[draw['part']]
        if draw.get('clip_mask'): im=alpha_extract(im,mask(draw['clip_mask']))
        layer=Image.new('RGBA',out.size);layer.paste(im,(PAD,PAD))
        if changes and draw['part'] in changes:
            pivot,angle,translation=changes[draw['part']]
            layer=transform(layer,(pivot[0]+PAD,pivot[1]+PAD),angle,translation)
        out=Image.alpha_composite(out,layer)
    return out

def display(frame,height):
    # Review viewport expands, but source textures/canvas stay exactly 1024x1536.
    frame=frame.crop((PAD-80,PAD,PAD+1240,PAD+1536))
    bbox=rgba(body_source()).getchannel('A').getbbox(); scale=height/(bbox[3]-bbox[1])
    size=(round(frame.width*scale),round(frame.height*scale))
    small=frame.convert('RGBa').resize(size,Image.Resampling.LANCZOS).convert('RGBA')
    white=Image.new('RGBA',small.size,'white');white.alpha_composite(small)
    return white.convert('RGB')

def combat_sheet(rows,path):
    tw,th=250,318;out=Image.new('RGB',(tw*6,th*len(rows)),'#e8eaec');d=ImageDraw.Draw(out)
    for row,(name,frames) in enumerate(rows):
        for hindex,height in enumerate((256,192)):
            for index,frame in enumerate(frames):
                col=hindex*3+index;x=col*tw;y=row*th
                d.text((x+5,y+4),f'{name} {[-20,0,20][index]:+} / {height}px',font=font(13),fill='black')
                tile=display(frame,height);out.paste(tile,(x+(tw-tile.width)//2,y+30))
    out.save(ROOT/path)

def main():
    assert body_review_ok();m=read('tools/roman_guard_parts_manifest.json');piv=read('assets/units/odyssey/roman_guard/roman_guard_pivots.json')
    images={p['name']:rgba(p['candidate_file']) for p in m['parts']};bodypasses=[d for d in m['draw_passes'] if d['part'] not in EQUIPMENT]
    folder=ROOT/'reports/joints_v3';folder.mkdir(exist_ok=True)
    rows=[];equipped=[];details=[];files={};tests=[]
    for key,parent,child,point,diameter,axis in JOINTS:
        descendant={'near_elbow':'hand_near','far_elbow':'hand_far','near_knee':'foot_near','far_knee':'foot_far'}[key]
        frames=[];eframes=[]
        for angle in (-20,0,20):
            changes={n:(point,angle,(0,0)) for n in [child,descendant]}
            frame=render(images,bodypasses,changes);frames.append(frame)
            if key=='near_elbow': changes['sword']=(point,angle,(0,0))
            if key=='far_elbow': changes['shield']=(point,angle,(0,0))
            eframes.append(render(images,m['draw_passes'],changes))
            path=f'reports/joints_v3/{key}_{angle:+d}.png';frame.save(ROOT/path);files[path]=sha(path)
            crop=frame.crop((PAD+point[0]-150,PAD+point[1]-150,PAD+point[0]+150,PAD+point[1]+150))
            details.append((f'{key} {angle:+d} / 1:1 pixels',preview(crop)))
            tests.append({'joint':key,'angle':angle,'pivot':point,'frame':path,'moved_parts':[child,descendant]})
        rows.append((key,frames));equipped.append((key,eframes))
    sheet(details,'reports/joint_rotation_test_v3.png',3,(300,300))
    combat_sheet(rows,'reports/joint_rotation_combat_scale_v3.png');combat_sheet(equipped,'reports/joint_equipped_combat_scale_v3.png')
    weaponrows=[]
    for part,cases in [('shield',[(-7,(-8,0)),(0,(0,0)),(7,(8,-5))]),('sword',[(0,(0,0)),(20,(18,-5)),(30,(25,-7))])]:
        frames=[]
        for angle,tr in cases:
            frames.append(render(images,m['draw_passes'],{part:(piv['parts'][part]['position'],angle,tr)}))
        weaponrows.append((part,frames))
    combat_sheet(weaponrows,'reports/equipment_combat_scale_v3.png')
    # Correct labels for weapon cases; motion metadata never reuses elbow angles.
    im=Image.open(ROOT/'reports/equipment_combat_scale_v3.png');d=ImageDraw.Draw(im)
    for row,(part,cases) in enumerate([('shield',[-7,0,7]),('sword',[0,20,30])]):
        for col in range(6):
            d.rectangle((col*250,row*318,col*250+249,row*318+26),fill='#e8eaec')
            d.text((col*250+5,row*318+4),f'{part} {cases[col%3]:+} / {[256,192][col//3]}px',font=font(13),fill='black')
    im.save(ROOT/'reports/equipment_combat_scale_v3.png')
    current=render(images,m['draw_passes']);ref=Image.new('RGBA',current.size);ref.paste(check_source(),(PAD,PAD))
    current.crop((PAD,PAD,PAD+1024,PAD+1536)).save(ROOT/'reports/roman_guard_recomposed_v3.png')
    full=Image.new('RGB',(2048,1576),'white');d=ImageDraw.Draw(full)
    for i,(label,frame) in enumerate([('Frozen Rig Master',ref),('Current recomposition',current)]):
        d.text((i*1024+12,5),label,font=font(22),fill='black');full.paste(preview(frame.crop((PAD,PAD,PAD+1024,PAD+1536))),(i*1024,40))
    full.save(ROOT/'reports/recomposition_full_resolution_v3.png')
    for height in (256,192):
        tiles=[display(f,height) for f in [ref,current]];o=Image.new('RGB',(2*250,max(t.height for t in tiles)+32),'#e8eaec');d=ImageDraw.Draw(o)
        for i,t in enumerate(tiles):d.text((i*250+5,3),['Rig Master','Recomposed'][i]+f' / {height}px',font=font(16),fill='black');o.paste(t,(i*250+(250-t.width)//2,30))
        o.save(ROOT/f'reports/recomposition_{height}px_v3.png')
    metrics,thresholds,old_pass,diff=comparison(check_source(),current.crop((PAD,PAD,PAD+1024,PAD+1536)));diff.save(ROOT/'reports/recomposition_diff_v3.png')
    write('reports/articulated_render_manifest_v3.json',{'status':'VISUAL_REVIEW_REQUIRED','body_sha256':sha(body_source()),'part_hashes':{p['name']:sha(p['candidate_file']) for p in m['parts']},'pivot_sha256':sha('assets/units/odyssey/roman_guard/roman_guard_pivots.json'),'render_config_sha256':render_config_digest(m),'tests':tests,'full_frames':files,'review_images':{p:sha(p) for p in ['reports/joint_pivot_review_v3.png','reports/joint_rotation_test_v3.png','reports/joint_rotation_combat_scale_v3.png','reports/joint_equipped_combat_scale_v3.png','reports/equipment_combat_scale_v3.png','reports/recomposition_full_resolution_v3.png','reports/recomposition_256px_v3.png','reports/recomposition_192px_v3.png']},'legacy_geometry_diagnostic_only':{'metrics':metrics,'old_thresholds':thresholds,'old_result':old_pass,'blocking':False},'timestamp':now()})

if __name__=='__main__':main()
