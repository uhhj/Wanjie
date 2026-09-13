"""Check actual staged blob bytes against the frozen/native SHA evidence.

This catches Git line-ending conversion without editing a frozen working file.
Run after staging the delivery. The output itself is not a hash input.
"""
import hashlib
import io
import json
import subprocess
import cretan_archer_pipeline as p


def main():
    expected = dict(p.load(p.REPORT+'roman_guard_freeze_baseline.json')['files'])
    prefix = p.REPORT+'native/'
    for name in ['headless_tests.json','capture_manifest.json','smoke_20_walk.json','rig_lab_startup.json']:
        report = p.load(prefix+name)
        expected.update({f.replace('res://',''):h for f,h in report['artifact_inputs'].items()})
    capture = p.load(prefix+'capture_manifest.json')
    expected.update({r['path'].replace('res://',''):r['sha256'] for r in capture['frames']})
    visual = p.load(prefix+'visual_gate.json')
    expected.update(visual['reviewed_files'])
    expected[p.WORK+'04_complete_body_rgba.png'] = p.sha(p.WORK+'04_complete_body_rgba.png')
    manifest = p.load('tools/cretan_archer_parts_manifest.json')
    expected[manifest['approved_review']] = p.sha(manifest['approved_review'])
    requests = ''.join(':'+f+'\n' for f in expected).encode()
    result = subprocess.run(['git','cat-file','--batch'], input=requests, capture_output=True, cwd=p.ROOT, check=True)
    stream = io.BytesIO(result.stdout)
    failures = []
    for path, digest in expected.items():
        header = stream.readline().decode().strip().split()
        if len(header)!=3 or header[1]!='blob':
            failures.append({'file':path,'reason':'not staged as a blob'})
            continue
        content = stream.read(int(header[2])); stream.read(1)
        got = hashlib.sha256(content).hexdigest()
        if got!=digest:
            failures.append({'file':path,'expected_sha256':digest,'staged_sha256':got})
    report = {'status':'PASS' if not failures else 'FAIL', 'checked_staged_blobs':len(expected),
              'method':'git cat-file --batch, raw staged bytes SHA256; no filesystem rewrites',
              'frozen_roman_files':49, 'failures':failures, 'timestamp':p.now()}
    p.save(prefix+'git_snapshot_gate.json',report)
    print(json.dumps(report))
    return 0 if not failures else 2


if __name__=='__main__':
    raise SystemExit(main())
