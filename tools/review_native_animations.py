"""Assemble actual Godot frame captures at native scale, never synthesize motion."""
from rg_common import *

def main():
    capture=read('reports/native_rig_v2/capture_manifest.json');checks={};sheets=[]
    for name in ['idle','walk','attack_01','hit','death']:
        width=512 if name=='death' else 360
        columns=3
        row_height=442 if name=='death' else 370
        out=Image.new('RGB',(width*columns,row_height*4),'#edf0f2');d=ImageDraw.Draw(out)
        for row,height in enumerate([256,192]):
            frames=sorted([f for f in capture['frames'] if f['animation']==name and f['height']==height],key=lambda f:f['frame'])
            images=[Image.open(ROOT/f['path'].replace('res://','')).convert('RGB') for f in frames]
            palette_frames=[im.quantize(colors=256) for im in images]
            durations=[round(1000/15)]*len(images)
            if name not in ['walk','idle']:durations[-1]=1000
            gif=ROOT/f'reports/animations/{name}_{height}.gif'
            kwargs={'loop':0} if name in ['idle','walk'] else {}
            palette_frames[0].save(gif,save_all=True,append_images=palette_frames[1:],duration=durations,disposal=2,**kwargs)
            for col,index in enumerate(np.linspace(0,len(images)-1,6).round().astype(int)):
                x=(col%columns)*width;y=(row*2+col//columns)*row_height
                d.text((x+6,y+4),f'{name} / {height}px / t={frames[index]["time"]:.2f}',font=font(16),fill='black')
                crop=images[index].crop((0 if name=='death' else 100,0,512 if name=='death' else 460,420 if name=='death' else 350))
                out.paste(crop,(x,y+22))
        path=f'reports/animations/{name}_combat_review.png';out.save(ROOT/path)
        checks[name]={'status':'VISUAL_REVIEW_REQUIRED','sheet':path,'sha256':sha(path)}
    test=read('reports/native_rig_v2/headless_tests.json')
    out=Image.new('RGB',(1200,650),'white');d=ImageDraw.Draw(out)
    stride=read('resources/roman_guard_animations_v1.json')['walk']['root_motion_source_px_per_cycle']
    d.text((30,15),f'Walk support: Godot world positions / matched forward stride = {stride} source px',font=font(22),fill='black')
    colors={'near':'#db5b38','far':'#347bbb'}
    for side,basey in [('near',210),('far',460)]:
        rows=[r for r in test['foot_samples'] if r['side']==side];origin=next(r['world_position'] for r in rows if r['support'])
        points=[(70+r['time']*1040,basey-(r['world_position'][0]-origin[0])*.55) for r in rows]
        d.line(points,fill=colors[side],width=3);d.line((70,basey,1110,basey),fill='#333333',width=1)
        for r in rows:
            if r['support']:d.rectangle((70+r['time']*1040,basey+55,78+r['time']*1040,basey+70),fill='#5aaf70')
        d.text((30,basey-100),f'{side}: support green; world X (0.55x source px) | max support drift at 256px = {test["foot_slide"][side]["at_256px"]:.4f}px',font=font(18),fill=colors[side])
        d.text((70,basey+80),'0.0s                                      0.5s                                      1.0s',font=font(16),fill='black')
    out.save(ROOT/'reports/walk_foot_contact_debug.png')
    write('reports/native_rig_v2/animation_review_manifest.json',{'status':'VISUAL_REVIEW_REQUIRED','renderer':capture['renderer'],'animations':checks,'native_size':True,'source_capture_sha256':sha('reports/native_rig_v2/capture_manifest.json')})

if __name__=='__main__':main()
