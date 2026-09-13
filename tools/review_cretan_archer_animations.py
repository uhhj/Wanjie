"""Assemble only actual Godot Archer captures; never reconstruct/synthesize poses."""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw, ImageFont
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'reports/cretan_archer/native'
ANIMATIONS = ROOT / 'reports/cretan_archer/animations'
NAMES = ['idle', 'walk', 'attack_01', 'hit', 'death']

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def font(size=16):
    for path in [Path('C:/Windows/Fonts/arial.ttf'), Path('C:/Windows/Fonts/msyh.ttc')]:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()

def frame_path(row):
    path = (ROOT / row['path'].replace('res://', '')).resolve()
    if not path.is_relative_to(ROOT.resolve()):
        raise ValueError('Capture path leaves repository')
    if not path.exists() or sha(path) != row['sha256']:
        raise ValueError(f'Missing or stale Godot frame: {path}')
    return path

def composite(im, color=(232, 234, 232)):
    bg = Image.new('RGBA', im.size, color + (255,))
    bg.alpha_composite(im.convert('RGBA'))
    return bg.convert('RGB')

def common_crop(images, floor_y):
    """Crop only reporting whitespace; scale and every character pixel stay 1:1."""
    boxes = []
    for im in images:
        ar = np.array(im.convert('RGBA'))
        mask = ar[:, :, 3] > 12
        y = np.arange(im.height)[:, None]
        # Ignore neutral debug ground strokes when computing the crop, while
        # retaining them in the delivered image. Colored soles remain included.
        gray = ar[:, :, :3].max(2) - ar[:, :, :3].min(2) < 24
        ground = (y >= int(floor_y)) & (y <= int(floor_y) + 9) & gray
        mask[ground] = False
        yy, xx = np.where(mask)
        if len(xx):
            boxes.append((int(xx.min()), int(yy.min()), int(xx.max()) + 1, int(yy.max()) + 1))
    if not boxes:
        raise ValueError('No rendered character pixels found')
    return (max(0, min(b[0] for b in boxes) - 18), max(0, min(b[1] for b in boxes) - 18),
            min(images[0].width, max(b[2] for b in boxes) + 18),
            min(images[0].height, max(max(b[3] for b in boxes), int(floor_y) + 10) + 8))

def make_gif(images, frames, name, height, length, target):
    labeled = []
    for i, (im, row) in enumerate(zip(images, frames)):
        out = Image.new('RGB', (im.width, im.height + 24), (232, 234, 232))
        out.paste(composite(im), (0, 24))
        ImageDraw.Draw(out).text((5, 4), f'{name} | {height}px | {i+1:02}/16 | {row["time"]:.3f}s', font=font(13), fill='black')
        labeled.append(out)
    # One palette for the whole GIF avoids a different skin/cloth palette per frame.
    atlas = Image.new('RGB', (labeled[0].width * 4, labeled[0].height * 4))
    for i, im in enumerate(labeled):
        atlas.paste(im, ((i % 4) * im.width, (i // 4) * im.height))
    palette = atlas.quantize(colors=256)
    frames_q = [im.quantize(palette=palette, dither=Image.Dither.NONE) for im in labeled]
    if name in ['idle', 'walk']:
        durations = [round(length * 1000 / 16)] * 16
        options = {'loop': 0}
    else:
        durations = [round(length * 1000 / 15)] * 15 + [800]
        options = {}
    frames_q[0].save(target, save_all=True, append_images=frames_q[1:], duration=durations,
                     disposal=2, optimize=False, **options)
    with Image.open(target) as check:
        if check.n_frames != 16:
            raise ValueError(f'GIF does not preserve 16 captures: {target}')

def foot_review(test):
    out = Image.new('RGB', (1200, 720), 'white')
    d = ImageDraw.Draw(out)
    d.text((25, 12), 'Actual Godot world foot contacts: fixed material point during each support region', font=font(19), fill='black')
    d.text((25, 42), 'Lines: world X - expected world X. Green: sampled stable support/contact regions.', font=font(15), fill='black')
    rows = test.get('foot_samples', [])
    max_time = max((r['time'] for r in rows), default=1.0)
    for side, baseline, color in [('near', 220, '#a9442b'), ('far', 510, '#246eaa')]:
        metrics = test['foot_slide'][side]
        d.text((25, baseline - 120), f'{side} | drift@256px={metrics["at_256px"]:.4f} | expected-contact error@256px={metrics.get("expected_contact_error_at_256px",0):.4f}', font=font(16), fill=color)
        d.line((65, baseline, 1140, baseline), fill='#888888', width=1)
        groups = {}
        for row in rows:
            if row['side'] == side and row.get('support'):
                groups.setdefault(row['support_interval'], []).append(row)
        for group in groups.values():
            group.sort(key=lambda r:r['time'])
            points=[]
            for row in group:
                x=65+row['time']/max_time*1075
                error=row['world_position'][0]-row['expected_world_contact'][0]
                points.append((x,baseline-error*50))
                d.rectangle((x,baseline+45,x+4,baseline+56),fill='#529756')
            if len(points)>1:d.line(points,fill=color,width=2)
        for fraction in [0.0, 0.5, 1.0]:
            label=f'{fraction*max_time:.3f} s'
            label_width=d.textlength(label,font=font(15))
            x=65+fraction*1075-label_width*(0 if fraction==0 else 1 if fraction==1 else .5)
            d.text((x,baseline+74),label,font=font(15),fill='black')
        d.text((65,baseline+96), 'Vertical plot magnification: 50 display px per source-pixel error.',font=font(13),fill='#555555')
    target=ROOT/'reports/cretan_archer/walk_foot_contact_debug.png'
    out.save(target)
    return target

def reference_comparison(capture, crops):
    plan=read(ROOT/'reports/cretan_archer/walk_phase_plan.json')
    reference=ROOT/plan['reference_file']
    if sha(reference)!=plan['reference_sha256']:
        raise ValueError('Frozen Walk reference changed')
    ref=Image.open(reference).convert('RGB')
    rows=sorted([r for r in capture['frames'] if r['animation']=='walk' and r['height']==256],key=lambda r:r['time'])
    length=capture['animation_lengths']['walk']
    pose_images=[Image.open(frame_path(row)).convert('RGBA').crop(crops['walk']) for row in rows]
    cellw=210+pose_images[0].width
    cellh=max(280,pose_images[0].height)+80
    sheet=Image.new('RGB',(cellw*2,cellh*4+55),'#f0efea');d=ImageDraw.Draw(sheet)
    d.text((12,10),'WALK_REFERENCE motion cues (left) vs actual Godot Native Rig phases (right)',font=font(20),fill='black')
    d.text((12,35),'No pixel-similarity gate. Opposite-leg cycle and missing passing phases are authored and tested.',font=font(14),fill='black')
    mappings=[]
    for i,phase in enumerate(plan['phases']):
        x=(i%2)*cellw;y=55+(i//2)*cellh
        t=float(phase['normalized_time'])*length
        index=min(range(len(rows)),key=lambda j:abs(rows[j]['time']-t))
        crop_index=phase.get('approx_reference_crop_index')
        d.text((x+8,y+4),phase['name']+' | actual '+f'{rows[index]["time"]:.3f}s',font=font(16),fill='black')
        if crop_index is None:
            d.text((x+8,y+40),'No clear passing pose',font=font(14),fill='#633f26')
            d.text((x+8,y+62),'in the supplied strip.',font=font(14),fill='#633f26')
            d.text((x+8,y+88),'Rig pose authored;',font=font(14),fill='#633f26')
            d.text((x+8,y+110),'world contact tested.',font=font(14),fill='#633f26')
        else:
            b=(round((crop_index-1)*ref.width/8),0,round(crop_index*ref.width/8),ref.height)
            cue=ref.crop(b);cue.thumbnail((186,280),Image.Resampling.LANCZOS)
            sheet.paste(cue,(x+8,y+36))
            d.text((x+8,y+cellh-22),'Approximate motion cue',font=font(12),fill='#555555')
        sheet.paste(composite(pose_images[index],(255,255,255)),(x+202,y+36))
        mappings.append({'phase':phase['name'],'target_time':t,'actual_capture_time':rows[index]['time'],'capture':rows[index]['path'],'reference_crop_index':crop_index,'reference_match':phase['reference_match']})
    target=ROOT/'reports/cretan_archer_walk_reference_comparison.png';sheet.save(target)
    (REPORT/'walk_reference_comparison.json').write_text(json.dumps({'status':'VISUAL_REVIEW_REQUIRED','reference_role':'MOTION_ONLY','reference_pixels_in_formal_assets':False,'pixel_similarity_metric_used':False,'image':str(target),'phases':mappings},indent=2),encoding='utf-8')
    return target

def main():
    capture=read(REPORT/'capture_manifest.json')
    if capture.get('status')!='PASS' or capture.get('clipped_frames'):
        raise ValueError('GPU capture missing or clipped; do not publish a cropped passing review')
    if not capture.get('artifact_inputs'):
        raise ValueError('Capture has no scene/resource provenance')
    for path,digest in capture['artifact_inputs'].items():
        current=ROOT/path.replace('res://','')
        if not current.exists() or sha(current)!=digest:
            raise ValueError(f'GPU capture is stale for {current}')
    crops={};checks={};summary_panels=[]
    for name in NAMES:
        selected=sorted([r for r in capture['frames'] if r['animation']==name],key=lambda r:(-r['height'],r['frame']))
        all_images=[Image.open(frame_path(row)).convert('RGBA') for row in selected]
        crop=common_crop(all_images,capture['floor_y']);crops[name]=crop
        tw,th=crop[2]-crop[0],crop[3]-crop[1]
        sheet=Image.new('RGB',(tw*4,(th+26)*4),'#e8eae8');d=ImageDraw.Draw(sheet)
        outputs=[]
        for group,height in enumerate([256,192]):
            rows=sorted([r for r in selected if r['height']==height],key=lambda r:r['frame'])
            if len(rows)!=16:raise ValueError(f'{name}/{height}: expected exactly 16 GPU frames')
            images=[Image.open(frame_path(row)).convert('RGBA').crop(crop) for row in rows]
            gif=ANIMATIONS/f'{name}_{height}.gif'
            make_gif(images,rows,name,height,capture['animation_lengths'][name],gif)
            outputs.append({'height':height,'gif':str(gif),'sha256':sha(gif),'frames':16})
            for slot,index in enumerate([0,2,4,6,8,10,12,15]):
                x=(slot%4)*tw;y=(group*2+slot//4)*(th+26)
                d.text((x+5,y+4),f'{name} {height}px | f{index+1:02} | {rows[index]["time"]:.3f}s',font=font(14),fill='black')
                sheet.paste(composite(images[index],(255,255,255) if slot%2==0 else (128,128,128)),(x,y+26))
        target=ANIMATIONS/f'{name}_combat_review.png';sheet.save(target)
        checks[name]={'status':'VISUAL_REVIEW_REQUIRED','sheet':str(target),'sha256':sha(target),'crop_only_no_resize':list(crop),'gifs':outputs}
        # Summary remains a native-scale strip: one actual frame per height.
        for height in [256,192]:
            row=next(r for r in selected if r['height']==height and r['frame']==(8 if name!='death' else 15))
            im=Image.open(frame_path(row)).convert('RGBA').crop(crop)
            summary_panels.append((name,height,composite(im)))
    width=sum(max(p[2].width for p in summary_panels if p[0]==n) for n in NAMES)
    rh=max(p[2].height for p in summary_panels)+32
    summary=Image.new('RGB',(width,rh*2),'#eceeea');d=ImageDraw.Draw(summary)
    x=0
    for name in NAMES:
        panels=[p for p in summary_panels if p[0]==name]
        for row,(_,height,im) in enumerate(panels):
            d.text((x+5,row*rh+5),f'{name} | {height}px',font=font(16),fill='black');summary.paste(im,(x,row*rh+30))
        x+=max(p[2].width for p in panels)
    summary.save(ROOT/'reports/cretan_archer/animation_combat_scale_review.png')
    comparison=reference_comparison(capture,crops)
    test=read(REPORT/'headless_tests.json')
    foot=foot_review(test) if test.get('foot_samples') else None
    manifest={'status':'VISUAL_REVIEW_REQUIRED','renderer':capture['renderer'],'source_capture_sha256':sha(REPORT/'capture_manifest.json'),'actual_gpu_frames_only':True,'native_size_preserved':True,'animations':checks,'walk_reference_comparison':str(comparison),'walk_foot_contact_debug':str(foot) if foot else None,'headless_status':test.get('status')}
    (REPORT/'animation_review_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps({'status':'REPORTS_GENERATED_REVIEW_REQUIRED','animations':list(checks),'frames_per_gif':16},indent=2))

if __name__=='__main__':main()
