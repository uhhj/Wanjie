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

def body_source():
    return config().get('complete_body_source','work/03_complete_body_base.png')

def body_review_ok():
    """Combat acceptance is scoped and hash-bound; never relax per-part art gates."""
    if 'complete_body_source' not in config():
        return review_ok('complete_body','work/03_complete_body_base.png')
    try:
        source=body_source(); gate=read(config()['complete_body_gate'])
        render=read('reports/combat_scale_render_manifest.json')
        if gate.get('status')!='PASS_WITH_NON_BLOCKING_HIRES_EDGE_ARTIFACTS': return False
        if gate.get('combat_scale_visual_review')!='PASS' or gate.get('scope')!='COMBAT_RIG_ASSET': return False
        if gate.get('source')!=source or gate.get('source_sha256')!=sha(source): return False
        if not review_ok('complete_body_combat',source): return False
        if gate.get('render_manifest_sha256')!=sha('reports/combat_scale_render_manifest.json'): return False
        if render['source_sha256']!=sha(source) or render['source']!=source: return False
        if sha(render['review_image'])!=render['review_image_sha256']: return False
        if sorted(r['character_height_px'] for r in render['rows'])!=[128,192,256]: return False
        required={'no_obvious_halo','continuous_silhouette','no_visible_plume_specks','natural_shoulder','natural_greaves','no_floating_sole_chunks','no_isolated_noise_over_one_display_pixel','identity_structure_transparency_normal'}
        if set(gate['visual_checks'])!={'128','192','256'}: return False
        if any(set(row)!=required or any(v!='PASS' for v in row.values()) for row in gate['visual_checks'].values()): return False
        for row in render['rows']:
            if {x['background'] for x in row['composites']}!={'white','gray_50'}: return False
            if any(x['sha256']!=sha(x['file']) for x in row['composites']): return False
        a=np.array(rgba(source))[:,:,3]
        return bool(a.min()==0 and a.max()==255 and ((a>0)&(a<255)).any())
    except (KeyError,ValueError,FileNotFoundError): return False
