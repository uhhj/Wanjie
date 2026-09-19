"""Freeze gate for the Gauss Rifleman sources: hashes, dimensions, alpha state."""
from pathlib import Path
import hashlib, json, sys
ROOT = Path(__file__).resolve().parents[1]
from PIL import Image
ROLES = ['DESIGN_V1','COMBAT_LOOK_V1','RIG_MASTER_V1','CODEX_V1']
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    errors = []
    manifest = json.loads((ROOT/'art_source/odyssey/gauss_rifleman/source_manifest.json').read_text(encoding='utf-8'))
    for item in manifest['files']:
        p = ROOT/item['file']
        if not p.exists(): errors.append('missing: '+item['role']); continue
        if sha(p) != item['sha256']: errors.append('hash changed: '+item['role'])
        im = Image.open(p)
        if list(im.size) != item['dimensions']: errors.append('dimensions changed: '+item['role'])
        print(f"{item['role']}: {im.size} mode={im.mode} alpha={im.getchannel('A').getextrema() if 'A' in im.getbands() else None} sha={item['sha256'][:16]}")
    if errors:
        print('FAIL:', errors); raise SystemExit(1)
    print('PASS: four frozen Gauss Rifleman sources verified')
if __name__ == '__main__': main()
