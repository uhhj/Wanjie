"""Source-traced visible pixel partitions and measured joint overlap; no hidden painting."""
from rg_common import *
from extract_roman_guard_parts import extract

# Coordinates traced on the accepted 1024x1536 body. These are reviewable ownership
# boundaries, not inferred hidden anatomy. No nearest-label fill of unassigned pixels.
POLYGONS = {
 'torso':[(404,371),(488,371),(580,391),(640,436),(680,580),(640,619),(642,724),(375,739),(375,609),(445,537)],
 'pelvis':[(375,677),(638,677),(660,783),(686,866),(715,953),(715,1015),(589,1029),(483,1016),(360,1015),(302,1003),(301,962),(332,902),(358,821)],
 'leg_near_thigh':[(357,980),(487,986),(478,1030),(448,1091),(435,1133),(382,1157),(302,1118),(306,1076),(334,1047)],
 'leg_far_thigh':[(554,981),(692,981),(708,1042),(708,1111),(663,1148),(583,1120),(572,1057)],
 'leg_near_shin':[(307,1062),(347,1051),(394,1025),(432,1031),(461,1063),(459,1120),(436,1183),(399,1247),(379,1310),(377,1351),(286,1357),(264,1320),(272,1241),(263,1162),(279,1110)],
 'leg_far_shin':[(580,1080),(632,1074),(662,1032),(699,1027),(727,1067),(714,1149),(712,1225),(710,1288),(728,1340),(681,1369),(602,1364),(580,1313),(569,1248),(547,1173),(550,1134)],
 'foot_near':[(276,1333),(376,1325),(390,1362),(412,1393),(457,1430),(457,1480),(242,1480),(240,1424),(257,1374)],
 'foot_far':[(596,1330),(712,1325),(755,1355),(802,1375),(855,1410),(865,1473),(578,1473),(572,1380)],
 'arm_far_upper':[(580,391),(637,421),(669,481),(680,576),(672,615),(686,645),(713,666),(732,697),(704,739),(668,752),(623,720),(614,617),(618,492)],
 'arm_far_fore':[(681,687),(713,661),(737,691),(748,735),(770,766),(773,789),(732,814),(705,784),(672,766),(643,755)],
 'hand_far':[(723,779),(750,763),(777,786),(797,810),(797,844),(766,871),(732,872),(699,845),(699,810)],
 'arm_near_upper':[(280,447),(315,407),(379,373),(438,377),(494,405),(545,491),(539,512),(491,526),(480,579),(451,622),(419,611),(390,657),(386,705),(281,702),(272,636),(295,585),(279,570),(278,499)],
 'arm_near_fore':[(274,679),(325,663),(370,679),(391,704),(381,765),(374,842),(288,844),(274,770),(260,727)],
 'hand_near':[(289,831),(372,831),(392,855),(388,902),(360,936),(301,930),(267,896),(264,848)],
 'head':[(444,250),(627,250),(647,316),(628,388),(575,402),(594,442),(562,450),(511,414),(442,384),(451,345),(408,334)],
 'helmet':[(331,10),(724,10),(707,248),(647,278),(623,294),(624,323),(638,345),(620,384),(595,385),(565,373),(542,353),(516,333),(524,311),(534,296),(532,278),(522,267),(509,269),(504,282),(508,305),(498,319),(481,344),(402,346),(329,355)]
}

LINKS=[('torso','head','neck',(526,395),80),('torso','pelvis','waist',(530,701),160),
 ('torso','arm_near_upper','near_shoulder',(457,510),120),('torso','arm_far_upper','far_shoulder',(641,601),100),
 ('arm_near_upper','arm_near_fore','near_elbow',(333,681),84),('arm_near_fore','hand_near','near_wrist',(329,835),62),
 ('arm_far_upper','arm_far_fore','far_elbow',(682,704),82),('arm_far_fore','hand_far','far_wrist',(740,782),66),
 ('pelvis','leg_near_thigh','near_hip',(421,995),112),('pelvis','leg_far_thigh','far_hip',(619,1003),110),
 ('leg_near_thigh','leg_near_shin','near_knee',(405,1088),102),('leg_near_shin','foot_near','near_ankle',(332,1331),78),
 ('leg_far_thigh','leg_far_shin','far_knee',(671,1092),100),('leg_far_shin','foot_far','far_ankle',(658,1334),80)]

def main():
    assert body_review_ok(), 'Complete body gate must pass before splitting'
    source=rgba(body_source()); a=np.array(source); fg=a[:,:,3]>0
    labels=np.zeros(fg.shape,np.uint8); names=list(POLYGONS)
    for i,name in enumerate(names,1):
        m=Image.new('L',source.size); ImageDraw.Draw(m).polygon(POLYGONS[name],fill=255)
        labels[(np.array(m)>0)&fg]=i
    # The face opening under the brow/inside the cheek guard belongs to head.
    face=[(571,273),(607,275),(639,281),(643,315),(630,340),(617,372),(602,376),(599,366),(592,350),(589,335),(590,310),(590,306),(581,301),(575,295),(572,288)]
    fm=Image.new('L',source.size); ImageDraw.Draw(fm).polygon(face,fill=255)
    labels[(np.array(fm)>0)&fg]=names.index('head')+1
    unassigned=fg&(labels==0)
    write('work/masks/parts/source_traced_boundaries_v3.json',{'source':body_source(),'source_sha256':sha(body_source()),'canvas':list(source.size),'polygons':POLYGONS,'head_face_opening_override':face,'joint_hints':LINKS,'status':'DRAFT_VISUAL_REVIEW_REQUIRED','unassigned_foreground_pixels':int(unassigned.sum()),'hidden_geometry_synthesized':False})
    if unassigned.any():
        debug=a.copy(); debug[unassigned]=[255,0,255,255]
        Image.fromarray(debug).save(ROOT/'reports/part_unassigned_pixels.png')
        print('STOP_UNASSIGNED',int(unassigned.sum())); return 2
    masks={name:labels==i for i,name in enumerate(names,1)}
    yy,xx=np.indices(fg.shape); overlap=[]
    hints=read('assets/units/odyssey/roman_guard/roman_guard_pivots.json')
    for parent,child,key,(x,y),diameter in LINKS:
        # Only share existing opaque pixels owned by this anatomical pair.
        # A 25%-diameter axial band leaves the rest of each contour untouched.
        pair=masks[parent]|masks[child]
        parent_pos=hints['parts'][parent]['position']
        axis=np.array([x-parent_pos[0],y-parent_pos[1]],float)
        axis/=np.linalg.norm(axis)
        projection=(xx-x)*axis[0]+(yy-y)*axis[1]
        band=pair&(a[:,:,3]==255)&((xx-x)**2+(yy-y)**2<=(diameter*.65)**2)&(abs(projection)<=diameter*.125)
        masks[parent]|=band; masks[child]|=band
        overlap.append({'joint':key,'pivot':[x,y],'diameter':diameter,'band_axis':axis.tolist(),'band_span_px':float(projection[band].max()-projection[band].min()+1) if band.any() else 0,'shared_real_pixels':int(band.sum()),'hidden_completion':False})
    manifest=read('tools/roman_guard_parts_manifest.json')
    for p in manifest['parts']:
        if p['name'] not in masks: continue
        p['mask']='work/masks/parts/'+p['name']+'_v3.png'
        p['candidate_file']='work/candidates/parts/'+p['name']+'_v3.png'
        path=p['mask']; dst=ROOT/path; dst.parent.mkdir(parents=True,exist_ok=True)
        if dst.exists(): raise ValueError('Refuse to overwrite an existing part mask: '+path)
        Image.fromarray(masks[p['name']].astype(np.uint8)*255).save(dst)
        p.update(source=body_source(),mask_sha256=sha(path),mask_status='SOURCE_TRACED_DRAFT',status='READY_FOR_CANDIDATE_EXTRACTION',missing_hidden_regions=['Visible partition only; hidden joint surfaces require rotation review before formal approval.'])
    manifest['status']='CANDIDATES_IN_REVIEW'; manifest['complete_body_gate']='reports/complete_body_gate_combat_v1.json'
    write('tools/roman_guard_parts_manifest.json',manifest)
    pivots=read('assets/units/odyssey/roman_guard/roman_guard_pivots.json')
    for parent,child,key,pos,diameter in LINKS:
        pivots['parts'][child]['position']=list(pos)
        if key in pivots['joints']: pivots['joints'][key].update(position=list(pos),diameter_hint_px=diameter,overlap_hint_px=round(diameter*.25))
        p=next(p for p in manifest['parts'] if p['name']==child); p['pivot_hint']['position']=list(pos)
    pivots['source']=body_source(); pivots['source_sha256']=sha(body_source())
    write('assets/units/odyssey/roman_guard/roman_guard_pivots.json',pivots)
    write('tools/roman_guard_parts_manifest.json',manifest)
    for name in names: extract(name)
    write('reports/body_part_overlap_v1.json',{'status':'MEASURED_VISIBLE_OVERLAP_REVIEW_REQUIRED','joints':overlap,'source_sha256':sha(body_source())})
    colors=np.array([[0,0,0]]+[[55+(i*79)%180,55+(i*113)%180,55+(i*47)%180] for i in range(1,17)],np.uint8)
    label_rgba=np.dstack([colors[labels],a[:,:,3]])
    Image.fromarray(label_rgba).save(ROOT/'reports/body_part_ownership_v2.png')
    items=[(p['name']+' / draft',rgba(p['candidate_file'])) for p in read('tools/roman_guard_parts_manifest.json')['parts']]
    sheet(items,'reports/parts_candidate_review_v2.png',4,(300,450))
    print('19 real pixel candidates; no formal approval claimed')
    return 0

if __name__=='__main__': raise SystemExit(main())
