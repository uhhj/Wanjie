"""Render immutable body at actual combat character heights; never repairs source pixels."""
from rg_common import *

SOURCE = 'work/05_complete_body_candidate_v2_rgba_clean.png'
HEIGHTS = (256, 192, 128)

def scaled_character(im, height):
    # Review-only crop. Production sources and all part canvases remain full size.
    bbox = im.getchannel('A').getbbox()
    crop = im.crop(bbox)
    size = (round(crop.width * height / crop.height), height)
    # Explicit premultiplied resize prevents transparent RGB bleeding into the sprite.
    return crop.convert('RGBa').resize(size, Image.Resampling.LANCZOS).convert('RGBA'), bbox

def main():
    before = sha(SOURCE)
    im = rgba(SOURCE)
    out = Image.new('RGB', (660, 830), '#e7e9ec')
    d = ImageDraw.Draw(out)
    d.text((16, 10), 'COMBAT SCALE | 100% / 1 image pixel = 1 display pixel', font=font(17), fill='black')
    d.text((16, 36), 'White / 50% gray. No battlefield background asset available.', font=font(15), fill='black')
    rows=[]; y=70
    folder=ROOT/'reports/combat_scale'; folder.mkdir(parents=True, exist_ok=True)
    for height in HEIGHTS:
        sprite, bbox=scaled_character(im,height)
        entry={'character_height_px':height,'sprite_size':list(sprite.size),'source_alpha_bbox':list(bbox),'composites':[]}
        for col,(label,color) in enumerate([('white',(255,255,255)),('gray_50',(128,128,128))]):
            tile=Image.new('RGBA',(314,height+12),color+(255,))
            tile.alpha_composite(sprite,((314-sprite.width)//2,6))
            name=f'reports/combat_scale/body_{height}_{label}.png'
            tile.convert('RGB').save(ROOT/name)
            d.text((16+col*330,y),f'{height}px character / {label}',font=font(17),fill='black')
            out.paste(tile.convert('RGB'),(8+col*330,y+26))
            entry['composites'].append({'file':name,'sha256':sha(name),'background':label,'display_scale':1})
        rows.append(entry); y+=height+54
    path='reports/combat_scale_visual_review.png'; out.save(ROOT/path)
    assert sha(SOURCE)==before
    write('reports/combat_scale_render_manifest.json',{'gate_id':'COMBAT_SCALE_VISUAL_GATE_V1','source':SOURCE,'source_sha256':before,'source_canvas':list(im.size),'source_unchanged':True,'resampling':'premultiplied RGBA LANCZOS; no enlargement after rendering','battlefield_background':{'status':'NOT_AVAILABLE','searched':['repository filename inventory','D:/Wanjie/documents/pictures'],'note':'No artwork was repurposed as a battlefield.'},'rows':rows,'review_image':path,'review_image_sha256':sha(path),'timestamp':now()})

if __name__=='__main__': main()
