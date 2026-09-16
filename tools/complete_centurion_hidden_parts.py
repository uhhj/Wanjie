"""Apply only bounded hidden-grip/leg patches; frozen visible body is untouched."""
import json
from datetime import datetime,timezone
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
import build_centurion_parts as b
p=b.p
def save_part(n,a,mask,raw):
 out=b.O+n+'.png';Image.fromarray(a).save(p.ROOT/out)
 path=p.W+'masks/parts_completion/'+n+'.png';(p.ROOT/path).parent.mkdir(parents=True,exist_ok=True);Image.fromarray(mask).save(p.ROOT/path)
 return {'part':n,'output_file':out,'output_sha256':p.sha(out),'mask':path,'mask_sha256':p.sha(path),'raw':raw,'raw_sha256':p.sha(raw)}
def complete():
 p.verify();manifest=p.read('tools/roman_centurion_parts_manifest.json');recipes=[]
 # The generated crop preserves the two metal anchors. Resize only generated
 # material back into the recorded crop coordinates, never any frozen art.
 raw=p.W+'raw/005_sword_grip.png';g=Image.open(p.ROOT/raw).convert('RGB').resize((400,370),Image.Resampling.LANCZOS)
 canvas=Image.new('RGB',(1024,1536));canvas.paste(g,(240,780));rgb=np.array(canvas)
 visible=np.array(Image.open(p.ROOT/b.O/'sword.png'));base=visible.copy()
 # Trace away the non-sword strip caught by the original broad extraction.
 trim=b.poly([(386,933),(414,951),(460,995),(510,1048),(550,1084),(611,1129),(548,1098),(486,1054),(433,1003),(380,950)])
 base[trim]=0
 m=Image.new('L',(1024,1536));ImageDraw.Draw(m).polygon([(301,841),(309,838),(382,887),(374,898),(299,849)],fill=255)
 mask=np.array(m);patch=np.dstack([rgb,mask]);out=np.array(Image.alpha_composite(Image.fromarray(patch),Image.fromarray(base)))
 protected=base[:,:,3]>0;out[protected]=base[protected];out[out[:,:,3]==0,:3]=0
 recipes.append(save_part('sword',out,mask,raw));recipes[-1].update(protected_visible_rgb_changed=int(np.any(out[protected]!=base[protected],axis=1).sum()),trimmed_non_sword_pixels=int((trim&(visible[:,:,3]>0)).sum()))
 raw=p.W+'raw/006_hidden_legs.png';g=Image.open(p.ROOT/raw).convert('RGB').resize((450,520),Image.Resampling.LANCZOS)
 canvas=Image.new('RGB',(1024,1536));canvas.paste(g,(360,870));rgb=np.array(canvas);body=np.array(Image.open(p.ROOT/b.B))
 yy,xx=np.indices(body.shape[:2])
 # Upper-thigh completions end beneath opaque skirt; the real exposed thighs
 # are restored above generated pixels, and no source design pixels change.
 zones={
  'leg_near_thigh':[(444,889),(575,889),(550,988),(532,1034),(461,1059),(425,1030),(430,958)],
  'leg_far_thigh':[(622,929),(767,929),(757,1027),(747,1075),(682,1082),(636,1037)],
 }
 for n,points in zones.items():
  original=np.array(Image.open(p.ROOT/b.O/(n+'.png')))
  # Skirt fragments in a thigh candidate are not thigh anatomy.
  skirt=np.array(Image.open(p.ROOT/b.O/'pelvis.png'))[:,:,3]>0
  original[skirt]=0
  mask=b.poly(points).astype('uint8')*255
  # Derived cap is only used where original visible thigh pixels are absent.
  patch=np.dstack([rgb,mask]);out=np.array(Image.alpha_composite(Image.fromarray(patch),Image.fromarray(original)))
  protected=original[:,:,3]>0;out[protected]=original[protected];out[out[:,:,3]==0,:3]=0
  recipes.append(save_part(n,out,mask,raw));recipes[-1]['protected_visible_rgb_changed']=int(np.any(out[protected]!=original[protected],axis=1).sum())
 for side in ['near','far']:
  n='leg_'+side+'_shin';original=np.array(Image.open(p.ROOT/b.O/(n+'.png')))
  mask=b.poly(b.KNEES['knee_'+side]).astype('uint8')*255
  # Complete the surface actually hidden by the independent lion plate.
  patch=np.dstack([rgb,mask]);out=np.array(Image.alpha_composite(Image.fromarray(patch),Image.fromarray(original)))
  protected=original[:,:,3]>0;out[protected]=original[protected];out[out[:,:,3]==0,:3]=0
  recipes.append(save_part(n,out,mask,raw));recipes[-1]['protected_visible_rgb_changed']=int(np.any(out[protected]!=original[protected],axis=1).sum())
 raw=p.W+'raw/008_hidden_torso_cape.png';g=Image.open(p.ROOT/raw).convert('RGB').resize((530,610),Image.Resampling.LANCZOS)
 canvas=Image.new('RGB',(1024,1536));canvas.paste(g,(280,390));rgb=np.array(canvas)
 original=np.array(Image.open(p.ROOT/b.O/'cape.png'));master=np.array(Image.open(p.ROOT/p.W/'00_master_rgba.png'))
 swordmask=np.array(Image.open(p.ROOT/b.M/'sword.png'))>0
 bodymatch=np.all(master[:,:,:3]==body[:,:,:3],axis=2)&(body[:,:,3]>0)
 removed=swordmask|bodymatch
 original[removed]=0
 region=b.poly([(353,493),(449,428),(489,451),(510,611),(477,741),(434,856),(429,950),(391,997),(300,969),(273,887),(292,758),(321,640)])
 # All patch geometry lies behind the source arm/body or within the original
 # cape silhouette. A locally sampled red-fabric predicate excludes torso.
 red=(rgb[:,:,0].astype(float)>rgb[:,:,1]*1.35)&(rgb[:,:,0]>45)
 mask=(region&red&(master[:,:,3]>0)).astype('uint8')*255
 pommel=b.poly([(265,810),(289,808),(313,825),(317,852),(288,855),(264,840)])&(master[:,:,3]>0)
 # The pommel reaches 15px outside the generated crop. Use the recorded
 # neighboring generated cloth sample for this entirely hidden 53px patch.
 for y,x in zip(*np.where(pommel)):
  rgb[y,x]=rgb[y,min(x+55,1023)]
 mask[pommel]=255
 out=np.array(Image.alpha_composite(Image.fromarray(np.dstack([rgb,mask])),Image.fromarray(original)))
 protected=original[:,:,3]>0;out[protected]=original[protected];out[out[:,:,3]==0,:3]=0
 recipes.append(save_part('cape',out,mask,raw));recipes[-1]['protected_visible_rgb_changed']=int(np.any(out[protected]!=original[protected],axis=1).sum())
 n='torso';original=np.array(Image.open(p.ROOT/b.O/(n+'.png')))
 shoulder=np.array(Image.open(p.ROOT/b.O/'arm_near_upper.png'))[:,:,3]>0
 mask=(shoulder&b.poly([(439,444),(490,443),(510,525),(480,606),(457,587)])&~red).astype('uint8')*255
 out=np.array(Image.alpha_composite(Image.fromarray(np.dstack([rgb,mask])),Image.fromarray(original)))
 protected=original[:,:,3]>0;out[protected]=original[protected];out[out[:,:,3]==0,:3]=0
 recipes.append(save_part(n,out,mask,raw));recipes[-1]['protected_visible_rgb_changed']=int(np.any(out[protected]!=original[protected],axis=1).sum())
 for recipe in recipes:
  entry=next(e for e in manifest['parts'] if e['name']==recipe['part']);entry.update(ai_completed=True,completion_recipe=b.R+'hidden_completion_recipes.json',candidate_sha256=recipe['output_sha256'])
 p.save(b.R+'hidden_completion_recipes.json',{'tool':'built-in image_gen','timestamp':datetime.now(timezone.utc).isoformat(),'source_body_sha256':p.sha(b.B),'recipes':recipes,'review_required':True})
 p.save('tools/roman_centurion_parts_manifest.json',manifest)
 parts={n:Image.open(p.ROOT/b.O/(n+'.png')) for n in b.ORDER};bodyparts={n:im for n,im in parts.items() if n not in ['sword','cape','cape_front']}
 full=b.compose(parts);full.save(p.ROOT/b.R/'recomposed_completed.png')
 master=Image.open(p.ROOT/p.W/'00_master_rgba.png')
 b.tiles([('Master',master),('Completed parts rest',full)],b.R+'completed_recomposition_256.png',cols=2)
 b.tiles([('Master',master),('Completed parts rest',full)],b.R+'completed_recomposition_192.png',cols=2,h=192)
 items=[]
 for joint,chain in {'near_elbow':['arm_near_fore','hand_near'],'far_elbow':['arm_far_fore','hand_far'],'near_knee':['leg_near_shin','foot_near'],'far_knee':['leg_far_shin','foot_far']}.items():
  for angle in [-20,0,20]:
   trial=bodyparts.copy()
   for n in chain:trial[n]=trial[n].rotate(angle,Image.Resampling.BICUBIC,center=b.PIVOTS[chain[0]])
   items.append((f'{joint} {angle:+d}',b.compose(trial)))
 b.tiles(items,b.R+'completed_joint_256.png',cols=3);b.tiles(items,b.R+'completed_joint_192.png',cols=3,h=192)
 b.tiles([(n,parts[n]) for n in ['leg_near_thigh','leg_far_thigh','leg_near_shin','leg_far_shin','sword','cape','cape_front']],b.R+'completed_parts_review.png',cols=4)
 print('Local completion recipes saved; visual gate still required')
if __name__=='__main__':complete()
