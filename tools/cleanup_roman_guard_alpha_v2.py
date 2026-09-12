"""Trimap-limited deterministic matte and black-background edge decontamination.

No AI, resizing, global blur or opaque RGB editing. Reports require visual review.
"""
from pathlib import Path
import numpy as np
from PIL import Image
from rg_common import ROOT,sha,read,write,now,check_source

RGB='work/05_complete_body_candidate_v2.png'
INITIAL='work/05_complete_body_candidate_v2_rgba.png'
OUTPUT='work/05_complete_body_candidate_v2_rgba_clean.png'
RGB_SHA='042a00a27dac704b23ac0337ecdb27892edf7d490744ec9426ea4f3b44b647da'
INITIAL_SHA='5939747ad6f41a2b372f8f4bcf912d76875a8d2548226d54738f1513d00f6a11'


def offsets(radius):
    return sorted((dy*dy+dx*dx,dy,dx) for dy in range(-radius,radius+1)
                  for dx in range(-radius,radius+1) if dy*dy+dx*dx<=radius*radius)


def morph(mask,radius,dilate):
    h,w=mask.shape;p=np.pad(mask,radius,constant_values=False)
    result=np.zeros_like(mask) if dilate else np.ones_like(mask)
    for _,dy,dx in offsets(radius):
        shifted=p[radius+dy:radius+dy+h,radius+dx:radius+dx+w]
        if dilate:result|=shifted
        else:result&=shifted
    return result


def nearest(mask,ys,xs,radius=12):
    """Exact Euclidean distance/nearest-site transform at queried band pixels.

    Truncated to a documented radius; no unobserved reference color is invented.
    """
    h,w=mask.shape;dist=np.full(len(ys),np.inf);ry=ys.copy();rx=xs.copy()
    pending=np.arange(len(ys))
    for squared,dy,dx in offsets(radius):
        if not len(pending):break
        ny=ys[pending]+dy;nx=xs[pending]+dx
        valid=(ny>=0)&(ny<h)&(nx>=0)&(nx<w)
        hit=np.zeros(len(pending),bool)
        hit[valid]=mask[ny[valid],nx[valid]]
        ids=pending[hit];ry[ids]=ny[hit];rx[ids]=nx[hit];dist[ids]=np.sqrt(squared)
        pending=pending[~hit]
    return dist,ry,rx


def components(mask):
    """8-connected row-run union/find; diagonal plume pixels stay connected."""
    h,w=mask.shape;labels=np.zeros((h,w),np.int32);parent=[0];runs=[];previous=[]
    def find(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    for y,row in enumerate(mask):
        starts=np.flatnonzero(row&~np.r_[False,row[:-1]])
        ends=np.flatnonzero(row&~np.r_[row[1:],False])+1
        current=[];cursor=0
        for l,r in zip(starts,ends):
            label=len(parent);parent.append(label);labels[y,l:r]=label
            while cursor<len(previous) and previous[cursor][1]<l:cursor+=1
            k=cursor
            while k<len(previous) and previous[k][0]<=r:
                root=find(previous[k][2]);parent[find(label)]=root;k+=1
            current.append((int(l),int(r),label));runs.append((y,int(l),int(r),label))
        previous=current
    lookup=np.array([find(i) for i in range(len(parent))]);labels=lookup[labels]
    info={}
    for y,l,r,label in runs:
        root=int(lookup[label]);entry=info.setdefault(root,{'id':root,'area':0,'bbox':[l,y,r,y+1]})
        entry['area']+=r-l;b=entry['bbox'];b[0]=min(b[0],l);b[1]=min(b[1],y);b[2]=max(b[2],r);b[3]=max(b[3],y+1)
    return labels,info


def estimate(rgb,initial):
    m=initial>0;sf=morph(m,2,False);extent=morph(m,3,True);unknown=extent&~sf
    trimap=np.zeros(m.shape,np.uint8);trimap[unknown]=128;trimap[sf]=255
    labels,info=components(m);main_id=max(info,key=lambda k:info[k]['area']);main=labels==main_id
    near_main=morph(main,2,True);removed=np.zeros_like(m)
    stats={'components_removed':0,'pixels_removed':0,'components_preserved_near_foreground':0,
           'components_preserved_color_or_sure_foreground':0,'main_component_area':info[main_id]['area'],
           'connectivity':8,'maximum_removed_area':16,'near_distance_px':2,'component_records':[]}
    for cid,item in info.items():
        if cid==main_id:continue
        x0,y0,x1,y1=item['bbox'];local=labels[y0:y1,x0:x1]==cid
        close=bool(np.any(near_main[y0:y1,x0:x1][local]));fixed=bool(np.any(sf[y0:y1,x0:x1][local]))
        peak=int(rgb[y0:y1,x0:x1][local].max())
        action='PRESERVE_LARGE'
        if close:action='PRESERVE_NEAR_FOR_UNKNOWN_BAND';stats['components_preserved_near_foreground']+=1
        elif fixed or peak>24:
            action='PRESERVE_COLOR_OR_SURE_FOREGROUND';stats['components_preserved_color_or_sure_foreground']+=1
        elif item['area']<=16:
            action='REMOVE_DISTANT_DARK_SPECK';removed[y0:y1,x0:x1]|=local
            stats['components_removed']+=1;stats['pixels_removed']+=item['area']
        stats['component_records'].append({**item,'near_main':close,'peak_channel':peak,'action':action})
    ys,xs=np.where(unknown)
    ds,sy,sx=nearest(sf,ys,xs,12);db,_,_=nearest(~m,ys,xs,12)
    ref=rgb[sy,sx].astype(np.float64);c=rgb[ys,xs].astype(np.float64)
    valid=np.isfinite(ds)
    # Coverage transitions only over approximately one pixel, never a 5px blur.
    geometry=np.clip(db-.5,0,1)
    projection=np.sum(c*ref,axis=1)/np.maximum(np.sum(ref*ref,axis=1),1)
    color_coverage=np.clip(projection,0,1)
    ref_peak=ref.max(1)
    color_coverage=np.where(ref_peak<12,1,color_coverage)
    coverage=geometry*color_coverage
    coverage[~m[ys,xs]]=0  # Previously verified edge-connected background stays background.
    # No nearby sure-foreground color: retain original coverage for review,
    # especially a small colored feather; never invent a color or erase it.
    coverage[~valid]=m[ys[~valid],xs[~valid]].astype(float)
    # A genuine inward dark rim adjacent to the fixed interior remains opaque.
    protected=main&morph(sf,1,True)&m
    coverage[protected[ys,xs]]=1
    coverage[removed[ys,xs]]=0
    coverage[coverage<.02]=0
    alpha=np.zeros(m.shape,np.uint8);alpha[sf]=255
    alpha[ys,xs]=np.rint(coverage*255).astype(np.uint8)
    # Preserve all opaque and zero-alpha RGB; modify only fractional-band pixels.
    result=rgb.copy();partial=(alpha[ys,xs]>0)&(alpha[ys,xs]<255)
    av=alpha[ys[partial],xs[partial]].astype(float)/255
    cv=c[partial];fv=ref[partial]
    raw=cv/av[:,None]
    gain_limit=np.clip((fv.max(1)+20)/np.maximum(cv.max(1),1),1,4)
    bounded=np.minimum(raw,cv*gain_limit[:,None])
    weight=av*av
    mixed=weight[:,None]*bounded+(1-weight[:,None])*fv
    # Limit local brightening and protect against low-alpha noise amplification.
    upper=np.maximum(cv,fv+20)
    mixed=np.clip(np.minimum(mixed,upper),0,255)
    result[ys[partial],xs[partial]]=np.rint(mixed).astype(np.uint8)
    return np.dstack([result,alpha]),trimap,sf,unknown,main,removed,stats,protected


def detect_halo(rgb,alpha,main,sf):
    # Identical fixed ring and reference policy are used for before/after counts.
    ring=morph(main,1,True)&~morph(main,3,False)
    ys,xs=np.where(ring);distance,ry,rx=nearest(sf,ys,xs,12)
    peak=rgb[ys,xs].max(1);ref=rgb[ry,rx].max(1).astype(int)
    suspects=(alpha[ys,xs]>0)&(peak<=32)&(ref>=48)&(ref>=peak.astype(int)+24)&np.isfinite(distance)
    mask=np.zeros(alpha.shape,bool);mask[ys[suspects],xs[suspects]]=True
    return mask


def main():
    check_source()
    if sha(RGB)!=RGB_SHA or sha(INITIAL)!=INITIAL_SHA:raise ValueError('Input hash mismatch')
    rgb=np.array(Image.open(ROOT/RGB));initial=np.array(Image.open(ROOT/INITIAL))
    if rgb.shape!=(1536,1024,3) or initial.shape!=(1536,1024,4):raise ValueError('Unexpected source canvas/mode')
    clean,trimap,sf,unknown,main_mask,removed,stats,protected=estimate(rgb,initial[:,:,3])
    out=ROOT/OUTPUT
    if out.exists():raise ValueError('Existing clean candidate is evidence; do not overwrite or retune globally')
    Image.fromarray(clean).save(out)
    paths={'trimap':'work/masks/alpha_trimap_v2.png','specks':'work/masks/alpha_removed_specks_v2.png',
           'protected_rim':'work/masks/alpha_protected_rim_v2.png',
           'halo_before':'work/masks/suspected_halo_before_v2.png','halo_after':'work/masks/suspected_halo_after_v2.png'}
    previous=detect_halo(rgb,initial[:,:,3],main_mask,sf);new=detect_halo(clean[:,:,:3],clean[:,:,3],main_mask,sf)
    Image.fromarray(trimap).save(ROOT/paths['trimap'])
    for key,mask in [('specks',removed),('protected_rim',protected),('halo_before',previous),('halo_after',new)]:
        Image.fromarray(mask.astype(np.uint8)*255).save(ROOT/paths[key])
    delta=np.abs(clean[:,:,:3].astype(np.int16)-rgb.astype(np.int16));changed=np.any(delta!=0,axis=2)
    a=clean[:,:,3];opaque=a==255;edge=unknown&(a>0)&(a<255)
    assert not np.any(changed&~edge)
    assert not np.any(delta[opaque]) and not np.any(delta[sf])
    assert np.all(a[sf]==255) and np.all(a[trimap==0]==0)
    assert sha(RGB)==RGB_SHA and sha(INITIAL)==INITIAL_SHA
    metrics={'task':'ROMAN_GUARD_ALPHA_MATTE_CLEANUP_V2','input_file':RGB,'input_sha256':RGB_SHA,
      'initial_alpha_file':INITIAL,'initial_alpha_sha256':INITIAL_SHA,'output_file':OUTPUT,'output_sha256':sha(OUTPUT),
      'canvas_width':1024,'canvas_height':1536,'alpha_zero_count':int((a==0).sum()),'alpha_255_count':int(opaque.sum()),
      'fractional_alpha_count':int(edge.sum()),'rgb_changed_total_pixels':int(changed.sum()),
      'rgb_changed_opaque_pixels':int((changed&opaque).sum()),'rgb_changed_edge_pixels':int((changed&edge).sum()),
      'rgb_changed_sure_foreground_pixels':int((changed&sf).sum()),
      'rgb_changed_outside_unknown_pixels':int((changed&~unknown).sum()),
      'max_rgb_difference_opaque':int(delta[opaque].max(initial=0)),
      'max_rgb_difference_edge':int(delta[edge].max(initial=0)),
      'alpha_changed_outside_unknown_pixels':int(((a!=initial[:,:,3])&~unknown).sum()),
      'sure_foreground_pixels':int(sf.sum()),'unknown_band_pixels':int(unknown.sum()),
      'previous_suspected_halo_pixels':int(previous.sum()),'suspected_halo_pixels':int(new.sum()),
      'suspected_halo_reduction_fraction':float(1-new.sum()/max(1,previous.sum())),
      'mask_files':{k:{'file':p,'sha256':sha(p)} for k,p in paths.items()},
      'algorithm':{'trimap_erosion_radius':2,'trimap_dilation_radius':3,'morphology_kernel':'Euclidean disk',
        'distance_transform':'Exact Euclidean nearest-site query restricted to unknown band, radius 12px; unresolved sites retain original Alpha for review unless explicitly classified as removable specks',
        'alpha':'one-pixel geometric coverage * local RGB projection; preserve original connected background and inward rim',
        'edge_rgb':'bounded C/alpha blended with nearest sure-foreground reference; weight alpha squared; local gain cap 4; RGB clamp 0..255',
        'halo_detector':'fixed original main-component ring [-3,+1]px; RGB max<=32, local SF max>=48 and at least 24 brighter; alpha>0',
        'halo_detector_warning':'Heuristic debug only; real dark outlines may be flagged. Identical detector parameters before/after.',
        'global_blur':False,'global_threshold_changed':False},
      'input_unchanged':True,'initial_alpha_unchanged':True,'ai_calls':0,'visual_review':'PENDING','timestamp':now()}
    write('reports/alpha_cleanup_metrics_v2.json',metrics)
    write('reports/alpha_speck_cleanup_v2.json',{**stats,'input_sha256':INITIAL_SHA,'output_sha256':sha(OUTPUT),'timestamp':now()})
    print({k:v for k,v in metrics.items() if k.endswith('count') or k.startswith('rgb_changed') or 'halo_pixels' in k})


if __name__=='__main__':main()
