"""Read-only negative tests for the scoped near-knee acceptance."""
import copy,unittest
from unittest.mock import patch
import near_knee_gate as gate
from rg_common import *

class NearKneeTests(unittest.TestCase):
    def setUp(self):self.m=read('tools/roman_guard_parts_manifest.json')
    def test_current_pass(self):self.assertEqual(gate.verify(self.m),[])
    def test_plate_shin_parent_rejected(self):
        next(p for p in self.m['parts'] if p['name']=='knee_near')['binding']['inherits_shin_rotation']=True
        self.assertIn('Plate must not inherit shin swing',gate.verify(self.m))
    def test_rigid_shin_rejected(self):
        next(p for p in self.m['parts'] if p['name']=='leg_near_shin')['rigid_sprite_rotation_approved']=True
        self.assertIn('Near shin must use reviewed local weights',gate.verify(self.m))
    def test_frozen_sword_change_rejected(self):
        original=gate.sha
        with patch.object(gate,'sha',side_effect=lambda p:'changed' if p.endswith('/parts/sword.png') else original(p)):
            self.assertTrue(any('Frozen asset modified' in e for e in gate.verify(self.m)))
    def test_five_angle_review_required(self):
        original=gate.read
        def changed(p):
            d=original(p)
            if p=='reports/near_knee_gate_v1.json':d['combat_checks']['256']['plus20_no_dislocation']='FAIL'
            return d
        with patch.object(gate,'read',side_effect=changed):self.assertIn('Five-angle combat review incomplete',gate.verify(self.m))
    def test_no_expanded_overlap(self):
        original=gate.mask;part=next(p for p in self.m['parts'] if p['name']=='leg_near_shin')
        def changed(p):
            im=original(p)
            if p==part['mask']:im.putpixel((1,1),255)
            return im
        with patch.object(gate,'mask',side_effect=changed):self.assertIn('Overlap expanded or changed outside plate ownership',gate.verify(self.m))
    def test_other_pivot_change_rejected(self):
        original=gate.read
        def changed(p):
            d=original(p)
            if p.endswith('roman_guard_pivots.json'):d['joints']['far_knee']['position'][0]+=1
            return d
        with patch.object(gate,'read',side_effect=changed):self.assertIn('Unexpected pivot edit',gate.verify(self.m))

if __name__=='__main__':
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(NearKneeTests))
    write('reports/near_knee_validation_tests_v1.json',{'status':'PASS' if r.wasSuccessful() else 'FAIL','tests_run':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'timestamp':now()})
    raise SystemExit(0 if r.wasSuccessful() else 1)
