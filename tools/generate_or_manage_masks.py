"""Render reviewed polygon specs or import masks. Never invent body boundaries."""
import argparse, shutil
from PIL import ImageFilter
from rg_common import *
def render_polygons(polygons):
    w,h=config()['canvas']; im=Image.new('L',(w*4,h*4)); d=ImageDraw.Draw(im)
    for poly in polygons:
        if len(poly)<3: raise ValueError('Polygon requires at least 3 points')
        if any(not (0<=x<w and 0<=y<h) for x,y in poly): raise ValueError('Polygon coordinates outside canvas')
        d.polygon([(round(x*4),round(y*4)) for x,y in poly],fill=255)
    return im.resize((w,h),Image.Resampling.LANCZOS)
def overlay(name,path):
    src=check_source() if name in EQUIPMENT else rgba('work/03_complete_body_base.png')
    m=mask(path); color=Image.new('RGBA',src.size,(0,160,255)); color.putalpha(m.point(lambda x:round(x*.5)))
    sheet([(name+' mask - REVIEW',Image.alpha_composite(src,color))],f'reports/masks/{name}.png',1)
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['render','import','overlay']); p.add_argument('part',choices=PARTS)
    p.add_argument('--input'); a=p.parse_args()
    try:
        check_source(); manifest=read('tools/roman_guard_parts_manifest.json')
        part=next(x for x in manifest['parts'] if x['name']==a.part); path=part['mask']
        if a.action!='overlay':
            if a.part not in EQUIPMENT and not review_ok('complete_body','work/03_complete_body_base.png'):
                raise ValueError('STOP_ART_PIPELINE: complete body has not passed hash-bound art review. See docs/TODO_PART_MASK_REVIEW.md')
            if a.action=='render':
                spec=read(a.input)
                if spec.get('canvas')!=config()['canvas'] or not spec.get('polygons'): raise ValueError('Provide actual source-derived polygons with canvas, not an empty placeholder')
                m=render_polygons(spec['polygons'])
            else:
                m=Image.open(a.input)
                if m.mode!='L' or list(m.size)!=config()['canvas']: raise ValueError('Imported mask must be full-canvas 8-bit L')
            if not m.getbbox(): raise ValueError('Empty masks are not assets')
            dst=ROOT/path
            if dst.exists(): raise ValueError('Mask exists; archive it explicitly before replacement so reviews cannot silently change')
            dst.parent.mkdir(parents=True,exist_ok=True); m.save(dst)
            part.update(mask_sha256=sha(path),mask_status='REVIEW_REQUIRED',review_required=True)
            write('tools/roman_guard_parts_manifest.json',manifest)
        overlay(a.part,path); print(path); return 0
    except (ValueError,FileNotFoundError) as e: print(str(e)); return 2
if __name__=='__main__': raise SystemExit(main())

