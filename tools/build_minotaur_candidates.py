"""Source-pixel part candidates only. Never promotes an unreviewed part."""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
ROOT=Path(__file__).resolve().parents[1];W=ROOT/'work/minotaur_breaker';R=ROOT/'reports/minotaur_breaker'
POLYGONS={
'head':[(220,40),(710,40),(714,395),(667,411),(595,390),(503,347),(389,323),(275,275),(211,206)],
'shoulder_near':[(263,307),(343,310),(395,326),(465,365),(497,435),(459,481),(407,539),(336,547),(257,525),(172,558),(138,481),(149,425),(195,368)],
'shoulder_far':[(609,435),(654,447),(675,511),(666,596),(617,579),(595,527)],
'torso':[(372,337),(505,344),(605,376),(667,444),(658,606),(649,715),(393,720),(360,656),(373,590),(398,550),(423,484)],
'pelvis':[(379,645),(645,655),(663,747),(713,1005),(690,1070),(508,1100),(425,1034),(267,1002),(337,920),(355,816)],
'arm_near_upper':[(204,505),(338,492),(376,534),(375,571),(347,614),(319,685),(300,717),(158,698),(152,625),(184,554)],
'arm_near_fore':[(166,642),(304,635),(341,688),(328,804),(324,849),(211,866),(184,803),(170,736)],
'hand_near':[(206,820),(324,811),(359,871),(355,929),(324,960),(254,956),(201,922),(188,875)],
'arm_far_upper':[(603,538),(668,544),(671,639),(660,711),(691,751),(669,791),(620,780),(600,691)],
'arm_far_fore':[(637,715),(679,735),(730,778),(787,806),(788,877),(753,914),(687,871),(646,829),(622,767)],
'hand_far':[(764,796),(818,795),(846,817),(868,846),(872,899),(850,932),(817,939),(765,914),(735,887),(735,836)],
'leg_near_thigh':[(299,943),(451,974),(477,1010),(440,1082),(422,1136),(300,1150),(233,1084),(255,1016)],
'leg_near_shin':[(238,1050),(353,1022),(442,1037),(452,1094),(417,1180),(373,1302),(370,1390),(229,1409),(211,1340),(234,1251),(211,1180),(211,1112)],
'foot_near':[(218,1336),(367,1327),(391,1380),(427,1464),(425,1510),(169,1510),(164,1410),(186,1368)],
'leg_far_thigh':[(514,973),(650,978),(689,1035),(692,1109),(650,1155),(501,1155),(493,1097)],
'leg_far_shin':[(519,1041),(676,1033),(709,1092),(700,1157),(677,1289),(699,1404),(532,1417),(495,1332),(498,1233),(488,1142)],
'foot_far':[(526,1340),(682,1339),(711,1380),(800,1442),(814,1503),(492,1503),(489,1407)]}
ORDER=['cape','arm_far_upper','arm_far_fore','leg_far_thigh','leg_far_shin','foot_far','leg_near_thigh','leg_near_shin','foot_near','pelvis','torso','head','shoulder_far','arm_near_upper','arm_near_fore','shoulder_near','hand_near','axe','hand_far']
ORDER=['knee_far_support','knee_near_support']+ORDER
def main():
 im=Image.open(W/'01_complete_body_rgba.png');a=np.array(im);out=W/'candidates/parts';out.mkdir(parents=True,exist_ok=True);masks=W/'masks/parts';masks.mkdir(parents=True,exist_ok=True);parts={};manifest=[]
 for name,poly in POLYGONS.items():
  mask=Image.new('L',im.size);ImageDraw.Draw(mask).polygon(poly,fill=255)
  if name=='torso':
   for extra in [[(225,272),(382,277),(524,344),(497,387),(389,341),(270,330)],[(350,565),(396,549),(397,717),(345,853),(320,825),(327,681)]]:ImageDraw.Draw(mask).polygon(extra,fill=255)
  extensions={'arm_near_fore':[(143,650),(177,644),(194,806),(173,807)],'leg_near_shin':[(194,1298),(235,1298),(247,1392),(203,1392)],'foot_far':[(665,1329),(700,1349),(727,1394),(684,1408)]}
  if name in extensions:ImageDraw.Draw(mask).polygon(extensions[name],fill=255)
  mask=mask.filter(ImageFilter.MaxFilter(15));mask.save(masks/(name+'.png'));b=a.copy();b[:,:,3]=np.minimum(b[:,:,3],np.array(mask));b[b[:,:,3]==0,:3]=0;part=Image.fromarray(b);part.save(out/(name+'.png'));parts[name]=part;manifest.append({'name':name,'file':str((out/(name+'.png')).relative_to(ROOT)),'status':'CANDIDATE_REVIEW_REQUIRED','source':'work/minotaur_breaker/01_complete_body_rgba.png'})
 # Coverage diagnostic: never hide uncovered pixels in a catch-all torso.
 covered=np.zeros(a.shape[:2],bool)
 for part in parts.values():covered|=np.array(part)[:,:,3]>0
 missing=(a[:,:,3]>0)&~covered
 dbg=Image.new('RGBA',im.size,'#808080');dbg.alpha_composite(im);ov=np.zeros_like(a);ov[missing]=[255,0,255,255];dbg.alpha_composite(Image.fromarray(ov));dbg.resize((512,768)).save(R/'body_mask_coverage_review.png')
 (R/'candidate_parts.json').write_text(json.dumps({'status':'CANDIDATE_REVIEW_REQUIRED','parts':manifest,'unassigned_body_pixels':int(missing.sum()),'draw_order':ORDER,'missing_equipment':['axe','cape']},indent=2)+'\n',encoding='utf-8')
 thumb=Image.new('RGB',(1280,((len(parts)+5)//6)*330),'#bbb');d=ImageDraw.Draw(thumb)
 for i,(name,part) in enumerate(parts.items()):
  b=Image.new('RGBA',im.size,'#808080');b.alpha_composite(part);b.thumbnail((205,300));x=i%6*213;y=i//6*330;thumb.paste(b.convert('RGB'),(x,y+23));d.text((x+4,y+4),name,fill='black')
 thumb.save(R/'part_candidates_review.png');print('body candidate parts',len(parts),'unassigned',missing.sum())
if __name__=='__main__':main()
