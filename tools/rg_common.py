"""Shared read-only source checks and deterministic RGBA pipeline utilities."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json
from PIL import Image, ImageDraw, ImageFont
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PARTS = ['head','helmet','torso','pelvis','arm_near_upper','arm_near_fore','hand_near','arm_far_upper','arm_far_fore','hand_far','leg_near_thigh','leg_near_shin','foot_near','leg_far_thigh','leg_far_shin','foot_far','shield','sword','cape']
EQUIPMENT = ['shield','sword','cape']
DRAW_ORDER = ['cape','leg_far_thigh','leg_far_shin','foot_far','arm_far_upper','arm_far_fore','hand_far','leg_near_thigh','leg_near_shin','foot_near','pelvis','torso','head','helmet','arm_near_upper','arm_near_fore','hand_near','sword','shield']
def read(path): return json.loads((ROOT/path).read_text(encoding='utf-8-sig'))
def write(path, data):
    p=ROOT/path; p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(path): return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
def now(): return datetime.now(timezone.utc).isoformat()
def config(): return read('tools/pipeline_config.json')
def check_source():
    c=config(); p=ROOT/c['source']
    if not p.is_file(): raise ValueError('MANUAL_ACTION_REQUIRED: missing frozen source '+str(p))
    if sha(c['source'])!=c['source_sha256']: raise ValueError('STOP_ART_PIPELINE: frozen source SHA256 mismatch')
    with Image.open(p) as opened: im=opened.copy()
    if im.mode!='RGBA' or list(im.size)!=c['canvas']: raise ValueError('Frozen source RGBA/canvas mismatch')
    return im.copy()
def rgba(path):
    with Image.open(ROOT/path) as opened: im=opened.copy()
    if im.mode!='RGBA': raise ValueError(f'{path}: must be RGBA; conversion alone cannot establish transparency')
    if list(im.size)!=config()['canvas']: raise ValueError(f'{path}: canvas mismatch; no automatic stretching')
    return im.copy()
def mask(path):
    with Image.open(ROOT/path) as opened: im=opened.copy()
    if im.mode!='L' or list(im.size)!=config()['canvas']: raise ValueError(f'{path}: expected full-canvas 8-bit L mask')
    return im.copy()
def alpha_extract(im,m):
    a=np.array(im); w=np.array(m,dtype=np.uint16)
    a[:,:,3]=((a[:,:,3].astype(np.uint16)*w+127)//255).astype(np.uint8)
    a[a[:,:,3]==0,:3]=0
    return Image.fromarray(a)
def checker(size,cell=24):
    yy,xx=np.indices((size[1],size[0])); v=np.where((xx//cell+yy//cell)%2,220,245).astype(np.uint8)
    return Image.fromarray(np.dstack([v,v,v,np.full_like(v,255)]))
def preview(im): return Image.alpha_composite(checker(im.size),im).convert('RGB')
def font(size=22):
    for path in [Path('C:/Windows/Fonts/msyh.ttc'),Path('C:/Windows/Fonts/arial.ttf')]:
        if path.exists(): return ImageFont.truetype(str(path),size)
    return ImageFont.load_default()
def sheet(items,path,columns=2,thumb=(512,768)):
    rows=(len(items)+columns-1)//columns
    out=Image.new('RGB',(columns*thumb[0],rows*(thumb[1]+50)),(38,40,44)); d=ImageDraw.Draw(out)
    for i,(label,im) in enumerate(items):
        x=(i%columns)*thumb[0]; y=(i//columns)*(thumb[1]+50)
        d.text((x+12,y+12),label,font=font(20),fill='white')
        tile=preview(im) if im.mode=='RGBA' else im.convert('RGB')
        tile.thumbnail(thumb,Image.Resampling.LANCZOS)
        out.paste(tile,(x+(thumb[0]-tile.width)//2,y+50))
    (ROOT/path).parent.mkdir(parents=True,exist_ok=True); out.save(ROOT/path)
def review_ok(key,file):
    p=ROOT/'reports/art_reviews.json'
    if not p.exists() or not (ROOT/file).exists(): return False
    r=read('reports/art_reviews.json').get(key,{})
    return r.get('status')=='PASS' and r.get('sha256')==sha(file) and bool(r.get('reviewer')) and bool(r.get('notes'))
