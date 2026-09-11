"""Pad a real RGBA part onto source canvas at an explicit measured offset. No stretch."""
import argparse
from rg_common import *
def normalize_image(im,canvas,offset=None):
    if im.mode!='RGBA': raise ValueError('RGBA input required; do not fabricate transparency by mode conversion')
    if im.getchannel('A').getextrema()[1]==0: raise ValueError('Empty image cannot be a part')
    if im.size==tuple(canvas):
        if offset not in [None,(0,0)]: raise ValueError('Full-canvas image cannot be translated by normalization')
        return im.copy()
    if offset is None: raise ValueError('Cropped input requires an explicit source-space --x and --y offset')
    x,y=offset; w,h=canvas
    if x<0 or y<0 or x+im.width>w or y+im.height>h: raise ValueError('Placement would clip pixels')
    out=Image.new('RGBA',(w,h)); out.paste(im,(x,y)); return out
def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('input'); p.add_argument('output'); p.add_argument('--x',type=int); p.add_argument('--y',type=int); a=p.parse_args()
    try:
        check_source(); dst=Path(a.output).resolve()
        if dst==(ROOT/config()['source']).resolve() or str(dst)==read('art_source/odyssey/roman_guard/source_manifest.json')['external_source']: raise ValueError('Frozen source is read-only')
        if dst.exists(): raise ValueError('Output already exists; use a versioned destination')
        if (a.x is None)!=(a.y is None): raise ValueError('Both offsets are required')
        out=normalize_image(Image.open(a.input),config()['canvas'],None if a.x is None else (a.x,a.y))
        dst.parent.mkdir(parents=True,exist_ok=True); out.save(dst); print(str(dst)); return 0
    except (ValueError,FileNotFoundError) as e: print(str(e)); return 2
if __name__=='__main__': raise SystemExit(main())

