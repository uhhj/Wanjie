"""Run production gates with truthful NOT_RUN states. Optional isolated tool tests."""
import argparse,subprocess,sys,json
from rg_common import *
def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--test-tools',action='store_true'); a=p.parse_args(); runs=[]
    scripts=['validate_source_asset.py','validate_parts.py','recompose_roman_guard.py','generate_joint_rotation_test.py','check_godot_handoff.py']
    if a.test_tools: scripts.insert(0,'test_pipeline_safety.py')
    for script in scripts:
        run=subprocess.run([sys.executable,str(ROOT/'tools'/script)],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',env={**__import__('os').environ,'PYTHONIOENCODING':'utf-8'})
        runs.append({'script':script,'exit_code':run.returncode,'stdout':run.stdout,'stderr':run.stderr})
        print(script+': '+('PASS' if run.returncode==0 else 'BLOCKED/FAIL' if run.returncode==2 else 'ERROR'))
    ready=all(r['exit_code']==0 for r in runs)
    write('reports/validation_run.json',{'status':'PASS' if ready else 'BLOCKED','runtime':sys.executable,'runs':runs,'timestamp':now()})
    return 0 if ready else 2
if __name__=='__main__': raise SystemExit(main())
