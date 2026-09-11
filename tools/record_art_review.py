"""Record an actual visual inspection. Hash binding invalidates stale approvals."""
import argparse
from rg_common import *
def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('key'); p.add_argument('--file',required=True); p.add_argument('--status',required=True,choices=['PASS','FAIL','REVIEWED_INTERMEDIATE_WITH_ISSUES']); p.add_argument('--reviewer',required=True); p.add_argument('--notes',required=True); a=p.parse_args()
    check_source()
    if len(a.notes.strip())<20: raise ValueError('Describe inspected invariants and any problems, not just approved')
    if a.key=='complete_body' and a.status=='PASS':
        # Every stage must be reviewed against its CURRENT output. Intermediate issues cannot disappear by omission.
        for s in config()['stages']:
            if not review_ok(s['id'],s['output']): raise ValueError('Resolve and PASS every stage before approving complete body')
    r=read('reports/art_reviews.json') if (ROOT/'reports/art_reviews.json').exists() else {}
    r[a.key]={'status':a.status,'file':a.file,'sha256':sha(a.file),'reviewer':a.reviewer,'notes':a.notes,'timestamp':now()}
    write('reports/art_reviews.json',r); print(a.key+': '+a.status)
if __name__=='__main__': main()

