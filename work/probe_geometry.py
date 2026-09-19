"""Geometry probe: charge axe placement, attack blade floor clearance, rest bone data."""
import json, math
import numpy as np

DATA = json.load(open('resources/minotaur_breaker_rig_v1.json', encoding='utf-8'))
B = DATA['bones']
ORIGIN = np.array(DATA['origin'], float)

def rot(v, a):
    c, s = math.cos(a), math.sin(a)
    return np.array([c*v[0]-s*v[1], s*v[0]+c*v[1]])

def fk(p, name):
    b = B[name]; parent = b['parent']
    pos, ang = fk(p, parent) if parent else (np.zeros(2), 0.)
    local = np.array(b['local_position'], float)
    local = local + np.array(p.get('bone_offsets', {}).get(name, [0., 0.]))
    if name == 'pelvis':
        local = local + np.array(p['pelvis_offset'])
    return pos + rot(local, ang), ang + math.radians(p['rotations'][name])

anim = json.load(open('resources/minotaur_breaker_animation_candidates.json', encoding='utf-8'))
GROUND = 1485.0

print('=== charge skill_01 (V2) axe geometry mid-charge ===')
s = anim['skill_01']
for idx in (85, 105, 125, 145, 165, 185, 205, 225):
    t = s['times'][idx]; p = s['poses'][idx]
    sock_pos, sock_ang = fk(p, 'axe_socket')
    world = sock_pos
    blade = world + rot([19, -220], sock_ang)
    butt = world + rot([-49, 460], sock_ang)
    print(f't={t:.2f}s socket=({world[0]:.0f},{world[1]:.0f}) ang={math.degrees(sock_ang):.0f} blade=({blade[0]:.0f},{blade[1]:.0f}) butt=({butt[0]:.0f},{butt[1]:.0f})')

print()
print('=== attack_01 (V3) blade floor clearance ===')
a = anim['attack_01']
lowest = None
for i, (t, p) in enumerate(zip(a['times'], a['poses'])):
    sock_pos, sock_ang = fk(p, 'axe_socket')
    world = sock_pos
    blade = world + rot([19, -220], sock_ang)
    if lowest is None or blade[1] < lowest[1]:
        lowest = (t, blade[1], sock_pos)
t, blade_y, sock = lowest
print(f'lowest blade tip: t={t:.2f}s y={blade_y:.0f}, ground={GROUND:.0f}, clearance={GROUND-blade[1]:.0f} source px')
for i, (t, p) in enumerate(zip(a['times'], a['poses'])):
    if abs(t-0.98) < 0.006 or abs(t-1.12) < 0.006 or abs(t-1.26) < 0.006:
        sock_pos, sock_ang = fk(p, 'axe_socket'); world = sock_pos
        blade = world + rot([19, -220], sock_ang)
        print(f't={t:.2f}s socket=({world[0]:.0f},{world[1]:.0f}) blade=({blade[0]:.0f},{blade[1]:.0f}) clearance={GROUND-blade[1]:.0f}px')

print()
print('=== torso/pelvis rest geometry ===')
for n in ['axe_socket', 'axe_support_socket', 'hand_far', 'hand_near', 'pelvis', 'torso', 'head', 'arm_far_upper', 'arm_near_upper']:
    b = B[n]
    print(f"{n}: pivot={b.get('pivot')} local={b['local_position']} parent={b['parent']}")
print('origin:', DATA['origin'])
print('axe_grips:', DATA['axe_grips'])
