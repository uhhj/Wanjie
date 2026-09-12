"""Regression tests on isolated copies of actual approved V3 evidence."""
import shutil,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import rg_common as c
import combat_rig_gate as gate
import sword_completion as sword

class ArticulatedGateTests(unittest.TestCase):
    def setUp(self):
        original=c.ROOT;r=c.read('reports/articulated_render_manifest_v3.json');g=c.read('reports/combat_rig_gate_v3.json');m=c.read('tools/roman_guard_parts_manifest.json');cr=c.read('reports/combat_scale_render_manifest.json')
        folder=original/'work/test_runs';folder.mkdir(exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(prefix='articulated_v3_',dir=folder);self.root=Path(self.temp.name)
        files={'tools/pipeline_config.json','tools/roman_guard_parts_manifest.json','reports/articulated_render_manifest_v3.json','reports/combat_rig_gate_v3.json','reports/art_reviews.json','reports/complete_body_gate_combat_v1.json','reports/combat_scale_render_manifest.json',c.body_source(),cr['review_image'],'assets/units/odyssey/roman_guard/roman_guard_pivots.json'}
        files.update(r['review_images']);files.update(r['full_frames']);files.update(g['extra_evidence'])
        for row in cr['rows']:files.update(x['file'] for x in row['composites'])
        for p in m['parts']:files.update([p['file'],p['mask']])
        files.update(d['clip_mask'] for d in m['draw_passes'] if d.get('clip_mask'))
        sp=next(p for p in m['parts'] if p['name']=='sword');recipe=c.read(sp['completion_recipe'])
        files.update(recipe[k] for k in ['original','generated_reference','grip_mask','remove_mask'])
        for file in files:
            dst=self.root/file;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(original/file,dst)
        self.patchers=[patch.object(c,'ROOT',self.root),patch.object(sword,'ROOT',self.root)]
        for p in self.patchers:p.start()
        self.assertEqual(gate.audit()['status'],'PASS')
    def tearDown(self):
        for p in reversed(self.patchers):p.stop()
        self.temp.cleanup()
    def test_current_evidence_passes(self):self.assertEqual(gate.audit()['status'],'PASS')
    def test_pivot_change_revokes_ready(self):
        p=self.root/'assets/units/odyssey/roman_guard/roman_guard_pivots.json';p.write_bytes(p.read_bytes()+b' ')
        self.assertEqual(gate.audit()['status'],'FAIL')
    def test_native_preview_change_revokes_ready(self):
        p=self.root/'reports/joint_rotation_combat_scale_v3.png';p.write_bytes(p.read_bytes()+b'changed')
        self.assertEqual(gate.audit()['status'],'FAIL')
    def test_empty_recomposition_checks_cannot_pass(self):
        g=c.read('reports/combat_rig_gate_v3.json');g['recomposition']['combat_checks']={};c.write('reports/combat_rig_gate_v3.json',g)
        self.assertEqual(gate.audit('recomposition')['status'],'FAIL')
    def test_missing_sword_approval_blocks_ready(self):
        g=c.read('reports/combat_rig_gate_v3.json');g['full_sword']['status']='PENDING';c.write('reports/combat_rig_gate_v3.json',g)
        self.assertEqual(gate.audit()['status'],'FAIL')
    def test_formal_texture_change_revokes_ready(self):
        p=self.root/'assets/units/odyssey/roman_guard/parts/leg_far_shin.png';p.write_bytes(p.read_bytes()+b'changed')
        self.assertEqual(gate.audit()['status'],'FAIL')
    def test_rehashed_blade_edit_still_fails_provenance(self):
        p=next(p for p in c.read('tools/roman_guard_parts_manifest.json')['parts'] if p['name']=='sword')
        a=c.np.array(c.rgba(p['file']));ys,xs=c.np.where((a[:,:,3]>0)&(c.np.indices(a.shape[:2])[0]>1000));a[ys[0],xs[0],0]^=1
        c.Image.fromarray(a).save(self.root/p['file'])
        recipe=c.read(p['completion_recipe']);recipe['output_sha256']=c.sha(p['file']);c.write(p['completion_recipe'],recipe);p['completion_recipe_sha256']=c.sha(p['completion_recipe'])
        with self.assertRaisesRegex(ValueError,'exact recorded'):sword.validate_completion(p,p['file'])

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ArticulatedGateTests))
    c.write('reports/articulated_gate_tool_tests_v3.json',{'status':'PASS' if result.wasSuccessful() else 'FAIL','tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'timestamp':c.now()})
    raise SystemExit(0 if result.wasSuccessful() else 1)
