"""Centurion source-pixel candidates; promotion requires separate visual gates."""
import math
import numpy as np
from PIL import Image, ImageDraw
import roman_centurion_pipeline as p

B=p.W+'03_complete_body_v2.png'
O=p.W+'candidates/parts/'
M=p.W+'masks/parts/'
R=p.R+'parts_v1/'
POLYS={
 'torso':[(462,365),(631,365),(703,425),(760,562),(723,641),(717,730),(487,738),(450,579),(455,480)],
 'pelvis':[(489,666),(709,666),(752,785),(802,959),(779,1020),(736,1044),(612,1048),(551,1036),(429,1004),(386,965),(424,846)],
 'head':[(385,30),(785,30),(785,350),(674,374),(636,398),(620,414),(531,398),(510,370),(385,370)],
 'leg_far_thigh':[(609,1005),(758,1005),(766,1125),(747,1180),(635,1180),(632,1120)],
 'leg_near_thigh':[(429,969),(568,1006),(552,1071),(529,1136),(490,1180),(389,1160),(408,1080)],
 'leg_far_shin':[(636,1100),(774,1090),(768,1210),(781,1357),(737,1390),(647,1381),(625,1200)],
 'leg_near_shin':[(416,1090),(549,1090),(531,1200),(491,1338),(488,1380),(391,1380),(375,1270),(384,1180)],
 'foot_far':[(651,1340),(766,1334),(792,1383),(906,1420),(906,1480),(637,1480)],
 'foot_near':[(390,1340),(484,1340),(514,1405),(532,1430),(532,1495),(367,1495)],
 'arm_far_upper':[(701,477),(733,490),(779,568),(786,603),(816,634),(815,690),(746,713),(714,680),(701,627)],
 'arm_far_fore':[(780,608),(817,596),(860,593),(908,575),(930,631),(873,665),(813,691),(786,692)],
 'hand_far':[(895,584),(913,549),(948,525),(1015,525),(1023,626),(937,659),(900,643)],
 'arm_near_upper':[(406,425),(447,425),(479,442),(500,483),(500,548),(480,604),(447,603),(419,652),(405,704),(325,704),(326,652),(343,607),(343,553),(342,500),(365,456)],
 'arm_near_fore':[(322,678),(410,678),(415,720),(395,770),(387,828),(317,838),(310,796)],
 'hand_near':[(320,812),(379,811),(397,843),(407,876),(382,915),(347,925),(312,903),(299,875),(300,845)],
}
PIVOTS={'pelvis':[605,690],'torso':[605,670],'head':[589,386],'helmet':[589,386],
 'arm_near_upper':[450,501],'arm_near_fore':[367,687],'hand_near':[350,815],
 'arm_far_upper':[729,555],'arm_far_fore':[789,652],'hand_far':[908,615],
 'leg_near_thigh':[494,941],'knee_near':[489,1109],'leg_near_shin':[489,1109],'foot_near':[442,1350],
 'leg_far_thigh':[691,974],'knee_far':[728,1112],'leg_far_shin':[728,1112],'foot_far':[713,1355],
 'sword':[351,857],'cape':[570,423],'cape_front':[570,423]}
KNEES={
 'knee_near':[(455,1060),(487,1047),(516,1057),(535,1076),(537,1101),(525,1135),(492,1161),(470,1148),(449,1112),(448,1081)],
 'knee_far':[(709,1060),(740,1049),(757,1059),(769,1083),(775,1113),(762,1139),(742,1157),(720,1148),(704,1124),(695,1097)]}
LINKS=[('torso','head',65),('torso','pelvis',165),('torso','arm_near_upper',110),('torso','arm_far_upper',80),
 ('arm_near_upper','arm_near_fore',82),('arm_near_fore','hand_near',64),('arm_far_upper','arm_far_fore',86),('arm_far_fore','hand_far',65),
 ('pelvis','leg_near_thigh',115),('pelvis','leg_far_thigh',110),('leg_near_thigh','leg_near_shin',102),('leg_far_thigh','leg_far_shin',99),
 ('leg_near_shin','foot_near',85),('leg_far_shin','foot_far',95)]
ORDER=['cape','arm_far_upper','arm_far_fore','hand_far','leg_far_thigh','leg_far_shin','foot_far','knee_far',
 'leg_near_thigh','leg_near_shin','foot_near','knee_near','pelvis','torso','head','helmet','arm_near_upper','cape_front','arm_near_fore','sword','hand_near']
def poly(points):
 im=Image.new('L',(1024,1536));ImageDraw.Draw(im).polygon(points,fill=255);return np.array(im)>0
def extract(im,mask):
 a=np.array(im);a[:,:,3]=np.where(mask,a[:,:,3],0);a[a[:,:,3]==0,:3]=0;return Image.fromarray(a)
def compose(parts):
 im=Image.new('RGBA',(1024,1536))
 for name in ORDER:
  if name in parts:im.alpha_composite(parts[name])
 return im
def tiles(items,file,h=256,cols=4):
 tw=230;th=h+45;sheet=Image.new('RGB',(tw*cols,th*math.ceil(len(items)/cols)),'#eeeeee');d=ImageDraw.Draw(sheet)
 for i,(label,im) in enumerate(items):
  v=im.resize((round(1024*h/1425),round(1536*h/1425)),Image.Resampling.LANCZOS)
  x=(i%cols)*tw;y=(i//cols)*th;bg=Image.new('RGBA',v.size,'white');bg.alpha_composite(v);sheet.paste(bg.convert('RGB'),(x+10,y+22));d.text((x+5,y+4),label,fill='black')
 sheet.save(p.ROOT/file)
def build():
 p.verify();gate=p.read(p.R+'complete_body_gate_v2.json');assert gate['status']=='PASS' and gate['input_sha256']==p.sha(B)
 for f in [O,M,R]:(p.ROOT/f).mkdir(parents=True,exist_ok=True)
 body=Image.open(p.ROOT/B).convert('RGBA');a=np.array(body);fg=a[:,:,3]>0;names=list(POLYS);labels=np.zeros(fg.shape,np.uint8)
 for i,n in enumerate(names,1):labels[poly(POLYS[n])&fg]=i
 # Explicitly reviewed contour omissions, assigned to their anatomical region.
 yy,xx=np.indices(fg.shape)
 repairs=[('torso',(yy<470)&(xx<650)),('arm_far_upper',(yy<590)&(xx>690)),
  ('arm_near_upper',(yy>=470)&(yy<680)&(xx<480)),('arm_near_fore',(yy>=680)&(yy<840)&(xx<425)),
  ('arm_far_fore',(yy>=575)&(yy<710)&(xx>780)&(xx<921)),('pelvis',(yy>=720)&(yy<1050)&(xx>=385)),
  ('leg_near_shin',(yy>=1050)&(yy<1340)&(xx<590)),('leg_far_shin',(yy>=1050)&(yy<1340)&(xx>=590)),
  ('foot_near',(yy>=1340)&(xx<590)),('foot_far',(yy>=1340)&(xx>=590))]
 for n,region in repairs:labels[(labels==0)&fg&region]=names.index(n)+1
 residual=fg&(labels==0);extract(body,residual).save(p.ROOT/R/'unassigned_pixels.png')
 masks={n:labels==i for i,n in enumerate(names,1)}
 # Head and helmet retain one rest anchor; exposed face pixels are traced explicitly.
 face=poly([(576,274),(601,276),(647,276),(649,297),(685,311),(678,324),(677,349),(672,365),(636,373),(626,399),(620,414),(531,398),(510,370),(530,343),(550,339),(556,317),(568,307)])
 masks['helmet']=masks['head']&~face;masks['head']&=face
 yy,xx=np.indices(fg.shape);overlaps=[]
 for parent,child,diam in LINKS:
  x,y=PIVOTS[child];axis=np.array(PIVOTS[child],float)-np.array(PIVOTS[parent],float);axis/=max(np.linalg.norm(axis),1)
  union=masks[parent]|masks[child];band=union&(a[:,:,3]>250)&((xx-x)**2+(yy-y)**2<(diam*.65)**2)&(abs((xx-x)*axis[0]+(yy-y)*axis[1])<=diam*.15)
  missing=not bool((band&masks[child]).any()) or not bool((band&masks[parent]).any())
  if missing:band[:]=False
  masks[parent]|=band;masks[child]|=band
  overlaps.append({'parent':parent,'child':child,'pivot':[x,y],'diameter':diam,'axial_overlap_percent':30,'shared_pixels':int(band.sum()),'hidden_connection_missing':missing})
 for n,points in KNEES.items():
  side=n.split('_')[1];mask=poly(points)&fg;masks[n]=mask
  # No duplicate plate in the moving shin or thigh. Any resulting exposure must be reviewed.
  masks['leg_'+side+'_shin']&=~mask;masks['leg_'+side+'_thigh']&=~mask
 parts={n:extract(body,m) for n,m in masks.items()}
 master=Image.open(p.ROOT/p.W/'00_master_rgba.png').convert('RGBA')
 sword=poly([(414,885),(427,902),(457,941),(511,1002),(560,1063),(611,1129),(545,1085),(492,1048),(438,995),(385,942),(361,929),(365,909),(393,873),(406,861),(417,864),(417,875)])|poly([(274,814),(286,810),(300,822),(317,831),(311,851),(290,847),(276,841),(267,831)])
 cape=poly([(354,548),(345,589),(337,629),(325,657),(317,705),(311,770),(313,814),(298,836),(298,875),(309,901),(341,922),(379,918),(394,936),(422,973),(430,1001),(420,1075),(399,1127),(381,1151),(345,1238),(295,1200),(242,1171),(250,1140),(173,1129),(109,1118),(72,1095),(99,1017),(145,963),(80,980),(51,968),(65,899),(111,824),(183,758),(250,697),(313,613)])
 cape_front=poly([(530,348),(588,369),(631,379),(663,380),(681,383),(699,407),(703,438),(725,467),(750,495),(778,533),(776,542),(730,538),(683,521),(637,498),(602,471),(550,463),(519,448),(485,433),(453,432),(420,443),(391,462),(351,496),(362,463),(377,432),(401,401),(442,376),(482,359)])
 # The lion clasp and hanging red tassel belong to the cape assembly.
 cape_front|=poly([(535,408),(568,395),(603,411),(612,444),(602,468),(604,502),(606,534),(569,537),(559,477),(541,458)])
 for n,m in [('sword',sword),('cape',cape),('cape_front',cape_front)]:masks[n]=m;parts[n]=extract(master,m)
 entries=[]
 for n,im in parts.items():
  im.save(p.ROOT/O/(n+'.png'));Image.fromarray(masks[n].astype('uint8')*255).save(p.ROOT/M/(n+'.png'))
  source=p.W+'00_master_rgba.png' if n in ['sword','cape','cape_front'] else B
  entries.append({'name':n,'file':'assets/units/odyssey/roman_centurion/parts/'+n+'.png','candidate_file':O+n+'.png','source':source,'source_sha256':p.sha(source),'mask':M+n+'.png','mask_sha256':p.sha(M+n+'.png'),'candidate_sha256':p.sha(O+n+'.png'),'pivot_hint':PIVOTS[n],'status':'CANDIDATE_REVIEW_REQUIRED','review_required':True,'ai_completed':source==B})
 p.save('tools/roman_centurion_parts_manifest.json',{'unit_id':'OD_UNIT_03_ROMAN_CENTURION','canvas_width':1024,'canvas_height':1536,'alpha_required':True,'parts':entries,'draw_order':ORDER,'status':'CANDIDATES_ONLY'})
 p.save(R+'mask_definition.json',{'polygons':POLYS,'knees':KNEES,'pivots':PIVOTS,'overlaps':overlaps,'unassigned_pixels':int(residual.sum()),'unassigned_visible_pixels':int((residual&(a[:,:,3]>16)).sum())})
 overlay=Image.new('RGBA',body.size,'#808080');overlay.alpha_composite(body);d=ImageDraw.Draw(overlay)
 for n,points in {**POLYS,**KNEES}.items():d.line(points+[points[0]],fill='#00ffff',width=2)
 for n,xy in PIVOTS.items():
  x,y=xy;d.ellipse((x-5,y-5,x+5,y+5),fill='yellow');d.text((x+7,y),n,fill='yellow')
 overlay.convert('RGB').save(p.ROOT/R/'mask_pivot_review.png')
 tiles(list(parts.items()),R+'part_contact_sheet.png',cols=5)
 bodyparts={n:im for n,im in parts.items() if n not in ['cape','cape_front','sword']};rest=compose(bodyparts);full=compose(parts)
 rest.save(p.ROOT/R/'body_recomposed.png');full.save(p.ROOT/R/'recomposed.png')
 tiles([('Approved body',body),('Body parts rest',rest),('Frozen Master',master),('Equipment recomposition',full)],R+'recomposition_256.png')
 tiles([('Frozen Master',master),('Equipment recomposition',full)],R+'recomposition_192.png',h=192,cols=2)
 diff=np.abs(np.array(rest).astype(int)-a.astype(int));Image.fromarray(np.clip(diff[:,:,:3]*4,0,255).astype('uint8')).save(p.ROOT/R/'body_diff.png')
 items=[]
 for joint,children in {'near_elbow':['arm_near_fore','hand_near'],'far_elbow':['arm_far_fore','hand_far'],'near_knee':['leg_near_shin','foot_near'],'far_knee':['leg_far_shin','foot_far']}.items():
  for angle in [-20,0,20]:
   trial=bodyparts.copy()
   for n in children:trial[n]=trial[n].rotate(angle,Image.Resampling.BICUBIC,center=PIVOTS[children[0]])
   im=compose(trial);im.save(p.ROOT/R/f'{joint}_{angle:+d}.png');items.append((f'{joint} {angle:+d}',im))
 tiles(items,R+'joint_rotation_256.png',cols=3);tiles(items,R+'joint_rotation_192.png',h=192,cols=3)
 p.save(R+'extraction_metrics.json',{'candidate_count':len(parts),'formal_approved_count':0,'body_source_sha256':p.sha(B),'unassigned_visible_pixels':int((residual&(a[:,:,3]>16)).sum()),'body_rest_max_rgba_difference':int(diff.max()),'body_rest_changed_pixels':int(np.any(diff,axis=2).sum()),'format':'RGBA_SAME_CANVAS','review':'PENDING','sword_hidden_grip':'NOT_COMPLETED','godot_handoff':'NOT_READY'})
 print(p.read(R+'extraction_metrics.json'))
if __name__=='__main__':build()
