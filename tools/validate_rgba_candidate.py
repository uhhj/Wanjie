"""Validate real Alpha, exact canvas/RGB preservation and edge-connected lineage."""
import argparse,json
from pathlib import Path
import numpy as np
from PIL import Image
from rg_common import ROOT, read, write, sha, now
from convert_roman_guard_rgba import edge_connected


def _validate(input_file, output_file, tolerance=2):
    errors=[]
    if not Path(input_file).is_file() or not Path(output_file).is_file():
        return {'status':'FAIL','errors':['Input or output file is missing']}
    with Image.open(input_file) as source:
        rgb=np.array(source)
        size=source.size
        if source.mode!='RGB':
            errors.append('Source must be the approved RGB image')
    with Image.open(output_file) as opened:
        if opened.format!='PNG':errors.append('Output is not PNG')
        if opened.mode!='RGBA':errors.append('Output mode is not RGBA')
        if opened.size!=size:errors.append('Canvas differs from source')
        if errors:return {'status':'FAIL','errors':errors}
        rgba=np.array(opened)
    alpha=rgba[:,:,3]
    transparent=int((alpha==0).sum());opaque=int((alpha==255).sum())
    minimum_count=max(1,int(alpha.size*.01))
    bbox=Image.fromarray(alpha).getbbox()
    if alpha.min()!=0:errors.append('Alpha min must be 0; all-255 fake RGBA is forbidden')
    if alpha.max()!=255:errors.append('Alpha max must be 255')
    if transparent<minimum_count:errors.append('Fewer than 1% fully transparent pixels')
    if opaque<minimum_count:errors.append('Fewer than 1% fully opaque pixels')
    if bbox is None:errors.append('Foreground bounding box is empty')
    if np.any(alpha[0]) or np.any(alpha[-1]) or np.any(alpha[:,0]) or np.any(alpha[:,-1]):
        errors.append('Nontransparent pixels touch the canvas border')
    rgb_changed=int(np.any(rgba[:,:,:3]!=rgb,axis=2).sum())
    if rgb_changed:errors.append('RGB pixels were changed')
    eligible=rgb.max(2)<=tolerance
    background=edge_connected(eligible)
    if not np.array_equal(alpha==0,background):errors.append('Transparent region differs from edge-connected background')
    if np.any(alpha[~background]!=255):errors.append('Foreground must remain opaque; no unrecorded feathering')
    preserved=int((eligible&~background).sum())
    return {'status':'PASS' if not errors else 'FAIL','errors':errors,
            'output_exists':True,'png':True,'mode':'RGBA','dimensions':list(size),
            'alpha_min':int(alpha.min()),'alpha_max':int(alpha.max()),
            'transparent_pixel_count':transparent,'opaque_pixel_count':opaque,
            'minimum_each_count':minimum_count,'foreground_bbox':list(bbox) if bbox else None,
            'rgb_changed_pixel_count':rgb_changed,'disconnected_dark_pixels_preserved':preserved,
            'edge_connected_mask_matches':np.array_equal(alpha==0,background),
            'limitation':'Format/connectivity PASS is not visual approval; connected dark outlines may still be damaged.'}


def validate(input_file, output_file, tolerance=2):
    try:
        return _validate(input_file, output_file, tolerance)
    except (OSError,ValueError) as error:
        return {'status':'FAIL','errors':[str(error)]}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',default='work/05_complete_body_candidate_v2.png')
    parser.add_argument('--output',default='work/05_complete_body_candidate_v2_rgba.png')
    parser.add_argument('--tolerance',type=int,default=2)
    args=parser.parse_args()
    result=validate(ROOT/args.input,ROOT/args.output,args.tolerance)
    result.update(input_file=args.input,output_file=args.output,timestamp=now())
    if (ROOT/args.input).is_file():result['input_sha256']=sha(args.input)
    if (ROOT/args.output).is_file():result['output_sha256']=sha(args.output)
    write('reports/rgba_candidate_validation.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['status']=='PASS' else 2


if __name__=='__main__':raise SystemExit(main())
