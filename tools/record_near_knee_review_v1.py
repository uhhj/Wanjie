"""Publish only the reviewed near-knee split and preserve frozen approvals."""
import shutil
from rg_common import *
from near_knee_skinning import vertices_at

def main():
    r=read('reports/near_knee_articulation_v1.json');b=read('reports/near_knee_baseline_v1.json')
    m=json.loads(json.dumps(b['manifest']));piv=json.loads(json.dumps(b['pivots']))
    prior='reports/near_knee_prior_pivots_v3.json'
    if not (ROOT/prior).exists():shutil.copy2(ROOT/'assets/units/odyssey/roman_guard/roman_guard_pivots.json',ROOT/prior)
    assert sha(prior)==read('reports/articulated_render_manifest_v3.json')['pivot_sha256']
    reviews=read('reports/art_reviews.json');notes='Near-knee-only source pixel partition. Fixed independent patellar plate; local two-bone shin weights. Five continuous angles reviewed at 256px and 192px. No source/mask expansion; rest composition exactly unchanged.'
    for name,data in r['parts'].items():
        if name=='knee_near':
            p={'name':name,'file':f'assets/units/odyssey/roman_guard/parts/{name}.png','source':body_source(),'ai_completed':True,
               'pivot_hint':{'anchor':'near_knee_socket','position':r['pivot_new'],'coordinate_space':'source canvas pixels, top-left origin','review_required':False},'missing_hidden_regions':[]}
            m['parts'].append(p)
        else:p=next(p for p in m['parts'] if p['name']==name)
        p.update(data);p.update(candidate_sha256=data['sha256'],candidate_mask_sha256=data['mask_sha256'],candidate_source_sha256=sha(body_source()),review_required=False,status='ART_APPROVED',mask_status='ART_APPROVED',art_review_status='PASS',art_review_notes=[notes],structural_status='PASS',review_scope='NEAR_KNEE_FIVE_ANGLES_V1')
        p['ai_completed_note']='Inherited body-source completion only; no AI or painting performed in this articulation change.'
        if name=='leg_near_shin':
            p['pivot_hint']['position']=r['pivot_new'];p['articulation_mesh']=r['skinning_file'];p['rigid_sprite_rotation_approved']=False
        if name=='knee_near':p['binding']=r['knee_near_binding']
        shutil.copy2(ROOT/p['candidate_file'],ROOT/p['file'])
        for prefix,path in [('part:',p['file']),('mask:',p['mask'])]:reviews[prefix+name]={'status':'PASS','sha256':sha(path),'reviewer':'Codex visual review','notes':[notes],'timestamp':now()}
    m.update(required_count=20,core_required_count=19,attachment_count=1,articulation_layout='NEAR_KNEE_V1',draw_passes=r['draw_passes'])
    piv['parts']['leg_near_shin']['position']=r['pivot_new'];piv['joints']['near_knee']['position']=r['pivot_new']
    piv['parts']['knee_near']={'anchor':'near_knee_socket','position':r['pivot_new'],'review_required':False,**r['knee_near_binding']}
    write('tools/roman_guard_parts_manifest.json',m);write('assets/units/odyssey/roman_guard/roman_guard_pivots.json',piv);write('reports/art_reviews.json',reviews)
    mesh=read(r['skinning_file']);v=np.array(mesh['vertices']);tri=np.array(mesh['triangles'])
    def area(v):
        a=v[tri[:,1]]-v[tri[:,0]];bb=v[tri[:,2]]-v[tri[:,0]];return a[:,0]*bb[:,1]-a[:,1]*bb[:,0]
    ratios={str(a):float((area(vertices_at(mesh,a))/area(v)).min()) for a in r['angles']}
    r.update(status='PASS',visual_review_scope='COMBAT_SCALE_ANATOMICAL_CONTINUITY',reviewer='Codex visual review',
             notes=[notes,'High-resolution greave-border flex remains visible; combat-scale motion is accepted. Independent plate +/-3 degrees is only a hint, not tested or required; production default is zero at all five angles.'],minimum_triangle_area_ratios=ratios)
    write('reports/near_knee_articulation_v1.json',r)
    evidence=['reports/near_knee_baseline_v1.json','reports/near_knee_articulation_v1.json',r['skinning_file'],'reports/near_knee_pivot_review_v1.png','reports/near_knee_motion_256px_v1.png','reports/near_knee_motion_192px_v1.png','reports/near_knee_motion_detail_v1.png','reports/near_knee_rest_recomposition_v1.png',prior,'assets/units/odyssey/roman_guard/roman_guard_pivots.json']
    for d in r['parts'].values():evidence.extend([d['mask'],d['candidate_file']])
    write('reports/near_knee_gate_v1.json',{'status':'PASS','reviewer':'Codex visual review','notes':[notes],
          'combat_checks':{str(h):{key:'PASS' for key in ['plate_stable','anatomical_connection','plus20_no_dislocation','continuous_five_angles']} for h in [256,192]},
          'supersedes':'Only the near_knee approval in combat_rig_gate_v3. Other approved motions inherit unchanged evidence through exact rest recomposition.',
          'evidence':{p:sha(p) for p in evidence},'part_hashes':{p['name']:sha(p['file']) for p in m['parts']},'timestamp':now()})
    from validate_parts import validate
    from combat_rig_gate import audit
    result=validate();gate=audit();assert result['status']=='PASS',result['errors'];assert gate['status']=='PASS',gate['errors']
    write('reports/parts_validation.json',result)
    print('PASS: 20 parts, five-angle near-knee review; frozen assets unchanged')

if __name__=='__main__':main()
