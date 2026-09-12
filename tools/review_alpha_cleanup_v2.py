"""Render required multi-background, trimap, 4x details and debug halo evidence."""
from PIL import Image,ImageDraw
import numpy as np
from rg_common import ROOT,read,sha,write,now,font,checker

REGIONS=[
 ('plume_top','红冠顶部',(429,26,603,70)),
 ('plume_tail','红冠尾部',(347,256,400,347)),
 ('helmet','头盔后缘',(410,314,546,375)),
 ('shoulder','肩甲外缘',(310,380,491,432)),
 ('hand_near','近侧手',(276,822,386,929)),
 ('hand_far','远侧手',(708,766,792,870)),
 ('skirt','裙甲下摆',(318,954,510,1020)),
 ('leg_near','近侧腿外缘',(269,1120,323,1295)),
 ('leg_far','远侧腿外缘',(673,1150,716,1325)),
 ('sole_near','近侧鞋底',(254,1420,447,1469)),
 ('sole_far','远侧鞋底',(659,1408,852,1465)),
]


def composite(rgba,color):
    bg=checker(rgba.size,16) if color=='checker' else Image.new('RGBA',rgba.size,(*color,255))
    return Image.alpha_composite(bg,rgba).convert('RGB')


def thumbnail(im,size):
    im=im.copy();im.thumbnail(size,Image.Resampling.LANCZOS);return im


def main():
    metrics=read('reports/alpha_cleanup_metrics_v2.json')
    source=Image.open(ROOT/metrics['input_file']).copy()
    old=Image.open(ROOT/metrics['initial_alpha_file']).copy()
    clean=Image.open(ROOT/metrics['output_file']).copy()
    locked=[sha(metrics[k]) for k in ['input_file','initial_alpha_file','output_file']]
    views={name:composite(clean,color) for name,color in [('checker','checker'),('white',(255,255,255)),
                                                           ('gray',(128,128,128)),('blue',(70,110,155))]}
    full=Image.new('RGB',(1080,1710),(32,34,39));d=ImageDraw.Draw(full)
    for i,(name,tile) in enumerate(views.items()):
        x=i%2*540;y=i//2*850
        d.text((x+16,y+12),{'checker':'棋盘','white':'白底','gray':'50% 灰底','blue':'中蓝底'}[name],font=font(25),fill='white')
        full.paste(tile.resize((520,780),Image.Resampling.LANCZOS),(x+10,y+55))
    full.save(ROOT/'reports/rgba_background_review_v2.png')
    tri=Image.open(ROOT/'work/masks/alpha_trimap_v2.png').copy();t=np.array(tri)
    tint=np.zeros((*t.shape,4),np.uint8);tint[t==255]=[30,210,80,45];tint[t==128]=[250,80,220,180]
    overlay=Image.alpha_composite(old,Image.fromarray(tint))
    sheet=Image.new('RGB',(1560,860),(32,34,39));d=ImageDraw.Draw(sheet)
    for i,(label,tile) in enumerate([('初始 Alpha',composite(old,'checker')),
        ('Trimap：白=SF / 灰=unknown',tri.convert('RGB')),
        ('绿=固定主体 / 紫=未知带',composite(overlay,'checker'))]):
        d.text((i*520+10,12),label,font=font(19),fill='white')
        sheet.paste(tile.resize((500,750),Image.Resampling.NEAREST),(i*520+10,65))
    d.text((15,827),'Euclidean disk erosion 2px / dilation 3px；RGB 修改仅限紫色带中的半透明像素。',font=font(18),fill='white')
    sheet.save(ROOT/'reports/alpha_trimap_review_v2.png')
    # Every detail is exactly 4x nearest-neighbor, not a fit-to-box thumbnail.
    folder=ROOT/'reports/alpha_edge_details_v2';folder.mkdir(exist_ok=True)
    widths=[(b[2]-b[0])*4 for _,_,b in REGIONS];col_width=max(widths)+24
    heights=[(b[3]-b[1])*4+85 for _,_,b in REGIONS]
    edge=Image.new('RGB',(col_width*3,sum(heights)),(32,34,39));d=ImageDraw.Draw(edge);y=0
    detail_records=[]
    for (key,label,box),height in zip(REGIONS,heights):
        tile_sheet=Image.new('RGB',(col_width*3,height),(32,34,39));td=ImageDraw.Draw(tile_sheet)
        for col,name in enumerate(['white','gray','checker']):
            x=col*col_width
            td.text((x+12,10),f'{label} / {name} / 4x',font=font(23),fill='white')
            td.text((x+12,42),str(box),font=font(17),fill=(200,205,210))
            crop=views[name].crop(box);crop=crop.resize((crop.width*4,crop.height*4),Image.Resampling.NEAREST)
            tile_sheet.paste(crop,(x+12,75))
        file=f'reports/alpha_edge_details_v2/{key}.png';tile_sheet.save(ROOT/file)
        edge.paste(tile_sheet,(0,y));y+=height
        detail_records.append({'region':key,'label':label,'bbox':list(box),'magnification':4,'file':file,'sha256':sha(file)})
    edge.save(ROOT/'reports/rgba_edge_review_v2.png')
    halo=Image.new('RGB',(1080,870),(32,34,39));d=ImageDraw.Draw(halo)
    for i,(asset,key,label,count) in enumerate([
        (old,'halo_before','上一版',metrics['previous_suspected_halo_pixels']),
        (clean,'halo_after','本版',metrics['suspected_halo_pixels'])]):
        mask=Image.open(ROOT/metrics['mask_files'][key]['file'])
        marked=asset.copy();layer=Image.new('RGBA',asset.size,(255,0,180,0));layer.putalpha(mask)
        marked=Image.alpha_composite(marked,layer)
        d.text((i*540+12,12),f'{label}：疑似 {count} px',font=font(23),fill='white')
        halo.paste(composite(marked,(255,255,255)).resize((520,780),Image.Resampling.NEAREST),(i*540+10,55))
    d.text((12,844),'紫色仅为 debug；真实黑色描边可能被标记。未据此自动修图。',font=font(18),fill='white')
    halo.save(ROOT/'reports/suspected_halo_overlay_v2.png')
    if locked!=[sha(metrics[k]) for k in ['input_file','initial_alpha_file','output_file']]:raise ValueError('Image changed during report rendering')
    paths=['reports/rgba_background_review_v2.png','reports/rgba_edge_review_v2.png',
           'reports/alpha_trimap_review_v2.png','reports/suspected_halo_overlay_v2.png']
    write('reports/alpha_cleanup_review_images_v2.json',{'timestamp':now(),'output_sha256':locked[2],
          'files':{p:sha(p) for p in paths},'details':detail_records,'input_images_unchanged':True})
    print('Rendered four backgrounds, trimap, 11 exact-4x region sheets and fixed-detector halo overlay.')


if __name__=='__main__':main()
