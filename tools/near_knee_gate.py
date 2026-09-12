"""Scoped near-knee override; frozen V3 approvals remain bound to old evidence."""
from rg_common import *
from recompose_roman_guard import compose,render_config_digest
from near_knee_skinning import vertices_at

CHANGED={'leg_near_thigh','leg_near_shin','knee_near'}
BASE='reports/near_knee_baseline_v1.json'

def verify(m):
    errors=[]
    try:
        g=read('reports/near_knee_gate_v1.json');r=read('reports/near_knee_articulation_v1.json');b=read(BASE)
        if g.get('status')!='PASS' or not g.get('reviewer') or not g.get('notes'):errors.append('Near knee visual approval missing')
        checks={'plate_stable','anatomical_connection','plus20_no_dislocation','continuous_five_angles'}
        if set(g['combat_checks'])!={'256','192'} or any(set(c)!=checks or set(c.values())!={'PASS'} for c in g['combat_checks'].values()):errors.append('Five-angle combat review incomplete')
        for p,digest in g['evidence'].items():
            if sha(p)!=digest:errors.append('Near knee evidence changed: '+p)
        if r['angles']!=[-20,-10,0,10,20] or r['sizes']!=[256,192] or len(r['frames'])!=5:errors.append('Near knee cases incomplete')
        for p,digest in r['frames'].items():
            if sha(p)!=digest:errors.append('Near knee frame stale: '+p)
        if sha(body_source())!=b['file_hashes'][body_source()]:errors.append('Frozen body modified')
        original={p['name']:p for p in b['manifest']['parts']};current={p['name']:p for p in m['parts']}
        if set(current)!=set(PARTS)|{'knee_near'}:errors.append('Expected 19 core parts plus knee_near')
        changed_old={original[n]['file'] for n in CHANGED if n in original}
        for p,digest in b['file_hashes'].items():
            if p not in changed_old and sha(p)!=digest:errors.append('Frozen asset modified: '+p)
        for n,p in current.items():
            if n not in CHANGED and p!=original[n]:errors.append('Frozen part metadata modified: '+n)
        if {n:sha(p['file']) for n,p in current.items()}!=g['part_hashes']:errors.append('Formal part hashes stale')
        if m['draw_passes']!=r['draw_passes']:errors.append('Draw order changed')
        expected=[dict(d) for d in b['manifest']['draw_passes']]
        expected.insert(next(i for i,d in enumerate(expected) if d['part']=='foot_near')+1,{'part':'knee_near'})
        if m['draw_passes']!=expected:errors.append('Unrelated draw pass edit')
        body=rgba(body_source());a=np.array(body)[:,:,3]
        pm=np.array(mask(original['leg_near_thigh']['mask']))>0;sm=np.array(mask(original['leg_near_shin']['mask']))>0
        new={n:np.array(mask(current[n]['mask']))>0 for n in CHANGED};plate=new['knee_near']
        if not np.array_equal(new['leg_near_thigh'],pm&~plate) or not np.array_equal(new['leg_near_shin'],sm&~plate):errors.append('Overlap expanded or changed outside plate ownership')
        if np.any(plate&~(pm|sm)):errors.append('Plate pixels outside original near leg')
        for n in CHANGED:
            if not np.array_equal(np.array(rgba(current[n]['file'])),np.array(alpha_extract(body,mask(current[n]['mask'])))):errors.append('New pixels painted: '+n)
        oldimages={n:rgba(p['candidate_file']) for n,p in original.items()};images={n:rgba(p['file']) for n,p in current.items()}
        if not np.array_equal(np.array(compose(oldimages,b['manifest']['draw_passes'])),np.array(compose(images,m['draw_passes']))):errors.append('Rest pose changed; cannot inherit frozen tests')
        piv=read('assets/units/odyssey/roman_guard/roman_guard_pivots.json');expected_piv=json.loads(json.dumps(b['pivots']))
        expected_piv['parts']['leg_near_shin']['position']=r['pivot_new']
        expected_piv['joints']['near_knee']['position']=r['pivot_new']
        expected_piv['parts']['knee_near']={'anchor':'near_knee_socket','position':r['pivot_new'],'review_required':False,**r['knee_near_binding']}
        if piv!=expected_piv:errors.append('Unexpected pivot edit')
        if current['leg_near_shin']['pivot_hint']['position']!=r['pivot_new'] or current['knee_near']['pivot_hint']['position']!=r['pivot_new']:errors.append('Manifest pivot mismatch')
        if current['knee_near'].get('binding')!=r['knee_near_binding'] or r['knee_near_binding']['inherits_shin_rotation'] is not False:errors.append('Plate must not inherit shin swing')
        if current['leg_near_shin'].get('articulation_mesh')!=r['skinning_file'] or current['leg_near_shin'].get('rigid_sprite_rotation_approved') is not False:errors.append('Near shin must use reviewed local weights')
        mesh=read(r['skinning_file']);v=np.array(mesh['vertices']);tri=np.array(mesh['triangles'])
        def areas(v):
            a=v[tri[:,1]]-v[tri[:,0]];bb=v[tri[:,2]]-v[tri[:,0]];return a[:,0]*bb[:,1]-a[:,1]*bb[:,0]
        base=areas(v);weights=np.array(mesh['shin_weights'])
        if np.any(weights<0) or np.any(weights>1) or not np.allclose(weights+mesh['stationary_socket_weights'],1):errors.append('Invalid bone weights')
        for angle in r['angles']:
            if np.any(areas(vertices_at(mesh,angle))/base<=0):errors.append('Mesh inversion at '+str(angle))
        if sha(r['skinning_file'])!=r['skinning_sha256']:errors.append('Skinning mesh changed')
    except (FileNotFoundError,KeyError,ValueError,TypeError) as e:errors.append(str(e))
    return errors
