"""Exercise real candidate textures without bypassing formal approval or Godot gates."""
from rg_common import *
from recompose_roman_guard import compose, comparison, render_config_digest
from generate_joint_rotation_test import transform, joint_diagnostic
from cleanup_roman_guard_alpha_v2 import components

def combat_tile(im, height=256):
    scale=height/(rgba(body_source()).getchannel('A').getbbox()[3]-rgba(body_source()).getchannel('A').getbbox()[1])
    size=(round(im.width*scale),round(im.height*scale))
    small=im.convert('RGBa').resize(size,Image.Resampling.LANCZOS).convert('RGBA')
    out=Image.new('RGBA',small.size,'white'); out.alpha_composite(small)
    return out.convert('RGB')

def contact(items,path,columns=3):
    tilew,tileh=350,330
    out=Image.new('RGB',(columns*tilew,((len(items)+columns-1)//columns)*tileh),'#ededed'); d=ImageDraw.Draw(out)
    for i,(label,im) in enumerate(items):
        x=i%columns*tilew; y=i//columns*tileh
        d.text((x+8,y+6),label,font=font(15),fill='black')
        tile=combat_tile(im); out.paste(tile,(x+(tilew-tile.width)//2,y+42))
    out.save(ROOT/path)

def main():
    assert body_review_ok()
    m=read('tools/roman_guard_parts_manifest.json'); piv=read('assets/units/odyssey/roman_guard/roman_guard_pivots.json')
    images={p['name']:rgba(p['candidate_file']) for p in m['parts']}; checks=[]
    for p in m['parts']:
        im=images[p['name']]; a=np.array(im)[:,:,3]
        expected=alpha_extract(rgba(p['source']),mask(p['mask']))
        exact=np.array_equal(np.array(expected),np.array(im))
        _,comps=components(a>32)
        sizes=sorted((v['area'] for v in comps.values()),reverse=True)
        assert p['candidate_source_sha256']==sha(p['source']) and p['candidate_mask_sha256']==sha(p['mask'])
        assert p['candidate_sha256']==sha(p['candidate_file']) and exact
        checks.append({'name':p['name'],'status':'FORMAT_PASS_ART_REVIEW_REQUIRED','file':p['candidate_file'],'sha256':sha(p['candidate_file']),'canvas':list(im.size),'mode':im.mode,'bbox':im.getchannel('A').getbbox(),'nonzero_alpha_pixels':int((a>0).sum()),'exact_source_mask_extraction':exact,'connected_component_areas_gt_32_alpha':sizes,'missing_hidden_regions':p['missing_hidden_regions']})
    write('reports/parts_candidate_validation_v2.json',{'status':'FORMAT_PASS_ART_REVIEW_REQUIRED','required':19,'generated':len(checks),'missing':0,'formal_approved':0,'source':body_source(),'source_sha256':sha(body_source()),'parts':checks,'timestamp':now()})
    result=compose(images,m['draw_passes']); result.save(ROOT/'reports/roman_guard_recomposed_v2.png')
    metrics,thresholds,automatic,diff=comparison(check_source(),result); diff.save(ROOT/'reports/recomposition_diff_v2.png')
    bodypasses=[d for d in m['draw_passes'] if d['part'] not in EQUIPMENT]
    body=compose(images,bodypasses); original=rgba(body_source())
    ba=np.array(body); oa=np.array(original)
    delta=int(np.count_nonzero(np.any(ba!=oa,axis=2)))
    alpha_changed=int(np.count_nonzero(ba[:,:,3]!=oa[:,:,3]))
    visible_rgb_changed=int(np.count_nonzero(np.any(ba[:,:,:3]!=oa[:,:,:3],axis=2)&(oa[:,:,3]>0)))
    contact([('RIG MASTER / reference',check_source()),('RECOMPOSED / candidates',result),('BODY PARTS / rest pose',body)],'reports/recomposition_combat_review_v2.png')
    write('reports/recomposition_metrics_v2.json',{'status':'REVIEW_REQUIRED' if automatic else 'FAIL','scope':'CANDIDATES_ONLY_NOT_FORMAL','automatic_checks_passed':automatic,'metrics':metrics,'thresholds':thresholds,'body_reassembly_changed_rgba_pixels_including_invisible_rgb':delta,'body_reassembly_alpha_changed_pixels':alpha_changed,'body_reassembly_visible_rgb_changed_pixels':visible_rgb_changed,'transparent_rgb_note':'Part extraction zeros RGB where alpha=0; these invisible RGB differences are not appearance drift.','output_sha256':sha('reports/roman_guard_recomposed_v2.png'),'part_hashes':{p['name']:sha(p['candidate_file']) for p in m['parts']},'render_config_sha256':render_config_digest(m),'timestamp':now()})
    items=[]; results=[]
    cases=[('near elbow','near_elbow','arm_near_upper','arm_near_fore',['arm_near_fore','hand_near']),('far elbow','far_elbow','arm_far_upper','arm_far_fore',['arm_far_fore','hand_far']),('near knee','near_knee','leg_near_thigh','leg_near_shin',['leg_near_shin','foot_near']),('far knee','far_knee','leg_far_thigh','leg_far_shin',['leg_far_shin','foot_far'])]
    details=[]
    for title,key,parent,child,desc in cases:
        hint=piv['joints'][key]; pivot=hint['position']; diameter=hint['diameter_hint_px']
        for angle in (-20,0,20):
            changed={**images}
            for name in desc: changed[name]=transform(images[name],pivot,angle)
            parent_pivot=piv['parts'][parent]['position']; axis=[pivot[0]-parent_pivot[0],pivot[1]-parent_pivot[1]]
            diagnostic=joint_diagnostic(images[parent],images[child],changed[child],pivot,diameter,axis,angle==0)
            frame=compose(changed,bodypasses)
            items.append((f'{title} {angle:+d} / body only',frame))
            crop=preview(frame).crop((pivot[0]-120,pivot[1]-120,pivot[0]+120,pivot[1]+120))
            details.append((f'{title} {angle:+d}',crop))
            results.append({'joint':key,'angle_deg':angle,'moved_parts':desc,**diagnostic})
    for name,cases in [('shield',[(-7,(-8,0)),(0,(0,0)),(7,(8,-5))]),('sword',[(0,(0,0)),(20,(18,-5)),(30,(25,-7))])]:
        for angle,translation in cases:
            changed={**images}; changed[name]=transform(images[name],piv['parts'][name]['position'],angle,translation)
            items.append((f'{name} {angle:+d} move {translation}',compose(changed,m['draw_passes'])))
            pad=max(config()['canvas']); base=images[name]
            large=Image.new('RGBA',(base.width+pad*2,base.height+pad*2)); large.paste(base,(pad,pad))
            point=piv['parts'][name]['position']
            moved=transform(large,(point[0]+pad,point[1]+pad),angle,translation)
            all_alpha=np.array(moved.getchannel('A'))
            total=int(all_alpha.sum()); kept=int(all_alpha[pad:pad+base.height,pad:pad+base.width].sum())
            clipped=(total-kept)/max(1,total)
            results.append({'joint':name,'angle_deg':angle,'translation_px':translation,'moved_parts':[name],'clipped_alpha_fraction':clipped,'automatic_status':'FAIL' if clipped>=.001 else 'PASS','note':'Padded transform detects preview canvas clipping separately from texture completeness; grip alignment still requires visual review.'})
    contact(items,'reports/joint_rotation_test_v2.png')
    sheet(details,'reports/joint_rotation_detail_v2.png',3,(240,240))
    write('reports/joint_rotation_metrics_v2.json',{'status':'FAIL' if any(t['automatic_status']=='FAIL' for t in results) else 'REVIEW_REQUIRED','scope':'CANDIDATES_ONLY_NOT_FORMAL','tests':results,'output_sha256':sha('reports/joint_rotation_test_v2.png'),'part_hashes':{p['name']:sha(p['candidate_file']) for p in m['parts']},'pivot_config_sha256':sha('assets/units/odyssey/roman_guard/roman_guard_pivots.json'),'body_joints_rendered_without_equipment':True,'timestamp':now()})
    print('19 candidates validated; recomposition and all 18 motion cases rendered for review.')

if __name__=='__main__': main()
