"""Publish an explicitly recorded review; do not infer visual approval from tests."""
import shutil
from rg_common import *
import sys

def main():
    folder=(sys.argv[1].rstrip('/')+'/' if len(sys.argv)>1 else 'reports/walk_reference_v1/')
    metrics=read(folder+'walk_reference_metrics.json')
    review=read(folder+'visual_review.json')
    assert review['animation_source_sha256']==sha('resources/roman_guard_animations_v1.json')
    assert review['256px']=='PASS' and review['192px']=='PASS'
    metrics.update(status='PASS_WITH_QUALITY_RESERVATIONS',visual_review=review)
    if (ROOT/folder/'leg_chain_key_audit.json').exists():
        audit=read(folder+'leg_chain_key_audit.json')
        metrics['leg_chain_audit']={k:v for k,v in audit.items() if k!='samples'}
    write(folder+'walk_reference_metrics.json',metrics)
    capture=read(folder+'capture_manifest.json')
    current=read('reports/native_rig_v2/capture_manifest.json')
    current['frames']=[r for r in current['frames'] if r['animation']!='walk']
    for row in capture['frames']:
        destination=f'reports/animations/walk_{row["height"]}_{row["frame"]:03d}.png'
        shutil.copy2(ROOT/row['path'].replace('res://',''),ROOT/destination)
        current['frames'].append(dict(row,path='res://'+destination))
    write('reports/native_rig_v2/capture_manifest.json',current)
    for height in [256,192]:
        shutil.copy2(ROOT/metrics['outputs'][str(height)]['gif'],ROOT/f'reports/animations/walk_{height}.gif')
    shutil.copy2(ROOT/metrics['outputs']['256']['sheet'],ROOT/'reports/animations/walk_combat_review.png')
    for name in ['headless_tests.log','editor_import.log']:
        shutil.copy2(ROOT/folder/name,ROOT/'reports/native_rig_v2'/name)
    approval=read('reports/native_rig_v2/visual_approval.json')
    approval['animation_source_sha256']=sha('resources/roman_guard_animations_v1.json')
    approval['animations']['walk']={'status':'PASS','sheet_sha256':sha('reports/animations/walk_combat_review.png'),'note':review['scope']+' Naturalness remains subject to user review; no new user approval implied.','additional_192px_sheet':metrics['outputs']['192']['sheet']}
    write('reports/native_rig_v2/visual_approval.json',approval)
    manifest=read('reports/native_rig_v2/animation_review_manifest.json')
    manifest['animations']['walk']['sha256']=sha('reports/animations/walk_combat_review.png')
    manifest['source_capture_sha256']=sha('reports/native_rig_v2/capture_manifest.json')
    write('reports/native_rig_v2/animation_review_manifest.json',manifest)
    # Plot drift within each physically active support region. Changing the
    # contact vertex while rolling is not itself material-point movement.
    test=read(folder+'headless_tests.json')
    out=Image.new('RGB',(1200,680),'white');d=ImageDraw.Draw(out)
    d.text((25,15),'Walk reference: rolling sole contact / actual Godot world transforms',font=font(22),fill='black')
    d.text((25,50),'Green = stance. Colors identify successive planted material points. Errors shown at 256px.',font=font(16),fill='black')
    colors=['#555555','#bd6932','#447bb0','#619944','#995c9c']
    for side,basey in [('near',220),('far',490)]:
        rows=[r for r in test['foot_samples'] if r['side']==side and r['support']]
        d.line((70,basey,1110,basey),fill='#999999',width=1)
        d.text((25,basey-100),f'{side}: max material-point drift {test["foot_slide"][side]["at_256px"]:.4f}px',font=font(20),fill='black')
        for index in sorted({r['contact_index'] for r in rows}):
            group=[r for r in rows if r['contact_index']==index];anchor=np.array(group[0]['world_position'])
            points=[]
            for row in group:
                error=np.linalg.norm(np.array(row['world_position'])-anchor)*256/1435
                x=70+row['time']*1040;points.append((x,basey-error*600))
                d.rectangle((x,basey+25,x+8,basey+38),fill='#72b183')
            if len(points)>1:d.line(points,fill=colors[index],width=3)
            d.text((points[0][0],basey+43),f'contact {index}',font=font(12),fill=colors[index])
        d.text((70,basey+73),'0.0s                                      0.5s                                      1.0s',font=font(16),fill='black')
    out.save(ROOT/'reports/walk_foot_contact_debug.png')
    out.save(ROOT/folder/'walk_foot_contact_debug.png')
    print('Published reviewed Walk outputs; other animations retained')

if __name__=='__main__':main()
