"""Checks provenance, PNG format, native binding integrity and frozen source hashes."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'reports/minotaur_breaker'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 errors=[];sources=json.loads((ROOT/'art_source/odyssey/minotaur_breaker/source_manifest.json').read_text(encoding='utf-8'))
 for item in sources['files']:
  if sha(ROOT/item['file'])!=item['sha256']:errors.append('Frozen source changed: '+item['role'])
 manifest=json.loads((ROOT/'work/minotaur_breaker/candidates/manifest.json').read_text())
 names=[];parts=[]
 for item in manifest['parts']:
  names.append(item['name']);p=ROOT/item['file'];im=Image.open(p);a=np.array(im)
  valid=im.format=='PNG' and im.mode=='RGBA' and im.size==(1024,1536) and a[:,:,3].min()==0 and a[:,:,3].max()==255
  if not valid:errors.append('PNG validation failed: '+item['name'])
  if sha(p)!=item['sha256']:errors.append('Part hash changed: '+item['name'])
  parts.append({'name':item['name'],'format_pass':bool(valid),'opaque_pixels':int((a[:,:,3]==255).sum()),'fractional_pixels':int(((a[:,:,3]>0)&(a[:,:,3]<255)).sum())})
 if len(names)!=21 or len(set(names))!=21:errors.append('Expected 19 core parts and two hidden knee supports')
 meshes=json.loads((ROOT/'resources/minotaur_breaker_skinning_candidates.json').read_text())
 body_path=ROOT/'work/minotaur_breaker/01_complete_body_rgba_v2.png'
 body=np.array(Image.open(body_path));master=np.array(Image.open(ROOT/'work/minotaur_breaker/00_rig_master_rgba.png'))
 allowed=np.array(Image.open(ROOT/'work/minotaur_breaker/masks/body_completion_effective.png'))>0
 outside_changes=int(np.any(body!=master,2)[~allowed].sum())
 if outside_changes:errors.append('Complete body changed pixels outside approved local edit mask')
 for mesh in meshes['meshes']:
  part=next(x for x in manifest['parts'] if x['name']==mesh['part'])
  if mesh['texture_sha256']!=part['sha256']:errors.append('Mesh texture mismatch: '+mesh['part'])
  if mesh['vertices']!=mesh['uv']:errors.append('UV changed: '+mesh['part'])
  if not np.allclose(sum(np.array(v) for v in mesh['weights'].values()),1):errors.append('Weights do not sum to one')
 report={'status':'PASS' if not errors else 'FAIL','scope':'Format/provenance only; NOT art or animation approval','frozen_source_hashes_checked':4,'body_sha256':sha(body_path),'body_outside_mask_rgba_changes':outside_changes,'parts':parts,'native_meshes':len(meshes['meshes']),'mesh_vertices':sum(len(m['vertices']) for m in meshes['meshes']),'errors':errors}
 (R/'candidate_format_validation.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k!='parts'}))
 if errors:raise SystemExit(1)
if __name__=='__main__':main()
