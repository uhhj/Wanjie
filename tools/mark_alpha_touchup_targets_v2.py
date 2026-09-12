"""Draw observed local matte targets; never modify candidate or infer a repair."""
from PIL import Image,ImageDraw
from rg_common import ROOT,read,write,sha,now,font
from review_alpha_cleanup_v2 import composite

TARGETS=[
 ('region_001','plume_top',[483,27,638,63],'红冠顶部不规则黑色凸点',
  '逐点核对红色羽毛轮廓，只处理其外侧残留 Alpha；保留真正细羽毛，不按小面积统一删除。'),
 ('region_002','shoulder',[326,381,445,415],'肩甲弧线上缘黑色凸点',
  '沿现有金属外轮廓处理外侧残留，保留原暗描边；仅修窄带 Alpha/半透明 RGB。'),
 ('region_003','leg_far',[682,1169,709,1282],'远侧护胫外缘不规则黑色阶梯/凸点',
  '逐段区分真实甲边与轮廓外的近黑残留；不得削薄整条护胫或改变腿形。'),
 ('region_004','sole_near',[330,1448,442,1468],'近侧鞋底下方扁块状黑色残留',
  '按真实鞋底轮廓审查下方小块，保留鞋底厚度和原阴影；不统一侵蚀整只鞋。'),
 ('region_005','sole_far',[686,1434,838,1459],'远侧鞋底下方离散黑色凸点',
  '仅修鞋底外侧的离散点/短段，保留真实深色鞋底，不提高全局颜色阈值。'),
]


def main():
    m=read('reports/alpha_cleanup_metrics_v2.json');path=m['output_file'];before=sha(path)
    rgba=Image.open(ROOT/path).copy();white=composite(rgba,(255,255,255));gray=composite(rgba,(128,128,128))
    # Full-scale overview keeps boxes in source coordinates; details are 4x.
    report_height=max(1720,65+sum(max(280,88+(box[3]-box[1])*8) for _,_,box,_,_ in TARGETS))
    canvas=Image.new('RGB',(2100,report_height),(31,33,38));d=ImageDraw.Draw(canvas)
    canvas.paste(white,(10,90));d.text((15,15),'Local Alpha Touchup Only · 已观察区域',font=font(27),fill='white')
    d.text((15,53),'框是审查范围，不是授权修改整个矩形。',font=font(21),fill='white')
    records=[];y=15
    trimap=Image.open(ROOT/'work/masks/alpha_trimap_v2.png')
    for rid,key,box,problem,correction in TARGETS:
        x0,y0,x1,y1=box
        d.rectangle((10+x0,90+y0,10+x1,90+y1),outline=(255,25,180),width=3)
        lx=max(12,min(820,x0+10));ly=max(92,y0+62)
        d.rectangle((lx,ly,lx+150,ly+27),fill=(31,33,38))
        d.text((lx+3,ly+2),rid,font=font(20),fill=(255,90,210))
        d.text((1070,y),rid+' '+str(box),font=font(22),fill='white')
        d.text((1070,y+34),problem,font=font(20),fill='white')
        for index,tile in enumerate([white,gray]):
            crop=tile.crop(box);crop=crop.resize((crop.width*4,crop.height*4),Image.Resampling.NEAREST)
            # Stack white and gray to retain 4x without squeezing broad strips.
            canvas.paste(crop,(1070,y+72+index*(crop.height+8)))
        height=(y1-y0)*4
        y+=max(280,88+height*2)
        import numpy as np
        local=np.array(trimap.crop(box))
        records.append({'id':rid,'region':key,'bbox':box,'problem_type':problem,
          'recommended_correction':correction,
          'constraint':'Unknown-band edits only. If the target requires changing locked sure foreground, stop and flag it; do not alter it automatically.',
          'sure_foreground_pixels_in_review_box':int((local==255).sum()),
          'unknown_pixels_in_review_box':int((local==128).sum()),
          'bbox_is_edit_mask':False})
    if y>canvas.height:raise ValueError('Review labels exceed sheet; enlarge report canvas, not image')
    canvas.save(ROOT/'reports/alpha_manual_touchup_targets_v2.png')
    write('reports/alpha_manual_touchup_targets_v2.json',{'status':'LOCAL_REVIEW_REQUIRED','output_file':path,
          'output_sha256':before,'targets':records,'timestamp':now(),
          'global_algorithm_frozen':True,'automatic_correction_executed':False})
    if sha(path)!=before:raise ValueError('Candidate changed')
    print(f'Marked {len(records)} local review targets; no image edits.')


if __name__=='__main__':main()
