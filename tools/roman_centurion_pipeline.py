"""Resumable, hash-bound Centurion asset gates. No fabricated PNGs or approvals."""
import argparse,hashlib,json
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];S='art_source/odyssey/roman_centurion/';W='work/roman_centurion/';R='reports/roman_centurion/'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def save(p,d):(ROOT/p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def verify():
 for e in read(S+'source_manifest.json')['files']:assert sha(e['file'])==e['sha256'],e['file']
 for p,h in read(R+'existing_units_freeze.json')['files'].items():assert sha(p)==h,p
 print('Existing units and 4 source images unchanged')
def compose(raw):
 verify();path=Path(raw).resolve();assert path.is_relative_to(Path('D:/Wanjie').resolve())
 source=Image.open(ROOT/W/'00_master_rgba.png');candidate=Image.open(path)
 assert candidate.size==source.size,'AI canvas mismatch; no automatic scale/warp allowed'
 assert candidate.mode=='RGBA','True RGBA output required'
 mask=np.array(Image.open(ROOT/W/'masks/complete_body_edit.png'))>0
 a=np.array(source);b=np.array(candidate);out=a.copy();out[mask]=b[mask]
 Image.fromarray(out).save(ROOT/W/'01_complete_body_candidate.png')
 save(R+'ai_jobs/001_complete_body.json',{'input_file':W+'00_master_rgba.png','input_sha256':sha(W+'00_master_rgba.png'),'mask':W+'masks/complete_body_edit.png','mask_sha256':sha(W+'masks/complete_body_edit.png'),'tool':'built-in image_gen','raw_output':path.relative_to(ROOT).as_posix(),'raw_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'output_file':W+'01_complete_body_candidate.png','output_sha256':sha(W+'01_complete_body_candidate.png'),'protected_pixels_changed':int(np.any(out!=a,axis=2)[~mask].sum()),'status':'VISUAL_REVIEW_REQUIRED','timestamp':datetime.now(timezone.utc).isoformat()})
 review()
def review():
 im=Image.open(ROOT/W/'01_complete_body_candidate.png');src=Image.open(ROOT/W/'00_master_rgba.png');arr=np.array(im);alpha=arr[:,:,3]
 metrics={'mode':im.mode,'dimensions':list(im.size),'alpha_min':int(alpha.min()),'alpha_max':int(alpha.max()),'opaque_pixels':int((alpha==255).sum()),'transparent_pixels':int((alpha==0).sum()),'fractional_pixels':int(((alpha>0)&(alpha<255)).sum())}
 save(R+'body_format_metrics.json',metrics)
 sheet=Image.new('RGB',(1200,880),'#eee');d=ImageDraw.Draw(sheet)
 for col,(name,image) in enumerate([('RIG MASTER',src),('BODY CANDIDATE',im)]):
  bg=Image.new('RGBA',image.size,'#b0b0b0');bg.alpha_composite(image);bg.thumbnail((550,825));sheet.paste(bg.convert('RGB'),(col*600+20,30));d.text((col*600+20,8),name,fill='black')
 sheet.save(ROOT/R/'complete_body_review.png')
 combat=Image.new('RGB',(1200,600),'#eeeeee');d=ImageDraw.Draw(combat)
 bounds=im.getbbox();height=bounds[3]-bounds[1]
 for row,h in enumerate([256,192]):
  v=im.resize((round(im.width*h/height),round(im.height*h/height)),Image.Resampling.LANCZOS)
  for col,color in enumerate(['white','#808080','#507596']):
   bg=Image.new('RGBA',v.size,color);bg.alpha_composite(v);combat.paste(bg.convert('RGB'),(col*400+90,row*300+20));d.text((col*400+10,row*300+5),str(h)+'px',fill='black')
 combat.save(ROOT/R/'complete_body_combat_review.png')
 print(json.dumps(metrics))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('command',choices=['verify','compose','review']);ap.add_argument('--raw');args=ap.parse_args()
 if args.command=='verify':verify()
 elif args.command=='compose':compose(args.raw)
 else:review()
if __name__=='__main__':main()
