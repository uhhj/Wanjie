"""Prepare two local-mask DRAFTS and truthful blocked records. No AI invocation.

This does not repair any character pixels or unlock the production pipeline.
It refuses changed baselines and existing fix outputs / executed job records.
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw
from rg_common import ROOT, check_source, sha, now, write, preview, font, PARTS

FROZEN = '98642eef9516a371af2e23aea63fbb7156ba506281bc6b245b60c159b7bfc563'
BASELINES = {
    'work/01_no_shield.png': '830e7e277d4536285d22422c4f9c24a59cc17827b0e28008d1be28f9ee848a7b',
    'work/02_no_shield_no_sword.png': '2fb867592d48fc664261c814e75e0d1384488e0f73a51ce8d6edd80a81a2df42',
    'work/03_complete_body_base.png': '492adab57065964962b6a7ef635cbb8990a4e774bdb5ec2ee30989049624c5bf',
}
BODY = 'work/03_complete_body_base.png'
BLOCKED = 'BLOCKED_LOCAL_INPAINT_UNAVAILABLE'
JOBS = [
    ('004_fix_skirt_seam', BODY, 'work/masks/fix_skirt_seam_v2.png', 'work/04_skirt_fixed.png'),
    ('005_remove_unapproved_collar', 'work/04_skirt_fixed.png',
     'work/masks/remove_unapproved_collar_v2.png', 'work/05_complete_body_candidate_v2.png'),
]
PROMPTS = [
    '''只修复当前罗马军团盾兵裙甲区域的拼接和不自然连续问题。
严格延续周围已经存在的罗马裙甲结构、铁灰/青铜甲片、暗红内衬和皮革连接方式。
让裙甲从腰部向腿部自然、连续、对称合理地衔接。
不得重新设计裙甲。不得新增甲片类型。不得改变人物姿势、腿部、胸甲、头盔、脸或其他装备。
只消除局部 AI 拼接痕迹并恢复连续结构。
仅在提供的局部 mask 白色区域内 inpaint，黑色区域保护；不要全图重绘。
保持 1024×1536 原坐标和真实透明 RGBA，不画棋盘格，不裁切。
''',
    '''移除当前补全过程中新出现、但原始罗马军团盾兵设计中不存在的高领甲或额外颈部装甲。
恢复为与原角色设计一致的颈部、肩部和胸甲上缘过渡。
严格参考原设计中已经可见的盔甲结构。不得创造新的甲片、领甲、肩甲或装饰。
不得修改头部、头盔、脸、身体比例或胸甲主体。只修复披风移除后必须存在的合理身体/甲胄结构。
参考优先级：DESIGN_V1 > RIG_MASTER_V1 > COMBAT_LOOK_V1。不得使用 CODEX 原画决定隐藏颈甲结构。
只在 mask 白色区域内 inpaint，黑色区域保护；保留现有肩甲主体，不增加装备，不全图重绘。
保持 1024×1536 原坐标和真实透明 RGBA，不画棋盘格，不裁切。
''',
]


def main():
    frozen = check_source()
    external = ROOT.parent / 'pictures/OD_UNIT_01_ROMAN_GUARD_RIG_MASTER_V1.png'
    if sha(external) != FROZEN:
        raise SystemExit('STOP: external frozen source mismatch')
    for file, expected in BASELINES.items():
        if sha(file) != expected:
            raise SystemExit('STOP: baseline changed: ' + file)
    if not (ROOT / 'reports/complete_body_fix_plan.md').is_file():
        raise SystemExit('STOP: review and fix plan must exist first')
    for job, _, _, output in JOBS:
        if (ROOT / output).exists():
            raise SystemExit('STOP: actual fix output exists; do not replace its evidence')
        record = ROOT / f'reports/ai_jobs/{job}.json'
        if record.exists():
            old = json.loads(record.read_text(encoding='utf-8'))
            if old.get('attempted') is not False or old.get('status') != 'NOT_RUN':
                raise SystemExit('STOP: job progressed; do not overwrite record')

    size = frozen.size
    body = Image.open(ROOT / BODY).copy()
    skirt = Image.new('L', size, 0)
    ds = ImageDraw.Draw(skirt)
    paths = [
        [[331,949],[345,954],[365,958],[386,945],[409,966],[440,991],[468,1014],[480,1023]],
        [[478,945],[500,957],[527,976],[547,994],[568,1012],[586,1034],[599,1056]],
    ]
    for points in paths:
        ds.line([tuple(p) for p in points], fill=255, width=18, joint='curve')
        for x, y in points:
            ds.ellipse((x-9,y-9,x+9,y+9), fill=255)
    collar_points = [[460,350],[478,356],[512,375],[556,397],[563,405],
                     [564,430],[550,431],[511,414],[472,394],[442,385],
                     [439,377],[453,368]]
    collar = Image.new('L', size, 0)
    ImageDraw.Draw(collar).polygon([tuple(p) for p in collar_points], fill=255)
    masks = [skirt, collar]
    prepared = now()
    mask_metadata = []
    for (job, input_file, mask_file, output), prompt, m in zip(JOBS, PROMPTS, masks):
        (ROOT / mask_file).parent.mkdir(parents=True, exist_ok=True)
        m.save(ROOT / mask_file)
        prompt_file = f'work/prompts/{job}.txt'
        (ROOT / prompt_file).parent.mkdir(parents=True, exist_ok=True)
        # Keep prompt hashes stable when Git checks out text on another platform.
        (ROOT / prompt_file).write_bytes(prompt.encode('utf-8'))
        pixels = int(np.count_nonzero(np.asarray(m)))
        meta = {'file': mask_file, 'sha256': sha(mask_file), 'mode': m.mode,
                'canvas': list(m.size), 'editable_pixels': pixels,
                'editable_canvas_percent': round(100*pixels/(size[0]*size[1]), 4),
                'bbox_exclusive': list(m.getbbox()), 'review_status': 'DRAFT_REVIEW_REQUIRED',
                'semantics': '255 edit; 0 protect; convert only per verified editor contract',
                'geometry_source': 'visually inspected seams / collar on current 03',
                'geometry': paths if job.startswith('004') else collar_points}
        mask_metadata.append(meta)
        write(f'reports/ai_jobs/{job}.json', {
            'job_id': job, 'status': 'NOT_RUN', 'attempted': False,
            'reason': BLOCKED, 'input_file': input_file,
            'input_sha256': sha(input_file) if (ROOT/input_file).is_file() else None,
            'input_status': 'EXISTS' if (ROOT/input_file).is_file() else 'WAITING_FOR_JOB_004',
            'mask': mask_file, 'mask_sha256': sha(mask_file),
            'mask_review_status': 'DRAFT_REVIEW_REQUIRED',
            'prompt_file': prompt_file, 'prompt': prompt, 'prompt_sha256': sha(prompt_file),
            'model_tool_identifier': None, 'output_file': output, 'output_sha256': None,
            'output_exists': False, 'timestamp': prepared, 'timestamp_kind': 'preparation_only',
            'invoked_at': None, 'depends_on': None if job.startswith('004') else JOBS[0][0],
            'native_mask_support_required': True,
            'note': 'Prepared request, not an AI call. No post-compositing workaround allowed.'})

    write('work/masks/complete_body_fix_masks_v2.json', {
        'candidate_file': BODY, 'candidate_sha256': sha(BODY),
        'stage_005_geometry_binding': 'Draft on 03; recheck against actual 04 before job 005',
        'masks': mask_metadata})
    references = []
    for priority, (suffix, expected) in enumerate([
        ('DESIGN_V1', 'e51470290606b2167f723fb84d5178bdb2af4acf298c519d73143e5cb6aa826d'),
        ('RIG_MASTER_V1', FROZEN),
        ('COMBAT_LOOK_V1', 'e681b196e3a2865bd5866803557952346cbc53d7b2870976d6296a15a3c75a1c')], 1):
        path = ROOT.parent / f'pictures/OD_UNIT_01_ROMAN_GUARD_{suffix}.png'
        if sha(path) != expected:
            raise SystemExit('STOP: reference changed: ' + str(path))
        references.append({'priority': priority, 'path': str(path), 'sha256': expected,
                           'visually_reviewed': True})
    write('reports/complete_body_fix_references_v2.json', {
        'references': references, 'codex_reference_used': False,
        'limitation': 'Cloth obscures neck/shoulder; hidden armor is not an approved known design.'})

    # Diagnostic overlays only: the character input and all previous outputs stay untouched.
    out = Image.new('RGB', (1200,1080), (31,33,38))
    draw = ImageDraw.Draw(out)
    for index, (m, label, box) in enumerate(zip(masks,
            ['004 裙甲接缝 · MASK 草案', '005 高领甲 · MASK 草案'],
            [(310,920,622,1082),(418,330,600,455)])):
        x = index*600
        draw.text((x+20,15), label, font=font(22), fill='white')
        draw.text((x+20,48), '未执行 AI · 紫色仅为编辑范围', font=font(18), fill='white')
        tint = Image.new('RGBA', size, (230,30,195,0))
        tint.putalpha(m.point(lambda v: 95 if v else 0))
        over = Image.alpha_composite(body, tint)
        whole = preview(over)
        whole.thumbnail((560,575), Image.Resampling.LANCZOS)
        out.paste(whole, (x+(600-whole.width)//2,85))
        detail = preview(over).crop(box)
        detail.thumbnail((560,360), Image.Resampling.LANCZOS)
        # Enlarge inspection crop explicitly; this is a report, never a part texture.
        factor = min(560/detail.width, 345/detail.height)
        detail = detail.resize((round(detail.width*factor),round(detail.height*factor)), Image.Resampling.NEAREST)
        out.paste(detail, (x+(600-detail.width)//2,695))
        draw.text((x+20,1040), f'局部范围：{mask_metadata[index]["editable_canvas_percent"]}% 画布',
                  font=font(18), fill='white')
    out.save(ROOT / 'reports/complete_body_fix_masks_review.png')

    write('reports/complete_body_gate_v2.json', {
        'task': 'FIX_COMPLETE_BODY_GATE_V1', 'status': BLOCKED,
        'candidate_file': JOBS[1][3], 'candidate_exists': False, 'candidate_sha256': None,
        'skirt_seam_pass': None, 'collar_design_pass': None,
        'body_completeness_pass': None, 'identity_consistency_pass': None,
        'evaluation_status': 'NOT_EVALUATED_MISSING_V2_CANDIDATE',
        'baseline_file': BODY, 'baseline_sha256': sha(BODY),
        'baseline_observations': {'skirt_seam': 'FAIL', 'collar_design': 'FAIL',
            'body_completeness': 'Both hands, legs and feet visible; shield/sword/cape absent',
            'identity': 'Face/helmet/crest protected; collar design drift remains'},
        'remaining_issues': ['Visible diagonal skirt/hem/thigh splice remains on current 03',
                             'Unsupported raised metal collar remains on current 03',
                             'No verified reliable native local-mask inpainting interface; jobs 004/005 not run'],
        'formal_parts': {'required': len(PARTS), 'passed': 0, 'missing': len(PARTS)},
        'recomposition': 'NOT_RUN', 'joint_rotation': 'NOT_RUN',
        'godot_handoff': 'NOT_READY', 'timestamp': prepared})

    for file, expected in BASELINES.items():
        assert sha(file) == expected, file
    assert sha(external) == FROZEN
    check_source()
    assert not list((ROOT / 'assets/units/odyssey/roman_guard/parts').glob('*.png'))
    assert all(not (ROOT / output).exists() for _, _, _, output in JOBS)
    assert all(m.mode == 'L' and m.size == size for m in masks)
    assert not np.any(np.asarray(collar)[:342])
    assert not np.any(np.asarray(skirt)[:936])
    write('reports/complete_body_fix_preparation_checks.json', {
        'status': 'PASS_PREPARATION_ONLY', 'timestamp': now(),
        'frozen_source_unchanged': True, 'prior_stage_hashes_unchanged': BASELINES,
        'mask_mode_and_canvas_valid': True, 'mask_coverage': mask_metadata,
        'ai_calls_this_continuation': 0, 'no_004_or_005_output': True,
        'formal_part_png_count': 0, 'art_gate_passed': False,
        'note': 'Checks preparation integrity only, not repair quality or editor mask fidelity.'})
    print(json.dumps({'verdict': BLOCKED, 'masks': mask_metadata, 'ai_calls': 0}, ensure_ascii=False))


if __name__ == '__main__':
    main()
