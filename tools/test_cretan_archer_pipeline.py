"""Fail-closed import tests using isolated 8px fixtures, never production parts."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from PIL import Image
import cretan_archer_pipeline as p


class ImportGateTests(unittest.TestCase):
    def setUp(self):
        parent=p.ROOT/'work/test_runs';parent.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(prefix='cretan_gate_',dir=parent)
        self.root=Path(self.temp.name)
        self.patchers=[patch.object(p,'ROOT',self.root),patch.object(p,'verify_frozen',return_value=(8,8))]
        for item in self.patchers:item.start()
        for folder in [p.SOURCE,p.WORK+'masks',p.WORK+'prompts',p.REPORT+'ai_jobs']:(self.root/folder).mkdir(parents=True,exist_ok=True)
        src=np.zeros((8,8,4),dtype=np.uint8);src[2:6,2:6]=[90,60,40,254]
        Image.fromarray(src).save(self.root/p.MASTER)
        for name,_,_ in p.STAGES:
            mask=np.zeros((8,8),dtype=np.uint8);mask[2:6,2:6]=255
            Image.fromarray(mask).save(self.root/p.WORK/'masks'/f'{name}.png')
            (self.root/p.WORK/'prompts'/f'{name}.txt').write_text('test-only local edit',encoding='utf-8')

    def tearDown(self):
        for item in reversed(self.patchers):item.stop()
        self.temp.cleanup()

    def edited(self,i=0,outside=False,mode='RGBA'):
        im=Image.open(self.root/p.STAGES[i][1]).convert('RGBA');a=np.array(im)
        a[3,3,0]+=1
        if outside:a[0,0,0]=5
        path=self.root/f'fixture_{i}.png';Image.fromarray(a).convert(mode).save(path);return path

    def imported(self,i=0):
        p.import_stage(i,str(self.edited(i)),'fixture-only; not a model call')

    def approved_chain(self):
        for i in range(3):
            self.imported(i);p.review_stage(i,'PASS','Synthetic fixture approval for gate testing only')

    def test_outside_mask_change_rejected(self):
        with self.assertRaisesRegex(ValueError,'OUTSIDE_MASK_CHANGED'):p.import_stage(0,str(self.edited(outside=True)),'fixture')
        self.assertFalse((self.root/p.STAGES[0][2]).exists())

    def test_rgb_rejected(self):
        with self.assertRaisesRegex(ValueError,'TRUE_RGBA'):p.import_stage(0,str(self.edited(mode='RGB')),'fixture')

    def test_next_stage_requires_actual_review(self):
        self.imported()
        with self.assertRaisesRegex(ValueError,'PREVIOUS_STAGE_NOT_APPROVED'):p.import_stage(1,str(self.edited(1)),'fixture')

    def test_review_cannot_approve_unimported_file(self):
        Image.open(self.root/p.MASTER).save(self.root/p.STAGES[0][2])
        with self.assertRaisesRegex(ValueError,'PROVENANCE'):p.review_stage(0,'PASS','Must reject bypass')

    def test_changed_prompt_invalidates_review(self):
        self.imported();p.review_stage(0,'PASS','Test fixture reviewed')
        self.assertTrue(p.valid_review(0))
        (self.root/p.WORK/'prompts'/f'{p.STAGES[0][0]}.txt').write_text('changed prompt',encoding='utf-8')
        self.assertFalse(p.valid_review(0))

    def test_output_not_overwritten(self):
        self.imported();before=p.sha(p.STAGES[0][2])
        with self.assertRaisesRegex(ValueError,'already exists'):self.imported()
        self.assertEqual(before,p.sha(p.STAGES[0][2]))

    def test_matte_cannot_add_foreground(self):
        self.approved_chain();a=np.array(Image.open(self.root/p.STAGES[2][2]).getchannel('A'));a[3,3]=255;a[0,0]=100
        f=self.root/'bad_matte.png';Image.fromarray(a).save(f)
        with self.assertRaisesRegex(ValueError,'INVENT_FOREGROUND'):p.import_matte(str(f))

    def test_matte_preserves_rgb_and_does_not_approve_body(self):
        self.approved_chain();original=np.array(Image.open(self.root/p.STAGES[2][2]));a=original[:,:,3].copy();a[a==254]=255
        f=self.root/'matte.png';Image.fromarray(a).save(f);p.import_matte(str(f))
        result=np.array(Image.open(self.root/p.BODY))
        self.assertTrue(np.array_equal(original[:,:,:3],result[:,:,:3]));self.assertTrue(p.valid_matte())
        self.assertEqual(p.gate(),2)
        self.assertFalse(p.load(p.REPORT+'complete_body_gate.json')['visual_pass'])

    def test_missing_body_never_passes(self):
        self.assertEqual(p.gate(),2)
        self.assertEqual(p.load(p.REPORT+'complete_body_gate.json')['status'],'NOT_RUN')
        self.assertEqual(p.load(p.REPORT+'pipeline_status.json')['godot_handoff'],'NOT_READY')

    def test_explicit_external_baseline_has_no_fake_edit_chain(self):
        im=np.array(Image.open(self.root/p.MASTER));im[im[:,:,3]==254,3]=255
        Image.fromarray(im).save(self.root/p.BODY)
        p.save(p.REPORT+'approved_body_baseline.json',{'status':'USER_APPROVED','user_acceptance':'accepted candidate',
            'input_file':p.MASTER,'input_sha256':p.sha(p.MASTER),'output_file':p.BODY,
            'output_sha256':p.sha(p.BODY),'rgb_changed_pixels':0})
        self.assertTrue(p.valid_external_body())
        self.assertFalse(p.valid_review(0))
        # Updating only the record cannot bless changed RGB under alpha-only normalization.
        im[3,3,0]+=10;Image.fromarray(im).save(self.root/p.BODY)
        r=p.load(p.REPORT+'approved_body_baseline.json');r['output_sha256']=p.sha(p.BODY)
        p.save(p.REPORT+'approved_body_baseline.json',r)
        self.assertFalse(p.valid_external_body())


if __name__=='__main__':
    unittest.main(verbosity=2)
