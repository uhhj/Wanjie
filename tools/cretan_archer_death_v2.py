"""Reference-cued chest reaction, kneeling, forward fall and settled pose.

Uses the existing native art/bones. The bow's later release is keyed socket
motion, not rigid-body physics or a combat-system behavior.
"""
import math
import numpy as np
from cretan_archer_motion_math import neutral, rotation, smooth, fk, solve_arm, material_clouds, material_world


def author_death(data):
    bones = data['bones']
    pivots = {n: np.array(r['pivot'], float) for n, r in bones.items()}
    clouds = material_clouds(data)
    times = np.linspace(0, 1.55, 101).tolist()
    poses = []
    floor_records = []
    for t in times:
        pose = neutral(data)
        k = float(smooth((t-.14)/.42))
        fall = float(smooth((t-.73)/.55))
        hurt = float(smooth(t/.11)*(1-smooth((t-.22)/.22)))
        settle = float(smooth((t-1.28)/.2))
        roll = 82*fall-2*settle
        pose['visual_rotation'] = roll
        pose['pelvis_offset'] = [-25*k+35*fall, 350*k-40*fall]
        pose['rotations'].update(torso=-6*hurt+18*k-4*fall,
                                  head=-8*hurt+12*k-6*fall,
                                  cape_root=-3*k+4*fall, quiver_socket=2*k-3*fall)
        # Knees first move forward and down; shins fold back. The body only
        # starts its major forward rotation after this distinct kneeling hold.
        for side in ['near', 'far']:
            # One leg gives way first; the other retains a flat supporting
            # sole until the first knee is down. Simultaneous toe pivots read
            # as a hop even when one mathematical extreme touches the floor.
            leg_k = float(smooth((t-(.14 if side == 'near' else .26))/.36))
            thigh = 'leg_'+side+'_thigh'
            shin = 'leg_'+side+'_shin'
            foot = 'foot_'+side
            va = pivots['knee_'+side]-pivots[thigh]
            vb = pivots[foot]-pivots['knee_'+side]
            a0, b0 = [math.degrees(math.atan2(v[1], v[0])) for v in [va, vb]]
            kneel_a = 53 if side == 'near' else 54
            final_a = 155 if side == 'near' else 175
            final_b = 190 if side == 'near' else 180
            thigh_world = a0*(1-leg_k)+(kneel_a*(1-fall)+final_a*fall)*leg_k
            calf_world = b0*(1-leg_k)+(180*(1-fall)+final_b*fall)*leg_k
            pose['rotations'][thigh] = thigh_world-a0-roll
            pose['rotations'][shin] = calf_world-b0-(thigh_world-a0)
            # Toes fold behind/up during kneeling, so the soles cannot prop
            # the knees and torso in mid-air during the forward collapse.
            foot_pitch = 180*leg_k if side == 'near' else 180*float(smooth((leg_k-.8)/.2))
            pose['rotations'][foot] = foot_pitch-(calf_world-b0)
        # The initial drawing hand closes on the chest before reaching down.
        transforms = fk(data, pose)
        torso_r, torso_p = transforms['torso']
        chest = torso_p + torso_r @ (np.array([560., 565.])-pivots['torso'])
        near_upper = 'arm_near_upper'
        near_fore = 'arm_near_fore'
        near_hand = 'hand_near'
        reach = float(smooth(t/.16)*(1-smooth((t-.43)/.22)))
        default_grip = transforms[near_hand][1] + transforms[near_hand][0] @ np.array([19.,70.])
        desired = default_grip*(1-reach)+chest*reach
        hand_angle = -85*reach
        target = desired-rotation(hand_angle)@np.array([19.,70.])
        va = pivots[near_fore]-pivots[near_upper]
        vb = pivots[near_hand]-pivots[near_fore]
        th, sh = solve_arm(transforms[near_upper][1], target, np.linalg.norm(va), np.linalg.norm(vb),
                           math.atan2(va[1],va[0]), math.atan2(vb[1],vb[0]), -1)
        torso_angle = pose['rotations']['torso']
        pose['rotations'][near_upper] = th-torso_angle
        pose['rotations'][near_fore] = sh
        pose['rotations'][near_hand] = hand_angle-th-sh
        brace = float(smooth((t-.53)/.25))
        for side in ['near', 'far']:
            upper, fore, hand = 'arm_'+side+'_upper', 'arm_'+side+'_fore', 'hand_'+side
            va, vb = pivots[fore]-pivots[upper], pivots[hand]-pivots[fore]
            a0, b0 = [math.degrees(math.atan2(v[1],v[0])) for v in [va,vb]]
            ua = (52*(1-fall)+55*fall) if side == 'near' else (62*(1-fall)+0*fall)
            fa = (65*(1-fall)+10*fall) if side == 'near' else (70*(1-fall)+0*fall)
            values = {upper: ua-a0-roll-torso_angle, fore: fa-b0-(ua-a0), hand: (-35-55*fall)-(fa-b0)}
            for name, value in values.items():
                pose['rotations'][name] = (1-brace)*pose['rotations'][name]+brace*value
        # Keep the held bow from being driven vertically through the floor.
        tr = fk(data, pose)
        hand_r = tr['hand_far'][0]
        hand_angle_world = math.degrees(math.atan2(hand_r[1,0],hand_r[0,0]))+roll
        desired_bow_angle = 58*k*(1-fall)+90*fall
        pose['rotations']['bow_socket'] = desired_bow_angle-hand_angle_world
        # Floor is established by real deformed body pixels, excluding the
        # bow after release. This corrects height; it does not erase any pixels.
        world = material_world(data, pose, clouds)
        maximum = max(float(v[:,1].max()) for n,v in world.items() if n != 'bow')
        pose['visual_offset'][1] = -maximum
        released = float(smooth((t-.86)/.26))
        if released:
            tr = fk(data, pose)
            bow_r,bow_p = tr['bow_socket']
            visual_r = rotation(roll)
            current = visual_r@(bow_p-np.array(data['origin']))+pose['visual_offset']
            bow_points = clouds['bow'][0]-pivots['bow_socket']
            # Finish as a horizontal bow lying in front of the collapsed body.
            desired_rotation = desired_bow_angle*(1-released)+90*released
            desired_point = np.array([530., -(bow_points@rotation(desired_rotation).T)[:,1].max()])
            target_point = current*(1-released)+desired_point*released
            skeleton_target = visual_r.T@(target_point-pose['visual_offset'])+data['origin']
            parent_r,parent_p = tr['hand_far']
            pose['bow_offset'] = (parent_r.T@(skeleton_target-parent_p)-np.array(bones['bow_socket']['local_position'])).tolist()
            pose['rotations']['bow_socket'] = desired_rotation-hand_angle_world
        poses.append(pose)
        floor_records.append({'time':t, 'body_floor_world_y':0., 'kneel_progress':k, 'forward_fall_progress':fall, 'bow_released_progress':released})
    poses[0] = neutral(data)
    return {'length':1.55, 'loop':False, 'times':times, 'poses':poses,
            'reference_sequence':['chest_reaction','loss_of_balance','kneel','kneeling_hold','hands_reach_floor','forward_fall','settle'],
            'kneeling_hold_seconds':[.56,.73], 'bow_release_seconds': [.86,1.12],
            'floor_authoring_samples': floor_records,
            'floor_authoring_method':'Same native triangle/weight deformation at opaque source material; real GPU review still required'}
