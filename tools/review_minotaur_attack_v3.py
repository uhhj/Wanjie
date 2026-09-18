"""Presentation only: GIFs and contact sheets from unchanged native GPU captures."""
from pathlib import Path
import json
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/minotaur_breaker/attack_v3'
data = json.loads((ROOT / 'resources/minotaur_breaker_animation_candidates.json').read_text())
for height in (360, 288):
    for name in ('attack_01',):
        files = sorted((OUT / 'frames').glob(f'{name}_{height}_*.png'))
        if len(files) != 32:
            continue
        frames = []
        for i, file in enumerate(files):
            source = Image.open(file).convert('RGB')
            t = data[name]['length'] * i / 31
            distance = max(0, min(2880, (t - .60) * 1000)) if name == 'skill_01' else 0
            center = 260 + distance * height / 1435
            left = round(center - 240)
            frame = source.crop((left, 0, left + 620, 540))
            ImageDraw.Draw(frame).text((10, 10), f'{name} | {height}px | {i+1}/32 | {t:.2f}s | camera follows world motion', fill='black')
            frames.append(frame)
        frames[0].save(OUT / f'{name}_{height}.gif', save_all=True, append_images=frames[1:], duration=round(data[name]['length']*1000/32), loop=0)
        # Native-size crops, no rescaling of the character.
        for page in range(4):
            sheet = Image.new('RGB', (620*4, 540*2), '#dbdddf')
            for k in range(8):
                sheet.paste(frames[page*8+k], ((k%4)*620, (k//4)*540))
            sheet.save(OUT / f'{name}_{height}_review_{page+1}.png')
        wide = [Image.open(f).convert('RGB') for f in files]
        wide[0].save(OUT / f'{name}_{height}_world.gif', save_all=True, append_images=wide[1:], duration=round(data[name]['length']*1000/32), loop=0)
print('Native 32-frame GIFs and 8-pose review pages created.')
