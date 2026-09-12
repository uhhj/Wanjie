"""Deterministic edge-connected near-black removal; change Alpha only, never RGB."""
import argparse
from collections import deque
from pathlib import Path
import numpy as np
from PIL import Image
from rg_common import ROOT, sha, read, write, now, check_source

OUTPUT = 'work/05_complete_body_candidate_v2_rgba.png'


def edge_connected(eligible):
    """4-connected scanline flood fill, seeded from every eligible border pixel."""
    h,w=eligible.shape
    result=np.zeros((h,w),dtype=bool)
    queue=deque([(0,int(x)) for x in np.flatnonzero(eligible[0])] +
                [(h-1,int(x)) for x in np.flatnonzero(eligible[-1])] +
                [(int(y),0) for y in np.flatnonzero(eligible[:,0])] +
                [(int(y),w-1) for y in np.flatnonzero(eligible[:,-1])])
    while queue:
        y,x=queue.popleft()
        if result[y,x] or not eligible[y,x]:
            continue
        left_stop=np.flatnonzero(~eligible[y,:x])
        right_stop=np.flatnonzero(~eligible[y,x+1:])
        left=int(left_stop[-1]+1) if left_stop.size else 0
        right=int(x+1+right_stop[0]) if right_stop.size else w
        result[y,left:right]=True
        for ny in (y-1,y+1):
            if 0<=ny<h:
                available=eligible[ny,left:right]&~result[ny,left:right]
                starts=np.flatnonzero(available&~np.r_[False,available[:-1]])
                queue.extend((ny,int(left+s)) for s in starts)
    return result


def background_statistics(rgb):
    h,w=rgb.shape[:2]
    border=np.concatenate([rgb[0],rgb[-1],rgb[:,0],rgb[:,-1]])
    n=min(32,h//4,w//4)
    corners={name:tile for name,tile in [('top_left',rgb[:n,:n]),('top_right',rgb[:n,-n:]),
             ('bottom_left',rgb[-n:,:n]),('bottom_right',rgb[-n:,-n:])]}
    return {
        'border_channel_max':int(border.max()),
        'border_max_rgb_percentiles':np.percentile(border.max(1),[0,50,90,95,99,100]).tolist(),
        'corner_sample_size':[n,n],
        'corners':{name:{'median_rgb':np.median(tile.reshape(-1,3),axis=0).tolist(),
                         'channel_max':int(tile.max())} for name,tile in corners.items()},
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tolerance',type=int,default=2)
    args=parser.parse_args()
    if not 0<=args.tolerance<=24:
        raise ValueError('Only conservative near-black tolerance 0..24 is allowed')
    check_source()
    gate=read('reports/complete_body_gate_v2.json')
    input_file=gate.get('visual_source_file',gate['candidate_file'])
    expected=gate.get('visual_source_sha256',gate['candidate_sha256'])
    if sha(input_file)!=expected:
        raise ValueError('Visual source hash mismatch')
    if gate.get('visual_source_checks_status',gate.get('visual_checks_status'))!='PASS':
        raise ValueError('Expected existing ten-item visual approval')
    with Image.open(ROOT/input_file) as opened:
        if opened.mode!='RGB' or opened.format!='PNG':
            raise ValueError('Expected read-only RGB PNG input')
        rgb=np.array(opened)
    stats=background_statistics(rgb)
    medians=np.array([s['median_rgb'] for s in stats['corners'].values()])
    if np.max(medians)>2 or np.max(np.ptp(medians,axis=0))>2 or stats['border_channel_max']>args.tolerance:
        raise ValueError('Border/corners do not establish the same eligible near-black background')
    eligible=rgb.max(2)<=args.tolerance
    background=edge_connected(eligible)
    alpha=np.where(background,0,255).astype(np.uint8)
    rgba=np.dstack([rgb,alpha])
    output=ROOT/OUTPUT
    if output.exists():
        with Image.open(output) as previous:
            if previous.mode!='RGBA' or not np.array_equal(np.array(previous),rgba):
                raise ValueError('Output exists with different pixels; refuse to overwrite evidence')
    else:
        Image.fromarray(rgba).save(output)
    mask_file='work/masks/rgba_background_connected.png'
    Image.fromarray(background.astype(np.uint8)*255).save(ROOT/mask_file)
    if sha(input_file)!=expected:
        raise ValueError('Input changed during conversion')
    record={
        'task':'ROMAN_GUARD_RGBA_BACKGROUND_CONVERSION_V1','timestamp':now(),
        'input':{'file':input_file,'absolute_path':str((ROOT/input_file).resolve()),
                 'sha256':expected,'mode':'RGB','dimensions':[rgb.shape[1],rgb.shape[0]]},
        'output':{'file':OUTPUT,'absolute_path':str(output.resolve()),'sha256':sha(OUTPUT),
                  'mode':'RGBA','dimensions':[rgb.shape[1],rgb.shape[0]],
                  'alpha_min':int(alpha.min()),'alpha_max':int(alpha.max()),
                  'transparent_pixel_count':int((alpha==0).sum()),'opaque_pixel_count':int((alpha==255).sum()),
                  'partial_alpha_pixel_count':0,'foreground_bbox':list(Image.fromarray(alpha).getbbox())},
        'background_sampling':stats,'method':'4-connected scanline flood fill from entire image border',
        'candidate_rule':f'max(R,G,B) <= {args.tolerance}', 'tolerance':args.tolerance,
        'connectivity':4,'feather_radius_px':0,'rgb_changed_pixel_count':0,
        'disconnected_near_black_pixels_preserved':int((eligible&~background).sum()),
        'background_mask':mask_file,'background_mask_sha256':sha(mask_file),
        'input_unchanged':True,'ai_calls':0,'stages_001_through_005_rerun':False,
        'visual_status':'REVIEW_REQUIRED',
        'limitation':'Connectivity alone cannot distinguish background from a dark character region joined to that background. Visual review is mandatory.'}
    write('reports/rgba_conversion.json',record)
    print(record['output'])


if __name__=='__main__':
    main()
