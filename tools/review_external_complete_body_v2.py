"""Read-only external V2 intake: render evidence, inspect format, never edit art.

This command does not infer visual approval, run AI stages, switch production
sources, or invoke the downstream part pipeline. Visual decisions are recorded
separately after inspecting the reports and frozen references.
"""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from rg_common import ROOT, check_source, sha, now, write, font, preview, rgba

CANDIDATE = 'work/05_complete_body_candidate_v2.png'
OLD_BODY = 'work/03_complete_body_base.png'
EXPECTED_OLD = {
    'work/01_no_shield.png': '830e7e277d4536285d22422c4f9c24a59cc17827b0e28008d1be28f9ee848a7b',
    'work/02_no_shield_no_sword.png': '2fb867592d48fc664261c814e75e0d1384488e0f73a51ce8d6edd80a81a2df42',
    OLD_BODY: '492adab57065964962b6a7ef635cbb8990a4e774bdb5ec2ee30989049624c5bf',
}


def on_black(im):
    if im.mode == 'RGBA':
        return Image.alpha_composite(Image.new('RGBA', im.size, (0,0,0,255)), im).convert('RGB')
    return im.convert('RGB')


def paste_fit(canvas, im, rect):
    x, y, w, h = rect
    scale = min(w/im.width, h/im.height)
    tile = im.resize((round(im.width*scale),round(im.height*scale)), Image.Resampling.LANCZOS)
    canvas.paste(tile, (x+(w-tile.width)//2, y+(h-tile.height)//2))


def main():
    source = check_source()
    external_source = ROOT.parent/'pictures/OD_UNIT_01_ROMAN_GUARD_RIG_MASTER_V1.png'
    frozen_sha = sha(external_source)
    if frozen_sha != '98642eef9516a371af2e23aea63fbb7156ba506281bc6b245b60c159b7bfc563':
        raise ValueError('STOP: external frozen source hash mismatch')
    for file, expected in EXPECTED_OLD.items():
        if sha(file) != expected:
            raise ValueError('STOP: prior stage changed: '+file)
    original_hash = sha(CANDIDATE)
    with Image.open(ROOT/CANDIDATE) as opened:
        candidate = opened.copy()
        original_format = opened.format
    old = Image.open(ROOT/OLD_BODY).copy()
    has_alpha = 'A' in candidate.getbands()
    alpha = np.asarray(candidate.getchannel('A')) if has_alpha else None
    metadata = {
        'file': CANDIDATE, 'sha256': original_hash, 'format': original_format,
        'mode': candidate.mode, 'dimensions': list(candidate.size),
        'has_alpha_channel': has_alpha,
        'alpha_extrema': [int(alpha.min()), int(alpha.max())] if has_alpha else None,
        'fully_transparent_pixels': int((alpha==0).sum()) if has_alpha else 0,
        'corners': {name:list(candidate.getpixel(point)) for name, point in [
            ('top_left',(0,0)),('top_right',(candidate.width-1,0)),
            ('bottom_left',(0,candidate.height-1)),('bottom_right',(candidate.width-1,candidate.height-1))]},
    }
    try:
        rgba(CANDIDATE)
        rgba_error = None
    except ValueError as e:
        rgba_error = str(e)
    transparent = has_alpha and bool(np.any(alpha==0)) and bool(np.any(alpha>0))
    technical_pass = (original_format=='PNG' and candidate.mode=='RGBA'
                      and candidate.size==source.size and transparent)

    # Full composition: transparent source on checker; candidate shown as supplied.
    full = Image.new('RGB', (1100,960), (32,34,39))
    d = ImageDraw.Draw(full)
    d.text((20,15), 'Complete Body V2 · 外部候选只读验收', font=font(25), fill='white')
    d.text((20,53), '左：冻结 Rig Master（棋盘仅用于预览）', font=font(18), fill='white')
    d.text((570,53), f'右：外部 V2 · {candidate.mode} · {candidate.width}×{candidate.height}', font=font(18), fill='white')
    # Identical viewport sizes preserve equal display scale for proportion review.
    paste_fit(full, preview(source), (20,95,520,795))
    candidate_preview = preview(candidate) if candidate.mode=='RGBA' else candidate.convert('RGB')
    paste_fit(full, candidate_preview, (565,95,520,795))
    d.text((20,906), '原图和候选文件均未修改；黑色背景不能视为透明。', font=font(20), fill='white')
    d.text((20,935), '此图是审查证据，不是骨骼重组结果。', font=font(16), fill=(205,209,215))
    full.save(ROOT/'reports/complete_body_review_v2.png')

    rows = [
        ('头部 / 头盔 / 冠饰', (350,25,680,390)),
        ('颈肩 / 胸甲上缘', (408,332,672,536)),
        ('裙甲 / 上大腿', (302,875,706,1085)),
        ('双腿 / 护胫 / 双脚', (250,1015,860,1475)),
    ]
    details = Image.new('RGB', (1500,1880), (32,34,39))
    d = ImageDraw.Draw(details)
    d.text((20,12), 'V2 局部审查 · 三列使用相同原图坐标 · 无配准或修图', font=font(23), fill='white')
    for i, label in enumerate(['冻结 Rig Master', '旧 03（历史失败底版）', '外部 V2（待验收）']):
        d.text((i*500+20,53), label, font=font(22), fill='white')
    for row, (label, box) in enumerate(rows):
        y=100+row*440
        d.text((20,y), f'{label} · {box}', font=font(19), fill=(220,225,230))
        for col, im in enumerate([source,old,candidate]):
            paste_fit(details,on_black(im).crop(box),(col*500+15,y+36,470,389))
    d.text((20,1860), '局部图在黑底上显示以便比较；不为 RGB 候选创建或推断 Alpha。', font=font(15), fill='white')
    details.save(ROOT/'reports/complete_body_detail_review_v2.png')

    roi_results = []
    if candidate.size == source.size:
        s = np.asarray(source)
        c = np.asarray(candidate.convert('RGB'))
        for name, box in [('helmet_crest',[350,0,700,342]),('visible_face',[570,265,636,360]),
                          ('near_hand',[287,839,375,909]),('near_greave',[295,1140,365,1290])]:
            x0,y0,x1,y1=box
            # Use source's high-alpha interior to avoid comparing transparent RGB.
            valid=s[y0:y1,x0:x1,3]>=240
            delta=np.abs(s[y0:y1,x0:x1,:3].astype(np.int16)-c[y0:y1,x0:x1].astype(np.int16))
            roi_results.append({'region':name,'rect':box,'source_interior_pixels':int(valid.sum()),
                'mean_absolute_rgb_difference':float(delta[valid].mean()) if valid.any() else None,
                'changed_rgb_pixels':int((np.any(delta!=0,axis=2)&valid).sum())})
    after_hash = sha(CANDIDATE)
    if after_hash != original_hash:
        raise ValueError('STOP: candidate changed during read-only review')
    for file, expected in EXPECTED_OLD.items():
        if sha(file) != expected:
            raise ValueError('STOP: prior stage changed during review')
    check_source()
    if sha(external_source) != frozen_sha:
        raise ValueError('STOP: frozen external source changed during review')
    record = {
        'kind': 'EXTERNAL_CANDIDATE_READ_ONLY_INTAKE', 'timestamp': now(),
        'provenance': 'User supplied externally repaired image; external editor/model and intermediate 04 not supplied.',
        'candidate': metadata, 'source_sha256': frozen_sha,
        'prior_stage_hashes': EXPECTED_OLD, 'ai_calls_this_continuation': 0,
        'stages_001_through_005_executed': False,
        'candidate_sha256_before': original_hash, 'candidate_sha256_after': after_hash,
        'candidate_unchanged': True, 'prior_stages_unchanged': True,
        'rgba_same_canvas_transparency_check': 'PASS' if technical_pass else 'FAIL',
        'existing_rgba_loader_error': rgba_error,
        'roi_rgb_comparison': roi_results,
        'comparison_limit': 'RGB pixel differences are evidence of changed pixels, not proof of identity drift, full redraw or a particular external editing process.',
        'art_review_status': 'RECORDED_SEPARATELY_AFTER_VISUAL_INSPECTION',
        'review_images': {file:sha(file) for file in ['reports/complete_body_review_v2.png','reports/complete_body_detail_review_v2.png']},
    }
    write('reports/external_complete_body_v2_intake.json', record)
    print(json.dumps({'candidate':metadata,'technical_check':record['rgba_same_canvas_transparency_check'],
                      'existing_rgba_loader_error':rgba_error,'candidate_unchanged':True},ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
