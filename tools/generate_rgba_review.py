"""Render Alpha review composites without changing input or candidate files."""
from PIL import Image,ImageDraw
from rg_common import ROOT,read,sha,write,font,checker,now


def fit(canvas,tile,box):
    x,y,w,h=box
    scale=min(w/tile.width,h/tile.height)
    tile=tile.resize((round(tile.width*scale),round(tile.height*scale)),Image.Resampling.NEAREST)
    canvas.paste(tile,(x+(w-tile.width)//2,y+(h-tile.height)//2))


def main():
    record=read('reports/rgba_conversion.json')
    source_path=record['input']['file']; output_path=record['output']['file']
    before=[sha(source_path),sha(output_path)]
    source=Image.open(ROOT/source_path).copy(); output=Image.open(ROOT/output_path).copy()
    white=Image.alpha_composite(Image.new('RGBA',output.size,'white'),output).convert('RGB')
    grey=Image.alpha_composite(Image.new('RGBA',output.size,(128,128,128,255)),output).convert('RGB')
    checked=Image.alpha_composite(checker(output.size,16),output).convert('RGB')
    full=Image.new('RGB',(1080,1730),(33,35,40)); d=ImageDraw.Draw(full)
    for i,(label,tile) in enumerate([('A 原 RGB 黑底',source),('B RGBA 合成白底',white),
                                    ('C RGBA 合成 50% 灰底',grey),('D RGBA 棋盘背景',checked)]):
        x=(i%2)*540;y=(i//2)*850
        d.text((x+16,y+14),label,font=font(24),fill='white')
        fit(full,tile,(x+10,y+60,520,780))
    d.text((18,1702),'仅改变 Alpha；RGB 原值逐像素保留。格式 PASS 不代表描边通过。',font=font(18),fill='white')
    full.save(ROOT/'reports/rgba_background_review.png')
    crops=[('红色冠饰',(343,25,691,186)),('头盔 / 后缘',(403,273,650,412)),
           ('肩甲 / 描边',(289,371,534,588)),('近侧手 / 手腕',(270,783,395,934)),
           ('远侧手 / 手腕',(665,733,796,876)),('裙甲下摆',(314,884,710,1030)),
           ('双腿外轮廓',(267,1018,719,1345)),('鞋底 / 凉鞋',(251,1326,850,1469))]
    edges=Image.new('RGB',(1410,2530),(33,35,40));d=ImageDraw.Draw(edges)
    for i,title in enumerate(['原 RGB','RGBA 白底','RGBA 棋盘']):
        d.text((i*470+15,12),title,font=font(24),fill='white')
    for row,(label,box) in enumerate(crops):
        y=55+row*305
        d.text((15,y),label+' '+str(box),font=font(19),fill='white')
        for col,tile in enumerate([source,white,checked]):
            fit(edges,tile.crop(box),(col*470+12,y+33,445,265))
    d.text((15,2505),'同坐标放大；无模糊，无 RGB 修色，Alpha 为 0 或 255。',font=font(17),fill='white')
    edges.save(ROOT/'reports/rgba_edge_review.png')
    # Standalone critical detail retains native inspection resolution in chat.
    detail=Image.new('RGB',(1480,660),(33,35,40));d=ImageDraw.Draw(detail)
    for row,(label,box) in enumerate([('头盔后缘',(400,294,552,398)),('鞋底',(255,1400,445,1468))]):
        y=row*330
        for col,tile in enumerate([source,white,checked]):
            d.text((col*490+12,y+8),label+' / '+['RGB','白底','棋盘'][col],font=font(20),fill='white')
            fit(detail,tile.crop(box),(col*490+10,y+44,470,274))
    detail.save(ROOT/'reports/rgba_critical_edge_detail.png')
    if before!=[sha(source_path),sha(output_path)]:raise ValueError('Input/output changed during review rendering')
    paths=['reports/rgba_background_review.png','reports/rgba_edge_review.png','reports/rgba_critical_edge_detail.png']
    write('reports/rgba_review_images.json',{'timestamp':now(),'input_sha256':before[0],
            'output_sha256':before[1],'files':{p:sha(p) for p in paths},'read_only':True})
    print('Rendered RGB, white, grey and checker composites plus edge details.')


if __name__=='__main__':main()
