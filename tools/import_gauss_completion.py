"""Import a manually produced image-edit result back into the pipeline.

Verifies dimensions, restricts changes to the mask, updates the job record.
Usage: import_gauss_completion.py import-result 001_remove_rifle --result work/gauss_rifleman/raw/001_remove_rifle.png
"""
from pathlib import Path
import argparse, hashlib, json, sys
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('command'); ap.add_argument('job')
    ap.add_argument('--result', required=True)
    args = ap.parse_args()
    assert args.command == 'import-result'
    rec_p = ROOT/'reports/gauss_rifleman/ai_jobs'/f'{args.job}.json'
    rec = json.loads(rec_p.read_text(encoding='utf-8'))
    res = Image.open(ROOT/args.result)
    master = Image.open(ROOT/rec['input_file']).convert('RGBA')
    errors = []
    if res.size != master.size: errors.append(f"result size {res.size} != master {master.size}")
    if res.mode not in ('RGBA','RGB'): errors.append(f'unexpected mode {res.mode}')
    if not errors:
        mask = Image.open(ROOT/rec['mask']).convert('L')
        if res.mode == 'RGB':
            errors.append('result is RGB without alpha: 需要先抠出透明底（或提供 matte），拒绝直接合成')
        else:
            out = master.copy(); res_a = res.convert('RGBA')
            comp = Image.alpha_composite(master, res_a)
            out = Image.composite(comp, master, mask)
            # 掩码外零改动校验
            m = mask.load(); o = out.load(); mm = master.load()
            outside_changed = 0
            for y in range(0, master.size[1], 2):
                for x in range(0, master.size[0], 2):
                    if m[x,y] < 8 and o[x,y] != mm[x,y]: outside_changed += 1
            if outside_changed: errors.append(f'mask 外发现 {outside_changed} 个抽样像素被改动')
            else:
                dest = ROOT/'work/gauss_rifleman'/f'{args.job.split("_")[0]}_no_rifle.png'
                out.save(dest)
                rec['status']='IMPORTED_PENDING_ART_REVIEW'; rec['output_file']=dest.relative_to(ROOT).as_posix()
                rec['output_sha256']=sha(dest); rec['timestamp']=__import__('datetime').datetime.utcnow().isoformat()
                dest.with_name(dest.stem+'_import_check.png').save.__self__  # noop keep linters calm
    rec['import_errors']=errors
    rec_p.write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n', encoding='utf-8')
    print(json.dumps({'status':rec['status'],'errors':errors},ensure_ascii=False))
    if errors: raise SystemExit(1)
if __name__=='__main__': main()
