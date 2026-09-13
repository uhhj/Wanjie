"""Compare actual GPU frames and audit the keyed thigh/calf/foot relationship."""
import math
from rg_common import *

def main():
    folder='reports/walk_chain_v2/'
    old=read(folder+'before_roman_guard_animations_v1.json')['walk']
    new=read('resources/roman_guard_animations_v1.json')['walk']
    leg_keys={f'{part}_{side}{tail}' for side in ['near','far'] for part,tail in [('leg','_thigh'),('leg','_shin'),('foot','')]}
    for a,b in zip(old['poses'],new['poses']):
        assert all(a['rotations'][k]==b['rotations'][k] for k in a['rotations'] if k not in leg_keys)
        assert all(a[k]==b[k] for k in a if k not in ['rotations','hip_offsets'])
    samples=[]
    for version,walk in [('before',old),('after',new)]:
        for i,(t,p) in enumerate(zip(walk['times'],walk['poses'])):
            r=p['rotations']
            for side,rest_tilt in [('near',math.degrees(math.atan2(56,248))),('far',math.degrees(math.atan2(-18,251)))]:
                shin=r[f'leg_{side}_thigh']+r[f'leg_{side}_shin']
                samples.append({'version':version,'time':t,'side':side,'shin_axis_from_down_degrees':shin+rest_tilt,'foot_world_degrees':shin+r['foot_'+side],'ankle_local_degrees':r['foot_'+side],'knee_local_degrees':r[f'leg_{side}_shin']})
    before=next(r for r in samples if r['version']=='before' and r['side']=='near' and r['time']==.5)
    after=next(r for r in samples if r['version']=='after' and r['side']=='near' and r['time']==.5)
    report={'animation_source_sha256':sha('resources/roman_guard_animations_v1.json'),'measurement':'Animation key values and bind-axis geometry; images are separate real Godot GPU captures','upper_body_and_knee_plate_keys_unchanged':True,'near_toeoff_before':before,'near_toeoff_after':after,'samples':samples}
    write(folder+'leg_chain_key_audit.json',report)
    indices=[5,7,8,9,10,12]
    out=Image.new('RGB',(1320,750),'#edf0f2');d=ImageDraw.Draw(out)
    for row,version,base in [(0,'BEFORE','reports/walk_reference_v1/follow'),(1,'AFTER','reports/walk_chain_v2/follow')]:
        for col,index in enumerate(indices):
            x=col*220;y=row*375;t=index/16
            im=Image.open(ROOT/f'{base}/walk_256_{index:03d}.png').convert('RGB')
            d.text((x+5,y+5),f'{version} / {t:.4f}s / 256px',font=font(14),fill='black')
            out.paste(im.crop((130,0,350,330)),(x,y+22))
            key=next(r for r in samples if r['version']==('before' if row==0 else 'after') and r['side']=='near' and abs(r['time']-t)<1e-6)
            d.text((x+5,y+353),f'Shin {key["shin_axis_from_down_degrees"]:+.1f} / Foot {key["foot_world_degrees"]:+.1f}',font=font(13),fill='#333333')
    out.save(ROOT/folder/'lower_leg_before_after_256.png')
    print('Upper body and knee-plate keys unchanged; near toe-off ankle %.2f -> %.2f degrees' %(before['ankle_local_degrees'],after['ankle_local_degrees']))

if __name__=='__main__':main()
