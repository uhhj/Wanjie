"""Independent geometry checks and immutable-interior tests; not an art gate."""
import unittest
from collections import deque
import numpy as np
from PIL import Image
from rg_common import ROOT,read,write,now,sha
from cleanup_roman_guard_alpha_v2 import morph,nearest,components,estimate,RGB,INITIAL,OUTPUT,RGB_SHA,INITIAL_SHA


class GeometryTests(unittest.TestCase):
    def test_disk_morphology(self):
        m=np.zeros((11,11),bool);m[5,5]=True
        yy,xx=np.indices(m.shape)
        self.assertTrue(np.array_equal(morph(m,3,True),(yy-5)**2+(xx-5)**2<=9))
        solid=np.ones((11,11),bool)
        self.assertEqual(int(morph(solid,2,False).sum()),49)

    def test_euclidean_distance_matches_brute_force(self):
        m=np.zeros((11,13),bool);m[2,3]=True;m[8,9]=True
        ys=np.array([0,5,9]);xs=np.array([7,2,10]);d,ry,rx=nearest(m,ys,xs,12)
        sites=np.argwhere(m)
        for i,(y,x) in enumerate(zip(ys,xs)):
            expected=np.min(np.sum((sites-[y,x])**2,axis=1))**.5
            self.assertAlmostEqual(d[i],expected);self.assertTrue(m[ry[i],rx[i]])

    def test_components_match_independent_eight_neighbor_bfs(self):
        rng=np.random.default_rng(458)
        for _ in range(12):
            m=rng.random((19,23))<.3;seen=np.zeros_like(m);sizes=[]
            for y,x in np.argwhere(m):
                if seen[y,x]:continue
                seen[y,x]=True;q=deque([(y,x)]);count=0
                while q:
                    yy,xx=q.popleft();count+=1
                    for dy in [-1,0,1]:
                        for dx in [-1,0,1]:
                            ny,nx=yy+dy,xx+dx
                            if 0<=ny<m.shape[0] and 0<=nx<m.shape[1] and m[ny,nx] and not seen[ny,nx]:
                                seen[ny,nx]=True;q.append((ny,nx))
                sizes.append(count)
            labels,info=components(m)
            self.assertEqual(sorted(sizes),sorted(x['area'] for x in info.values()))
            self.assertTrue(np.array_equal(labels>0,m))


class MatteTests(unittest.TestCase):
    def setUp(self):
        self.rgb=np.zeros((64,64,3),np.uint8);self.m=np.zeros((64,64),np.uint8)
        self.rgb[20:50,20:50]=[140,80,30];self.m[20:50,20:50]=255
        self.rgb[20,20:50]=[40,22,9]
        self.rgb[30:34,30:34]=[2,2,2]

    def test_fixed_interior_and_fractional_only_rgb_changes(self):
        clean,trimap,sf,unknown,*_=estimate(self.rgb,self.m)
        delta=np.any(clean[:,:,:3]!=self.rgb,axis=2);a=clean[:,:,3]
        self.assertTrue(np.all(a[sf]==255));self.assertTrue(np.all(a[trimap==0]==0))
        self.assertFalse(np.any(delta[sf]));self.assertFalse(np.any(delta&~unknown))
        self.assertFalse(np.any(delta&(a==255)));self.assertFalse(np.any(delta&(a==0)))
        self.assertTrue(np.any((a>0)&(a<255)));self.assertTrue(np.all(a[30:34,30:34]==255))

    def test_distant_dark_speck_removed_near_speck_reviewed(self):
        self.m[2,2]=255;self.rgb[2,2]=[5,5,5]
        self.m[18,25]=255;self.rgb[18,25]=[5,5,5]
        clean,*other=estimate(self.rgb,self.m);stats=other[-2]
        self.assertEqual(stats['components_removed'],1);self.assertEqual(stats['pixels_removed'],1)
        self.assertEqual(stats['components_preserved_near_foreground'],1)
        self.assertEqual(clean[2,2,3],0)

    def test_distant_colored_feather_not_erased_without_reference(self):
        self.m[1,1]=255;self.rgb[1,1]=[140,15,10]
        clean,*other=estimate(self.rgb,self.m)
        self.assertEqual(clean[1,1,3],255)
        self.assertTrue(np.array_equal(clean[1,1,:3],self.rgb[1,1]))
        self.assertEqual(other[-2]['components_preserved_color_or_sure_foreground'],1)

    def test_actual_candidate_reproducibility_and_hashes(self):
        self.assertEqual(sha(RGB),RGB_SHA);self.assertEqual(sha(INITIAL),INITIAL_SHA)
        rgb=np.array(Image.open(ROOT/RGB));old=np.array(Image.open(ROOT/INITIAL))
        actual=np.array(Image.open(ROOT/OUTPUT));computed=estimate(rgb,old[:,:,3])[0]
        self.assertTrue(np.array_equal(actual,computed))
        self.assertEqual(sha(OUTPUT),read('reports/alpha_cleanup_metrics_v2.json')['output_sha256'])


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(__import__(__name__)))
    write('reports/alpha_cleanup_tool_tests_v2.json',{'status':'PASS' if result.wasSuccessful() else 'FAIL',
       'count':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'timestamp':now(),
       'scope':'Geometry, speck safeguards, locked RGB/Alpha and exact reproducibility; not visual approval.'})
    raise SystemExit(0 if result.wasSuccessful() else 1)
