"""Record the completed native-size visual review, retaining historical hires failures."""
from rg_common import *
from review_combat_scale import SOURCE

def main():
    render=read('reports/combat_scale_render_manifest.json')
    assert render['source_sha256']==sha(SOURCE)
    assert sha(SOURCE)=='df706ed02285e40b2532085d76e9936bba073eec0180e40bf63e94b35de26dfd', 'New source requires a new visual review'
    assert sha(render['review_image'])=='db331f77fb4fc6df4bc1554a4dce1225cc8a8f7a4d45166380dca7dbeeeba0cb', 'New rendered pixels require a new visual review'
    keys=['no_obvious_halo','continuous_silhouette','no_visible_plume_specks','natural_shoulder','natural_greaves','no_floating_sole_chunks','no_isolated_noise_over_one_display_pixel','identity_structure_transparency_normal']
    gate={'gate_id':'COMBAT_SCALE_VISUAL_GATE_V1','status':'PASS_WITH_NON_BLOCKING_HIRES_EDGE_ARTIFACTS','scope':'COMBAT_RIG_ASSET','source':SOURCE,'source_sha256':sha(SOURCE),'combat_scale_visual_review':'PASS','hires_pixel_review':'NON_BLOCKING_COMBAT_ARTIFACT','historical_hires_result':'FAIL_LOCAL_TOUCHUP_ONLY','historical_evidence':'reports/complete_body_gate_v3.json','visual_checks':{str(h):{k:'PASS' for k in keys} for h in (256,192,128)},'reviewer':'Codex visual inspection of native 660x830 sheet','notes':'Reviewed all six native-size white/gray composites. Dark outlines are continuous and intentional; no conspicuous detached dots, sole blocks or halo at target heights. No zoomed source-pixel defects used to fail this combat review. Battlefield image unavailable.','render_manifest_sha256':sha('reports/combat_scale_render_manifest.json'),'manual_alpha_touchup':'STOPPED_PER_USER_COMBAT_POLICY','format_integrity_evidence':'reports/alpha_cleanup_integrity_v2.json','timestamp':now()}
    write('reports/complete_body_gate_combat_v1.json',gate)
    write('reports/combat_scale_visual_gate_v1.json',{**gate,'status':'PASS','complete_body_gate':gate['status']})
    reviews=read('reports/art_reviews.json')
    reviews['complete_body_combat']={'status':'PASS','file':SOURCE,'sha256':sha(SOURCE),'reviewer':gate['reviewer'],'notes':gate['notes'],'qualification':gate['status'],'timestamp':now()}
    write('reports/art_reviews.json',reviews)
    targets=read('reports/alpha_manual_touchup_targets_v2.json')
    targets.setdefault('historical_status',targets['status']); targets['status']='NON_BLOCKING_COMBAT_ARTIFACT'
    for t in targets['targets']:
        t['combat_classification']='NON_BLOCKING_COMBAT_ARTIFACT'; t['current_action']='NO_TOUCHUP'
    targets['superseding_acceptance']='reports/combat_scale_visual_gate_v1.json'
    write('reports/alpha_manual_touchup_targets_v2.json',targets)
    c=config(); c['complete_body_source']=SOURCE; c['complete_body_gate']='reports/complete_body_gate_combat_v1.json'; write('tools/pipeline_config.json',c)
    assert body_review_ok()

if __name__=='__main__': main()
