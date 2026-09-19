"""Debug the skill_v3 far-arm overreach around t=0.44-0.47."""
import sys, math, importlib.util
import numpy as np

sys.path.insert(0, 'tools')
import build_minotaur_animation_candidates as m

orig_solve = m.solve
records = []

def traced_solve(p, upper, lower, tip, target, orientation, branch, context):
    if upper == 'arm_far_upper' and 'skill_v3' in str(context):
        origin, _ = m.fk(p, upper)
        d = float(np.linalg.norm(np.array(target) - origin))
        if d > 300:
            records.append((context, tuple(np.round(origin,1)), tuple(np.round(np.array(target,float),1)), round(d,1)))
    return orig_solve(p, upper, lower, tip, target, orientation, branch, context)

m.solve = traced_solve
import minotaur_skill_v3
skill = minotaur_skill_v3.build_skill(m)
for r in records:
    print(r)
print('total far-arm long-reach samples:', len(records))
u = np.array(B) if False else None
# chain lengths
B = m.B
l1 = np.linalg.norm(np.array(B['arm_far_fore']['pivot']) - B['arm_far_upper']['pivot'])
l2 = np.linalg.norm(np.array(B['hand_far']['pivot']) - B['arm_far_fore']['pivot'])
print('far chain:', round(float(l1+l2), 1))
