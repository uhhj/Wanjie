"""Source-space native FK and conservative material hull for authoring only."""
import math
import numpy as np
from PIL import Image
import cretan_archer_pipeline as p


def rotation(degrees):
    a = math.radians(degrees)
    return np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])


def smooth(v):
    v = np.clip(v, 0., 1.)
    return v * v * (3 - 2 * v)


def neutral(data):
    return {'rotations': {n: 0. for n in data['bones']}, 'pelvis_offset': [0, 0],
            'hip_offsets': {'near': [0, 0], 'far': [0, 0]},
            'shoulder_offsets': {'near': [0, 0], 'far': [0, 0]},
            'visual_rotation': 0., 'visual_offset': [0, 0], 'bow_offset': [0, 0],
            'bow_draw_point': [-91.45, 0], 'arrow_visible': False, 'arrow_rotation': 0.}


def fk(data, pose):
    transforms = {}
    for name, record in data['bones'].items():
        off = np.array(record['local_position'], float)
        if name == 'pelvis':
            off += pose['pelvis_offset']
        for side in ['near', 'far']:
            if name == 'leg_' + side + '_thigh':
                off += pose['hip_offsets'][side]
            if name == 'arm_' + side + '_upper':
                off += pose['shoulder_offsets'][side]
        if name == 'bow_socket':
            off += pose.get('bow_offset', [0, 0])
        if name == 'arrow_socket':
            off = np.array(pose['bow_draw_point'], float)
        rr, pp = transforms[record['parent']] if record['parent'] else (np.eye(2), np.zeros(2))
        angle = pose['arrow_rotation'] if name == 'arrow_socket' else pose['rotations'][name]
        transforms[name] = (rr @ rotation(angle), pp + rr @ off)
    return transforms


def solve_arm(shoulder, target, l0, l1, rest0, rest1, sign):
    d = np.array(target) - np.array(shoulder)
    co = np.clip((d @ d - l0*l0 - l1*l1) / (2*l0*l1), -1, 1)
    bend = sign * math.acos(co)
    a = math.atan2(d[1], d[0]) - math.atan2(l1*math.sin(bend), l0+l1*math.cos(bend))
    first = math.degrees(a-rest0)
    return first, math.degrees(a+bend-rest1)-first


def material_clouds(data):
    """Evaluate the same triangles/weights as Godot at opaque material pixels."""
    spec = {r['part']: r for r in p.load('resources/cretan_archer_local_skinning.json')['meshes']}
    clouds = {}
    for name in data['draw_order']:
        if name in ['arrow_single', 'bow_string']:
            continue
        alpha = np.asarray(Image.open(p.ROOT / 'assets/units/odyssey/cretan_archer/parts' / (name+'.png')))[:, :, 3]
        yy, xx = np.where(alpha > 128)
        points = np.column_stack([xx, yy]).astype(float)
        weights = {}
        if name in spec:
            rec = spec[name]
            step = rec['grid_step']
            cells = np.floor(points / step) * step
            uv = (points-cells)/step
            for prefix in ['stationary', 'moving', 'additional']:
                if prefix+'_weights' not in rec:
                    continue
                lookup = {tuple(v): w for v, w in zip(rec['vertices'], rec[prefix+'_weights'])}
                values = []
                for (x, y), (u, v) in zip(cells, uv):
                    w00 = lookup.get((x, y), 0)
                    w10 = lookup.get((x+step, y), w00)
                    w11 = lookup.get((x+step, y+step), w00)
                    w01 = lookup.get((x, y+step), w00)
                    values.append(w00*(1-u)+w10*(u-v)+w11*v if u>=v else w00*(1-v)+w11*u+w01*(v-u))
                weights[rec[prefix+'_bone']] = np.asarray(values)[:, None]
        else:
            weights[data['attachments'][name]] = np.ones((len(points), 1))
        clouds[name] = (points, weights)
    return clouds


def material_world(data, pose, clouds):
    transforms = fk(data, pose)
    origin = np.array(data['origin'])
    global_r = rotation(pose['visual_rotation'])
    result = {}
    for name, (points, bindings) in clouds.items():
        world = np.zeros_like(points)
        for bone, weights in bindings.items():
            rr, pp = transforms[bone]
            pivot = np.array(data['bones'][bone]['pivot'])
            world += ((points-pivot)@rr.T + pp)*weights
        result[name] = (world-origin)@global_r.T + pose['visual_offset']
    return result
