"""Small independent tests for connectivity and rejection of fake/damaged RGBA."""
import unittest,tempfile
from pathlib import Path
from collections import deque
import numpy as np
from PIL import Image
from convert_roman_guard_rgba import edge_connected
from validate_rgba_candidate import validate
from rg_common import ROOT,write,now


def reference_bfs(mask):
    h,w=mask.shape;seen=np.zeros_like(mask);q=deque()
    for y in range(h):
        for x in range(w):
            if (x in (0,w-1) or y in (0,h-1)) and mask[y,x]:
                q.append((y,x));seen[y,x]=True
    while q:
        y,x=q.popleft()
        for ny,nx in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
            if 0<=ny<h and 0<=nx<w and mask[ny,nx] and not seen[ny,nx]:
                seen[ny,nx]=True;q.append((ny,nx))
    return seen


class ConnectivityTests(unittest.TestCase):
    def test_matches_independent_bfs(self):
        rng=np.random.default_rng(327)
        for _ in range(30):
            mask=rng.random((21,29))<.55
            self.assertTrue(np.array_equal(edge_connected(mask),reference_bfs(mask)))

    def test_diagonal_is_not_a_connection(self):
        mask=np.eye(5,dtype=bool)
        actual=edge_connected(mask)
        self.assertTrue(actual[0,0] and actual[4,4])
        self.assertFalse(actual[2,2])


class CandidateTests(unittest.TestCase):
    def setUp(self):
        base=ROOT/'work/test_runs';base.mkdir(parents=True,exist_ok=True)
        self.tmp=tempfile.TemporaryDirectory(dir=base)
        self.folder=Path(self.tmp.name)
        self.rgb=np.zeros((20,20,3),dtype=np.uint8)
        self.rgb[4:16,4:16]=180
        self.rgb[8:12,8:12]=0
        self.rgba=np.dstack([self.rgb,np.where(edge_connected(self.rgb.max(2)<=2),0,255).astype(np.uint8)])
        self.source=self.folder/'source.png';self.output=self.folder/'output.png'
        Image.fromarray(self.rgb).save(self.source)

    def tearDown(self):self.tmp.cleanup()

    def result(self):
        Image.fromarray(self.rgba).save(self.output)
        return validate(self.source,self.output)

    def test_real_transparency_preserves_internal_black(self):
        r=self.result();self.assertEqual(r['status'],'PASS')
        self.assertEqual(r['disconnected_dark_pixels_preserved'],16)
        self.assertEqual(self.rgba[9,9,3],255)

    def test_reject_all_opaque(self):
        self.rgba[:,:,3]=255
        self.assertEqual(self.result()['status'],'FAIL')

    def test_reject_all_transparent(self):
        self.rgba[:,:,3]=0
        self.assertEqual(self.result()['status'],'FAIL')

    def test_reject_internal_shadow_deleted(self):
        self.rgba[8:12,8:12,3]=0
        self.assertEqual(self.result()['status'],'FAIL')

    def test_reject_rgb_modified(self):
        self.rgba[5,5,0]=99
        self.assertEqual(self.result()['status'],'FAIL')

    def test_reject_canvas_change(self):
        self.rgba=self.rgba[:-1]
        self.assertEqual(self.result()['status'],'FAIL')

    def test_reject_border_foreground(self):
        self.rgba[0,0,3]=255
        self.assertEqual(self.result()['status'],'FAIL')

    def test_reject_rgb_and_missing_file(self):
        self.assertEqual(validate(self.source,self.output)['status'],'FAIL')
        self.output.write_bytes(b'not a PNG file')
        self.assertEqual(validate(self.source,self.output)['status'],'FAIL')
        Image.fromarray(self.rgb).save(self.output)
        self.assertEqual(validate(self.source,self.output)['status'],'FAIL')


if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromModule(__import__(__name__))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    write('reports/rgba_tool_tests.json',{'status':'PASS' if result.wasSuccessful() else 'FAIL',
          'count':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
          'timestamp':now(),'scope':'Algorithm/validator tests only; does not approve character Alpha matte.'})
    raise SystemExit(0 if result.wasSuccessful() else 1)
