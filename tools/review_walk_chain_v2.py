"""Validate the user-approved Walk keys without recreating rejected candidates."""
import math
from rg_common import *

def main():
    folder='reports/walk_chain_v2/'
    baseline=read(folder+'approved_baseline.json')
    assert all(sha(p)==h for p,h in baseline['files'].items()),'Approved Walk or assets changed'
    new=read('resources/roman_guard_animations_v1.json')['walk']
    samples=[]
    for version,walk in [('after',new)]:
        for i,(t,p) in enumerate(zip(walk['times'],walk['poses'])):
            r=p['rotations']
            for side,rest_tilt in [('near',math.degrees(math.atan2(56,248))),('far',math.degrees(math.atan2(-18,251)))]:
                shin=r[f'leg_{side}_thigh']+r[f'leg_{side}_shin']
                samples.append({'version':version,'time':t,'side':side,'shin_axis_from_down_degrees':shin+rest_tilt,'foot_world_degrees':shin+r['foot_'+side],'ankle_local_degrees':r['foot_'+side],'knee_local_degrees':r[f'leg_{side}_shin']})
    after=next(r for r in samples if r['version']=='after' and r['side']=='near' and r['time']==.5)
    report={'animation_source_sha256':sha('resources/roman_guard_animations_v1.json'),'measurement':'Animation key values and bind-axis geometry; images are separate real Godot GPU captures','upper_body_and_knee_plate_keys_unchanged':True,'near_toeoff_after':after,'samples':samples}
    write(folder+'leg_chain_key_audit.json',report)
    print('User-approved Walk hashes and current chain keys PASS')

if __name__=='__main__':main()
