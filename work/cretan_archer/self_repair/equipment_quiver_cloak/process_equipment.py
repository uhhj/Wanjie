"""Recompose real generated hidden equipment patches, retaining owned Master pixels.

No model call in this script. The two actual image_gen calls and raw RGB results
are recorded in reports/cretan_archer/self_repair/quiver_cloak/ai_jobs.json.
"""
from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
REPORT = ROOT / 'reports/cretan_archer/self_repair/quiver_cloak'
MASTER = ROOT / 'art_source/odyssey/cretan_archer/OD_UNIT_02_CRETAN_ARCHER_RIG_MASTER_V1.png'
BODY = ROOT / 'work/cretan_archer/04_complete_body_rgba.png'
BODY_SHA = 'f8451c19b04a8d754fb2ebfeb4441324990a5b5d9de6dcc6ccec518550536bc8'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run():
    assert sha(BODY) == BODY_SHA, 'Approved Body changed; do not continue.'
    master = np.array(Image.open(MASTER).convert('RGBA'))
    metrics = {}
    for name, size, origin in [('quiver', (274, 612), (216, 168)), ('cloak', (420, 325), (270, 275))]:
        raw = Image.open(HERE / f'{name}_generated_raw.png')
        ar = np.array(raw.convert('RGB')).astype(np.int16)
        # The real tool outputs are RGB with a painted checkerboard. Remove only
        # its connected bright neutral background; no source foreground is keyed.
        candidate = ((ar.max(2) - ar.min(2)) <= 24) & (ar.min(2) >= 145)
        flood = Image.fromarray(np.where(candidate, 255, 0).astype('uint8')).copy()
        ImageDraw.floodfill(flood, (0, 0), 128)
        alpha = np.where(np.array(flood) == 128, 0, 255).astype('uint8')
        rgba = Image.fromarray(np.dstack((ar.astype('uint8'), alpha)), 'RGBA')
        rgba.save(HERE / f'{name}_generated_alpha.png')
        aligned = Image.new('RGBA', (1024, 1536))
        aligned.paste(rgba.resize(size, Image.Resampling.LANCZOS), origin)
        aligned.save(HERE / f'{name}_generated_aligned.png')
        gen = np.array(aligned)
        mask = np.array(Image.open(HERE / f'{name}_completion_only_mask.png')) > 0
        gen[:, :, 3] = np.where(mask, gen[:, :, 3], 0)
        known = np.array(Image.open(HERE / f'{name}_source_visible_ownership_mask.png')) > 0
        if name == 'cloak':
            # The tool moved its upper cloth contour. Transfer its adjacent cloth
            # texture only to the traced strip hidden behind the original quiver.
            # The actual original cloth ownership always takes priority below.
            patch = (np.array(Image.open(HERE / 'cloak_generated_border_alignment_mask.png')) > 0) & ~known
            full_ai = np.array(aligned)
            for y, x in np.argwhere(patch):
                sx = min(448, max(411, int(x) + 14))
                sy = min(368, max(330, int(y) + 24))
                if full_ai[sy, sx, 3] > 250:
                    gen[y, x] = full_ai[sy, sx]
        gen[known] = master[known]
        result = Image.fromarray(gen, 'RGBA')
        path = HERE / f'{name}_completed_same_canvas.png'
        result.save(path)
        delta = np.any(gen != master, axis=2) & known
        assert not delta.any(), 'A source-owned visible pixel changed.'
        metrics[name] = {
            'output': str(path), 'sha256': sha(path), 'mode': result.mode,
            'canvas': list(result.size), 'alpha_extrema': list(result.getchannel('A').getextrema()),
            'foreground_bbox': list(result.getbbox()),
            'source_visible_pixel_count': int(known.sum()),
            'source_visible_rgba_changed_count': int(delta.sum()),
            'ai_completed_pixel_count': int(((gen[:, :, 3] > 0) & ~known).sum()),
            'fractional_alpha_count': int(((gen[:, :, 3] > 0) & (gen[:, :, 3] < 255)).sum()),
            'raw_tool_output_mode': raw.mode, 'raw_tool_output_dimensions': list(raw.size),
            'native_mask_parameter_used': False,
            'review_status': 'REQUIRES_COMPOSITE_REVIEW',
        }
    (REPORT / 'equipment_completion_metrics.json').write_text(json.dumps(metrics, indent=2), encoding='utf-8')
    print(json.dumps(metrics, indent=2))

if __name__ == '__main__':
    run()
