"""Hash invalidation and scope regression tests; copied evidence stays in test_runs."""
import shutil,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import rg_common as c

class CombatGateTests(unittest.TestCase):
    def setUp(self):
        self.original=c.ROOT
        folder=self.original/'work/test_runs'; folder.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(prefix='combat_gate_',dir=folder); self.root=Path(self.temp.name)
        render=c.read('reports/combat_scale_render_manifest.json')
        files=['tools/pipeline_config.json','reports/complete_body_gate_combat_v1.json','reports/combat_scale_render_manifest.json','reports/art_reviews.json',c.body_source(),render['review_image']]
        files += [p['file'] for row in render['rows'] for p in row['composites']]
        for file in files:
            dest=self.root/file; dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(self.original/file,dest)
        self.patcher=patch.object(c,'ROOT',self.root); self.patcher.start()
        self.assertTrue(c.body_review_ok())
    def tearDown(self):
        self.patcher.stop(); self.temp.cleanup()
    def test_source_change_revokes_body_acceptance(self):
        p=self.root/c.body_source(); p.write_bytes(p.read_bytes()+b'changed')
        self.assertFalse(c.body_review_ok())
    def test_review_image_change_revokes_acceptance(self):
        p=self.root/'reports/combat_scale_visual_review.png'; p.write_bytes(p.read_bytes()+b'changed')
        self.assertFalse(c.body_review_ok())
    def test_individual_scale_change_revokes_acceptance(self):
        p=self.root/'reports/combat_scale/body_192_white.png'; p.write_bytes(p.read_bytes()+b'changed')
        self.assertFalse(c.body_review_ok())
    def test_empty_visual_checks_cannot_pass(self):
        gate=c.read('reports/complete_body_gate_combat_v1.json'); gate['visual_checks']={}
        c.write('reports/complete_body_gate_combat_v1.json',gate); self.assertFalse(c.body_review_ok())
    def test_artwork_scope_cannot_use_combat_exception(self):
        gate=c.read('reports/complete_body_gate_combat_v1.json'); gate['scope']='CODEX_ARTWORK'
        c.write('reports/complete_body_gate_combat_v1.json',gate); self.assertFalse(c.body_review_ok())
    def test_qualified_part_approval_still_rejected(self):
        reviews=c.read('reports/art_reviews.json'); reviews['part:head']={**reviews['complete_body_combat'],'status':'PASS_WITH_NON_BLOCKING_HIRES_EDGE_ARTIFACTS'}
        c.write('reports/art_reviews.json',reviews)
        self.assertFalse(c.review_ok('part:head',c.body_source()))

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(CombatGateTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    c.write('reports/combat_gate_tool_tests.json',{'status':'PASS' if result.wasSuccessful() else 'FAIL','tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'scope':'Acceptance invalidation and scope isolation; not art approval','timestamp':c.now()})
    raise SystemExit(0 if result.wasSuccessful() else 1)
