"""Synthetic tests in isolated temporary directories; never formal production assets."""
import unittest,tempfile,json,sys
from pathlib import Path
from unittest.mock import patch
import numpy as np
from PIL import Image,ImageDraw
import rg_common as common
import ai_inpaint_roman_guard as jobs
from normalize_part_canvas import normalize_image
from generate_joint_rotation_test import transform

class SafetyTests(unittest.TestCase):
    def setUp(self):
        root=common.ROOT/'work/test_runs'; root.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(prefix='synthetic_',dir=root); self.root=Path(self.temp.name)
        self.patchers=[patch.object(common,'ROOT',self.root),patch.object(jobs,'ROOT',self.root)]
        for p in self.patchers: p.start()
        for d in ['tools','reports/ai_jobs','work/raw','work/masks','work/prompts','source']: (self.root/d).mkdir(parents=True,exist_ok=True)
        src=Image.new('RGBA',(32,32)); ImageDraw.Draw(src).rectangle((3,3,28,28),fill=(90,60,30,254)); src.save(self.root/'source/frozen.png')
        self.stage={'id':'001_test','input':'source/frozen.png','mask':'work/masks/edit.png','prompt':'work/prompts/edit.txt','output':'work/out.png'}
        common.write('tools/pipeline_config.json',{'source':'source/frozen.png','source_sha256':common.sha('source/frozen.png'),'canvas':[32,32],'stages':[self.stage]})
        m=Image.new('L',(32,32)); ImageDraw.Draw(m).rectangle((12,12,18,18),fill=255); m.save(self.root/'work/masks/edit.png')
        (self.root/'work/prompts/edit.txt').write_text('Test fixture only',encoding='utf-8'); common.write('reports/ai_jobs/001_test.json',self.stage)
    def tearDown(self):
        for p in reversed(self.patchers): p.stop()
        self.temp.cleanup()
    def test_source_mutation_is_rejected_without_repairing_source(self):
        p=self.root/'source/frozen.png'; p.write_bytes(p.read_bytes()+b'changed'); before=p.read_bytes()
        with self.assertRaisesRegex(ValueError,'SHA256'): common.check_source()
        self.assertEqual(before,p.read_bytes())
    def test_rgb_return_cannot_claim_transparency(self):
        path=self.root/'rgb.png'; Image.new('RGB',(32,32),'white').save(path)
        with self.assertRaisesRegex(ValueError,'NOT_TRANSPARENT'): jobs.import_result(self.stage,path)
        self.assertFalse((self.root/'work/out.png').exists())
    def test_hostile_global_edit_is_confined_to_mask(self):
        raw=Image.new('RGBA',(32,32),(255,0,240,255)); raw.putpixel((0,0),(0,0,0,0)); path=self.root/'actual.png'; raw.save(path)
        result=jobs.import_result(self.stage,path)
        source=np.array(common.rgba('source/frozen.png')); out=np.array(common.rgba('work/out.png')); allowed=np.array(common.mask(self.stage['mask']))>0
        self.assertTrue(np.array_equal(source[~allowed],out[~allowed])); self.assertTrue(np.any(source[allowed]!=out[allowed])); self.assertEqual(result['protected_changed_pixels'],0)
    def test_mismatched_ai_canvas_rejected_without_stretch(self):
        raw=Image.new('RGBA',(64,64)); path=self.root/'wrong.png'; raw.save(path)
        with self.assertRaisesRegex(ValueError,'canvas mismatch'): jobs.import_result(self.stage,path)
        self.assertFalse((self.root/'work/out.png').exists())
    def test_unreviewed_matte_rejected(self):
        path=self.root/'rgb.png'; Image.new('RGB',(32,32)).save(path)
        with self.assertRaisesRegex(ValueError,'review note'): jobs.import_result(self.stage,path,'work/masks/edit.png')
    def test_crop_needs_measured_offset(self):
        with self.assertRaisesRegex(ValueError,'explicit'): normalize_image(Image.new('RGBA',(8,8),'red'),(32,32))
    def test_normalization_cannot_clip(self):
        with self.assertRaisesRegex(ValueError,'clip'): normalize_image(Image.new('RGBA',(8,8),'red'),(32,32),(30,0))
    def test_normalization_retains_real_pixel_coordinates(self):
        im=Image.new('RGBA',(8,8)); im.putpixel((4,5),(23,42,99,127)); out=normalize_image(im,(32,32),(10,11))
        self.assertEqual(out.getpixel((14,16)),(23,42,99,127)); self.assertEqual(out.getchannel('A').getbbox(),(14,16,15,17))
    def test_stale_art_approval_cannot_unlock_pipeline(self):
        common.write('reports/art_reviews.json',{'complete_body':{'status':'PASS','sha256':common.sha('source/frozen.png'),'reviewer':'synthetic test','notes':'Synthetic hash invalidation case only'}})
        self.assertTrue(common.review_ok('complete_body','source/frozen.png'))
        im=Image.open(self.root/'source/frozen.png'); im.putpixel((12,12),(1,2,3,255)); im.save(self.root/'source/frozen.png')
        self.assertFalse(common.review_ok('complete_body','source/frozen.png'))
    def test_zero_angle_keeps_source_pixels_and_canvas(self):
        im=common.rgba('source/frozen.png'); out=transform(im,(16,16),0)
        self.assertTrue(np.array_equal(np.array(im),np.array(out)))
    def test_socket_transform_moves_child_about_parent_pivot(self):
        im=Image.new('RGBA',(32,32)); ImageDraw.Draw(im).rectangle((22,14,25,17),fill='red')
        out=transform(im,(16,16),90)
        ys,xs=np.where(np.array(out)[:,:,3]>128)
        self.assertAlmostEqual(float(xs.mean()),16,delta=1); self.assertLess(float(ys.mean()),11)
    def test_contact_sheet_reports_all_eighteen_cases_and_descendants(self):
        import generate_joint_rotation_test as rotation
        (self.root/'fixtures').mkdir()
        parts=[]
        for name in common.PARTS:
            file='fixtures/'+name+'.png'; im=Image.new('RGBA',(32,32)); ImageDraw.Draw(im).rectangle((12,10,23,22),fill=(190,70,30,255)); im.save(self.root/file)
            parts.append({'name':name,'file':file})
        common.write('tools/roman_guard_parts_manifest.json',{'parts':parts,'draw_passes':[{'part':n} for n in common.PARTS]})
        common.write('assets/units/odyssey/roman_guard/roman_guard_pivots.json',{'parts':{n:{'position':[8,16]} for n in common.PARTS},'joints':{n:{'position':[16,16],'diameter_hint_px':10} for n in ['near_elbow','far_elbow','near_knee','far_knee']}})
        with patch.object(rotation,'ROOT',self.root),patch.object(rotation,'validate',return_value={'status':'PASS'}),patch.object(sys,'argv',['synthetic_rotation_test']):
            code=rotation.main()
        self.assertEqual(code,2) # never production-approved by synthetic rendering alone
        report=common.read('reports/joint_rotation_metrics.json')
        self.assertEqual(len(report['tests']),18)
        near=[t for t in report['tests'] if t['joint']=='near_elbow']
        self.assertEqual([t['angle_deg'] for t in near],[-20,0,20]); self.assertIn('sword',near[0]['moved_parts'])
        self.assertTrue(near[1]['rest_overlap_requirement_checked']); self.assertTrue((self.root/'reports/joint_rotation_test.png').exists())

if __name__=='__main__': unittest.main(verbosity=2)
