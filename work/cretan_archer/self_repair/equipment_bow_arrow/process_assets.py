"""Deterministic extraction/compositing of genuine independent weapon edits.

Raw tool images are RGB with baked checker: no claim of native alpha/mask.
Only the missing bow grip uses generated pixels. Full arrow is AI completion.
"""
from pathlib import Path
from collections import deque
import json, hashlib
from datetime import datetime, timezone
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[4]
WORK = Path(__file__).resolve().parent
REPORT = ROOT/'reports/cretan_archer/self_repair/bow_arrow'
SOURCE = ROOT/'art_source/odyssey/cretan_archer/OD_UNIT_02_CRETAN_ARCHER_RIG_MASTER_V1.png'
REPORT.mkdir(parents=True, exist_ok=True)

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def savejson(name,data):
    (REPORT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def component_mask(rgb, region, threshold=155):
    """Keep foreground enclosed by dark colored outline; remove ONLY edge-connected gray checker.
    Restrict analysis to inspected object crop. Neutral light arrow feathers inside
    the continuous outline remain foreground. Never removes all pale pixels.
    """
    a=np.asarray(rgb).astype(np.int16)
    h,w=a.shape[:2]
    neutral=(np.max(a,axis=2)-np.min(a,axis=2)<28)&(a.mean(axis=2)>threshold)
    seen=np.zeros((h,w),bool);todo=deque()
    for x in range(w):
        for y in (0,h-1):
            if neutral[y,x] and not seen[y,x]:seen[y,x]=True;todo.append((y,x))
    for y in range(h):
        for x in (0,w-1):
            if neutral[y,x] and not seen[y,x]:seen[y,x]=True;todo.append((y,x))
    while todo:
        y,x=todo.popleft()
        for yy,xx in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
            if 0<=yy<h and 0<=xx<w and neutral[yy,xx] and not seen[yy,xx]:
                seen[yy,xx]=True;todo.append((yy,xx))
    fg=~seen
    # Explicit region inspected from raw image excludes unrelated background noise.
    reg=Image.new('L',(w,h));ImageDraw.Draw(reg).polygon(region,fill=255)
    fg&=np.array(reg)>0
    return fg

def runs(row):
    padded=np.pad(row,(1,1));edges=np.diff(padded.astype(int));return list(zip(np.where(edges==1)[0],np.where(edges==-1)[0]))

def bow_asset():
    src=np.array(Image.open(SOURCE).convert('RGBA'))
    out=src.copy();out[:,:,3]=0
    # Per-row rightmost wooden limb: bounded to the inspected weapon's region.
    # Forearm/hand is excluded before selecting components.
    for y in range(28,1410):
        if 673<=y<=761: continue
        segments=[(s+700,e+700) for s,e in runs(src[y,700:930,3]>80) if e-s>=3]
        if not segments:continue
        s,e=segments[-1]
        if y>=1400 and s<740:continue  # far shoe, not the bow tip
        # Narrow stray pixels never replace the large bow limb.
        if y>60 and y<1380:
            large=[p for p in segments if p[1]-p[0]>=15]
            if large:s,e=large[-1]
        s=max(700,s-1);e=min(930,e+1)
        # Remove only two attached original string stubs. The bow string is a
        # separate animated part; these inspected cut lines follow the wood edge.
        if 151<=y<=201:s=max(s,round(float(np.interp(y,[151,175,201],[789,790,791]))))
        if 1215<=y<=1240:s=max(s,round(float(np.interp(y,[1215,1240],[725,719]))))
        out[y,s:e]=src[y,s:e]
    raw=Image.open(WORK/'bow_grip_raw.png').convert('RGB')
    rgb=np.array(raw)
    fg=component_mask(raw,[(270,0),(690,0),(690,1535),(270,1535)])
    # Model reference transform: crop (738,536,994,920), scale=4.
    # Source hand occlusion has known upper/lower wood edges. Align each repair
    # row horizontally to these actual grip edges; use no model pixels elsewhere.
    generated=Image.fromarray(np.dstack((rgb,np.uint8(fg)*255)),'RGBA')
    generated.save(WORK/'bow_grip_rgba_derived.png')
    patch=np.zeros_like(src); mask=np.zeros(src.shape[:2],np.uint8)
    for y in range(673,762):
        sy=(y-536)*4
        ss=runs(fg[sy]);ss=[v for v in ss if v[1]-v[0]>80]
        if not ss:raise RuntimeError(f'No generated grip row {sy}')
        a,b=max(ss,key=lambda v:v[1]-v[0])
        t=(y-673)/(762-673)
        left=round(830*(1-t)+820*t);right=round(870*(1-t)+860*t)
        # One row resampled from four raw source rows, all already inside matte.
        strip=generated.crop((a,sy,b,min(sy+4,raw.height))).resize((right-left,1),Image.Resampling.LANCZOS)
        patch[y,left:right]=np.array(strip)[0]
        out[y,left:right]=patch[y,left:right];mask[y,left:right]=255
    # Transparent RGB scrub only: eliminates hidden discarded pixels, does not recolor wood.
    out[out[:,:,3]==0,:3]=0
    Image.fromarray(out).save(WORK/'bow_full_candidate.png')
    Image.fromarray(mask).save(WORK/'bow_grip_completion_mask.png')
    Image.fromarray(np.uint8((out[:,:,3]>0)&(mask==0))*255).save(WORK/'bow_visible_extraction_mask.png')
    Image.fromarray(patch).save(WORK/'bow_grip_patch_same_canvas.png')
    non_generated=(out[:,:,3]>0)&(mask==0)
    assert np.array_equal(out[non_generated],src[non_generated])
    return {'file':str(WORK/'bow_full_candidate.png'),'sha256':sha(WORK/'bow_full_candidate.png'),
            'canvas':[1024,1536],'mode':'RGBA','bow_grip':[844,725],
            'source_pixels_preserved':int(non_generated.sum()),'source_pixels_changed_outside_completion':0,
            'generated_pixel_count':int((mask>0).sum()),'completion_bbox':[820,673,870,762],
            'native_tool_alpha':False,'alpha_method':'inspected source row components; edge-connected gray-checker removal on generated crop; horizontal per-row alignment restricted to hand-covered grip',
            'tool_output_scope':'grip crop only; no person; original visible bow restored in final composite',
            'tip_bbox':Image.fromarray(out).getbbox(),'string_included':False}

def arrow_asset():
    raw=Image.open(WORK/'arrow_raw.png').convert('RGB');w,h=raw.size
    # Coordinates normalized to the visually reviewed 1374x1145 tool output.
    region=[(0,.40*h),(w,.40*h),(w,.60*h),(0,.60*h)]
    fg=component_mask(raw,region)
    # Select largest connected foreground component to discard isolated checker artifacts.
    seen=np.zeros_like(fg);best=[]
    for yy,xx in zip(*np.where(fg)):
        if seen[yy,xx]:continue
        stack=[(int(yy),int(xx))];seen[yy,xx]=1;part=[]
        while stack:
            y,x=stack.pop();part.append((y,x))
            for y2,x2 in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
                if 0<=y2<h and 0<=x2<w and fg[y2,x2] and not seen[y2,x2]:seen[y2,x2]=1;stack.append((y2,x2))
        if len(part)>len(best):best=part
    matte=np.zeros((h,w),np.uint8)
    for y,x in best:matte[y,x]=255
    rgba=np.dstack((np.array(raw),matte));rgba[matte==0,:3]=0
    im=Image.fromarray(rgba);im.save(WORK/'arrow_rgba_derived.png')
    bbox=im.getbbox();isolated=im.crop(bbox)
    length=680;rh=round(isolated.height*length/isolated.width)
    scaled=isolated.resize((length,rh),Image.Resampling.LANCZOS)
    out=Image.new('RGBA',(1024,1536));origin=(280,725-rh//2);out.alpha_composite(scaled,origin)
    out.save(WORK/'arrow_single_candidate.png')
    return {'file':str(WORK/'arrow_single_candidate.png'),'sha256':sha(WORK/'arrow_single_candidate.png'),
            'canvas':[1024,1536],'mode':'RGBA','native_tool_alpha':False,'raw_size':list(raw.size),
            'raw_object_bbox':bbox,'scale':length/isolated.width,'placement':origin,
            'nock_pivot':[282,725],'tip_approx':[958,725],'length_source_pixels':length,
            'ai_completed':True,'source_pixels_preserved':0,
            'design_reference':'Rig Master cream feather with muted dark-red tips and brown shaft; simple iron head completion',
            'alpha_method':'edge-connected neutral-checker flood only; retain largest outlined arrow component; RGBA downscale with Lanczos',
            'pending_rig_calibration':'length, nock/socket and bow/string draw position verified during actual attack rig review'}

def review():
    canvas=Image.new('RGB',(1300,1100),'#dedbd6');d=ImageDraw.Draw(canvas)
    for idx,bg in enumerate(('white','#808080','#4b6c94')):
        tile=Image.new('RGBA',(400,660),bg);im=Image.open(WORK/'bow_full_candidate.png');im=im.crop((690,0,920,1440)).resize((105,657),Image.Resampling.LANCZOS);tile.alpha_composite(im,(148,0));canvas.paste(tile.convert('RGB'),(idx*430,30));d.text((idx*430+10,8),['WHITE','50% GRAY','BLUE'][idx],fill='black')
    grip=Image.open(WORK/'bow_full_candidate.png').crop((809,647,884,789)).resize((225,426),Image.Resampling.NEAREST)
    t=Image.new('RGBA',grip.size,'white');t.alpha_composite(grip);canvas.paste(t.convert('RGB'),(25,670));d.text((270,690),'GRIP: AI only inside prior hand occlusion',fill='black')
    arrow=Image.open(WORK/'arrow_single_candidate.png').crop((260,660,980,790));bg=Image.new('RGBA',arrow.size,'white');bg.alpha_composite(arrow);canvas.paste(bg.convert('RGB'),(280,725))
    for i,ht in enumerate((256,192)):
        scale=ht/1340;arr=arrow.resize((round(arrow.width*scale),round(arrow.height*scale)),Image.Resampling.LANCZOS);b=Image.new('RGBA',arr.size,'#808080');b.alpha_composite(arr);canvas.paste(b.convert('RGB'),(300,900+i*60));d.text((300,880+i*60),f'Arrow at body height {ht}px (100%)',fill='black')
    canvas.save(REPORT/'weapon_completion_review.png')

if __name__=='__main__':
    bow=bow_asset();arrow=arrow_asset();review()
    savejson('weapon_candidates.json',{'timestamp':datetime.now(timezone.utc).isoformat(),'source_sha256':sha(SOURCE),'bow':bow,'arrow':arrow,'status':'VISUAL_REVIEW_REQUIRED_CANDIDATES_ONLY','formal_assets_modified':False})
    print(json.dumps({'bow':bow,'arrow':arrow},indent=2))
