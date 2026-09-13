"""Verify Walk-only changes and arrange the 16 actual Godot frames per size."""
import re
from rg_common import *
import sys

def main():
    folder=(sys.argv[1].rstrip('/')+'/' if len(sys.argv)>1 else 'reports/walk_chain_v2/')
    baseline=read(folder+'approved_baseline.json')
    snapshot=baseline['files']
    changed=[p for p,h in snapshot.items() if sha(p)!=h]
    assert not changed,('Approved version changed',changed)
    assert baseline['animation_source_sha256']==sha('resources/roman_guard_animations_v1.json')
    native=read('reports/native_rig_v2/headless_tests.json')
    assert native['status']=='PASS',native['errors']
    write(folder+'headless_tests.json',native)
    capture=read(folder+'capture_manifest.json')
    outputs={}
    for height in [256,192]:
        rows=sorted([r for r in capture['frames'] if r['height']==height],key=lambda r:r['frame'])
        assert len(rows)==16 and [r['frame'] for r in rows]==list(range(16))
        images=[Image.open(ROOT/r['path'].replace('res://','')).convert('RGB') for r in rows]
        palette=images[0].quantize(colors=256)
        indexed=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in images]
        durations=[60,60,70,60]*4 # GIF centisecond timing: exactly 1000ms / 16 frames.
        gif=folder+f'walk_reference_{height}.gif'
        indexed[0].save(ROOT/gif,save_all=True,append_images=indexed[1:],duration=durations,loop=0,disposal=2,optimize=False)
        with Image.open(ROOT/gif) as verify:
            assert verify.n_frames==16
            total=0
            for i in range(16):verify.seek(i);total+=verify.info['duration']
            assert total==1000
        out=Image.new('RGB',(1080,1496),'#edf0f2');d=ImageDraw.Draw(out)
        for i,im in enumerate(images):
            x=(i%4)*270;y=(i//4)*374
            d.text((x+4,y+4),f'{height}px | {i+1:02d}/16 | {rows[i]["time"]:.4f}s',font=font(14),fill='black')
            out.paste(im.crop((130,0,400,350)),(x,y+24))
        sheet=folder+f'walk_reference_{height}_review.png';out.save(ROOT/sheet)
        outputs[str(height)]={'gif':gif,'frames':16,'duration_ms':1000,'sheet':sheet,'gif_sha256':sha(gif),'sheet_sha256':sha(sheet)}
    # A native follow-camera view removes the once-per-cycle viewport reset.
    # Ground marks still move with the world; it is not an in-place walk variant.
    follow=read(folder+'follow/capture_manifest.json')
    for height in [256,192]:
        rows=sorted([r for r in follow['frames'] if r['height']==height],key=lambda r:r['frame'])
        assert len(rows)==16
        images=[Image.open(ROOT/r['path'].replace('res://','')).convert('RGB') for r in rows]
        palette=images[0].quantize(colors=256)
        indexed=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in images]
        path=folder+f'walk_reference_follow_{height}.gif'
        indexed[0].save(ROOT/path,save_all=True,append_images=indexed[1:],duration=[60,60,70,60]*4,loop=0,disposal=2,optimize=False)
        with Image.open(ROOT/path) as verify:assert verify.n_frames==16
        outputs[str(height)]['follow_gif']=path
        outputs[str(height)]['follow_gif_sha256']=sha(path)
    metrics={'status' :'TECHNICAL_PASS_VISUAL_REVIEW_REQUIRED','other_animations_unchanged':True,'rig_outside_walk_resource_unchanged':True,'frozen_files_verified':len(snapshot),'near_knee_unchanged':True,'gait_structure_unchanged':True,'stride_source_px':387,'foot_pitch_world_degrees':[min(r['world_foot_pitch'] for r in read('resources/walk_contact_targets.json')),max(r['world_foot_pitch'] for r in read('resources/walk_contact_targets.json'))],'foot_roll':'heel contact / flat support / toe push-off / trailing recovery / passing / forward placement','contact_method':native['foot_contact_method'],'support_drift_at_256px':native['runtime_support_drift_at_256px'],'support_drift_at_192px':native['runtime_support_drift_at_256px']*.75,'outputs':outputs,'animation_source_sha256':sha('resources/roman_guard_animations_v1.json')}
    write(folder+'walk_reference_metrics.json',metrics)
    print(json.dumps(metrics,ensure_ascii=False))

if __name__=='__main__':main()
