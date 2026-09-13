"""Author a light Archer walk from motion cues using the approved native rig.

This module only returns animation/contact data. It never writes files, edits
parts, copies reference-image pixels, or changes the shared skeleton. The caller
owns serialization and actual Godot validation.
"""
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PARTS = ROOT / "assets/units/odyssey/cretan_archer/parts"
STRIDE = 420.0
CYCLE_SECONDS = 1.05
SUPPORT = 0.55
KEY_COUNT = 96
PHASE_CUES = [
    ("contact_near", 0.0),
    ("down_near", 0.12),
    ("passing_near", 0.275),
    ("up_near", 0.40),
    ("contact_far", 0.5),
    ("down_far", 0.62),
    ("passing_far", 0.775),
    ("up_far", 0.90),
]


def _rotation(degrees):
    angle = math.radians(degrees)
    return np.array([[math.cos(angle), -math.sin(angle)],
                     [math.sin(angle), math.cos(angle)]])


def _smooth(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def _periodic_monotone_curve(times, values):
    """C1 Hermite curve with monotone segments and matching loop derivatives."""
    times, values = np.asarray(times, float), np.asarray(values, float)
    widths = np.diff(times)
    slopes = np.diff(values) / widths
    tangents = np.zeros(len(times))
    for i in range(1, len(times) - 1):
        if slopes[i - 1] * slopes[i] > 0.0:
            left_weight = 2.0 * widths[i] + widths[i - 1]
            right_weight = widths[i] + 2.0 * widths[i - 1]
            tangents[i] = (left_weight + right_weight) / (
                left_weight / slopes[i - 1] + right_weight / slopes[i])
    if slopes[-1] * slopes[0] > 0.0:
        left_weight = 2.0 * widths[0] + widths[-1]
        right_weight = widths[0] + 2.0 * widths[-1]
        tangents[0] = (left_weight + right_weight) / (
            left_weight / slopes[-1] + right_weight / slopes[0])
    tangents[-1] = tangents[0]

    def evaluate(phase):
        phase = max(float(times[0]), min(float(times[-1]), float(phase)))
        index = min(len(times) - 2, int(np.searchsorted(times, phase, side="right") - 1))
        index = max(0, index)
        width = widths[index]
        u = (phase - times[index]) / width
        return float((2 * u ** 3 - 3 * u ** 2 + 1) * values[index]
                     + (u ** 3 - 2 * u ** 2 + u) * width * tangents[index]
                     + (-2 * u ** 3 + 3 * u ** 2) * values[index + 1]
                     + (u ** 3 - u ** 2) * width * tangents[index + 1])

    return evaluate


def _solve_leg(hip, target, upper_length, lower_length, rest_upper, rest_lower):
    delta = target - hip
    distance = float(np.linalg.norm(delta))
    cosine = float(np.clip((distance ** 2 - upper_length ** 2 - lower_length ** 2)
                          / (2.0 * upper_length * lower_length), -1.0, 1.0))
    bend = math.acos(cosine)
    upper = math.atan2(delta[1], delta[0]) - math.atan2(
        lower_length * math.sin(bend), upper_length + lower_length * math.cos(bend))
    upper_degrees = math.degrees(upper - rest_upper)
    lower_degrees = math.degrees(upper + bend - rest_lower) - upper_degrees
    return upper_degrees, lower_degrees


def author_walk(data):
    """Return ``(walk_entry, contacts_dict)`` in the current Archer JSON schema.

    The near/far labels name the supporting half-cycle. The eight phase cues
    summarize contact/down/passing/up; they do not claim the supplied sheet is
    eight evenly timed, alternating frames of a mechanically complete walk.
    """
    bones = data["bones"]
    pivots = {name: np.asarray(record["pivot"], float) for name, record in bones.items()}
    origin = np.asarray(data["origin"], float)
    ground = float(origin[1])
    sole = {}
    input_hashes = {}
    for side in ["near", "far"]:
        source = PARTS / ("foot_" + side + ".png")
        input_hashes[side] = hashlib.sha256(source.read_bytes()).hexdigest()
        with Image.open(source) as image:
            if image.mode != "RGBA" or image.size != tuple(data["source_canvas"]):
                raise ValueError("Walk requires the approved same-canvas RGBA shoe: " + str(source))
            alpha = np.asarray(image)[:, :, 3]
        points = []
        for x in np.where(np.any(alpha > 128, axis=0))[0]:
            ys = np.where(alpha[:, x] > 128)[0]
            points.append([float(x), float(ys.max())])
        if not points:
            raise ValueError("Cannot derive material contact from an empty shoe")
        sole[side] = np.asarray(points) - pivots["foot_" + side]

    def pitch(phase):
        # Heel arrival, flat load, then a modest toe-off. The shin/knee curves
        # begin recovery before the foot curls, avoiding an isolated ankle flip.
        if phase < 0.13:
            return -8.0 * (1.0 - _smooth(phase / 0.13))
        return 18.0 * _smooth((phase - 0.35) / 0.20)

    support_samples = np.linspace(0.0, SUPPORT, 2641)
    roll = {}
    for side in sole:
        correction = np.zeros(len(support_samples))
        for i in range(1, len(support_samples)):
            before, after = support_samples[i - 1], support_samples[i]
            middle_rotation = _rotation(pitch((before + after) * 0.5))
            contact = sole[side][np.argmax((sole[side] @ middle_rotation.T)[:, 1])]
            correction[i] = correction[i - 1] + (
                (_rotation(pitch(before)) - _rotation(pitch(after))) @ contact)[0]
        correction -= np.interp(SUPPORT * 0.5, support_samples, correction)
        roll[side] = correction

    def stance(side, phase):
        angle = pitch(phase)
        turned = sole[side] @ _rotation(angle).T
        contact = sole[side][np.argmax(turned[:, 1])]
        ankle = np.array([
            518.0 + STRIDE * SUPPORT * 0.5 - STRIDE * phase
            + np.interp(phase, support_samples, roll[side]),
            ground - float(turned[:, 1].max()),
        ])
        return ankle, angle, contact

    def foot_target(side, phase):
        if phase < SUPPORT:
            return stance(side, phase)
        q = (phase - SUPPORT) / (1.0 - SUPPORT)
        progress = _smooth(q)
        start, _, _ = stance(side, SUPPORT)
        end, _, _ = stance(side, 0.0)
        # Preserve matched root-speed tangents at both contact exchanges.
        x = (start[0] * (1.0 - progress) + end[0] * progress
             - STRIDE * (1.0 - SUPPORT) * (2.0 * q ** 3 - 3.0 * q ** 2 + q))
        # Squared-sine clearance has zero endpoint vertical velocity, unlike
        # the former sine arc. The rear foot clears during passing without pop.
        y = start[1] * (1.0 - progress) + end[1] * progress - 62.0 * math.sin(math.pi * q) ** 2
        return np.array([x, y]), 18.0 - 26.0 * _smooth((q - 0.10) / 0.90), None

    knee_flex = _periodic_monotone_curve(
        [0.0, 0.12, 0.30, 0.45, 0.55, 0.66, 0.80, 1.0],
        [12.0, 17.0, 10.0, 18.0, 26.0, 40.0, 30.0, 12.0])
    entry = {
        "length": CYCLE_SECONDS, "loop": True,
        "times": [CYCLE_SECONDS * i / KEY_COUNT for i in range(KEY_COUNT + 1)],
        "poses": [], "root_motion_source_px_per_cycle": STRIDE,
        "support_intervals": {"near": [[0.0, SUPPORT]], "far": [[0.0, 0.05], [0.5, 1.0]]},
        "key_phases": [name for name, _ in PHASE_CUES],
        "key_phase_times": {name: phase * CYCLE_SECONDS for name, phase in PHASE_CUES},
    }
    records = []
    for i in range(KEY_COUNT + 1):
        phase = i / KEY_COUNT
        sine, cosine = math.sin(phase * 2.0 * math.pi), math.cos(phase * 2.0 * math.pi)
        bob = 4.5 * (1.0 - math.cos(4.0 * math.pi * (phase + 0.125)))
        counter = 1.05 * cosine - 0.10 * sine
        inertia = 0.25 * math.sin(phase * 4.0 * math.pi - 0.3)
        arm_swing = math.cos(phase * 2.0 * math.pi - 0.10)
        pose = {
            "rotations": {name: 0.0 for name in bones},
            "pelvis_offset": [2.0 * sine, bob],
            "hip_offsets": {"near": [0.0, 0.0], "far": [0.0, 0.0]},
            "shoulder_offsets": {"near": [0.0, 0.0], "far": [0.0, 0.0]},
            "visual_rotation": 0.0, "visual_offset": [0.0, 0.0],
            "bow_draw_point": [-91.45, 0.0], "arrow_visible": False,
            "arrow_rotation": 0.0,
        }
        pose["rotations"].update(
            torso=counter, head=-0.94 * counter,
            arm_near_upper=9.0 * arm_swing, arm_near_fore=-3.0 * arm_swing,
            hand_near=-2.0 * arm_swing, arm_far_upper=-counter,
            arm_far_fore=inertia, hand_far=-inertia,
            cape_root=1.0 * math.sin(phase * 2.0 * math.pi - 0.45),
            quiver_socket=0.35 * math.sin(phase * 2.0 * math.pi - 0.2))
        for side, offset in [("near", 0.0), ("far", 0.5)]:
            u = (phase + offset) % 1.0
            target, angle, contact = foot_target(side, u)
            hip = pivots["leg_" + side + "_thigh"]
            knee = pivots["knee_" + side]
            ankle = pivots["foot_" + side]
            upper_vector, lower_vector = knee - hip, ankle - knee
            upper_length, lower_length = np.linalg.norm(upper_vector), np.linalg.norm(lower_vector)
            bend = math.radians(knee_flex(u))
            reach_squared = (upper_length ** 2 + lower_length ** 2
                             + 2.0 * upper_length * lower_length * math.cos(bend))
            hip_x = hip[0] + 2.0 * sine
            height_squared = reach_squared - (target[0] - hip_x) ** 2
            if height_squared <= 0.0:
                raise ValueError("Unreachable Archer walk target: " + side)
            hip_y = target[1] - math.sqrt(height_squared)
            pose["hip_offsets"][side] = [0.0, float(hip_y - hip[1] - bob)]
            thigh, shin = _solve_leg(np.array([hip_x, hip_y]), target,
                                     upper_length, lower_length,
                                     math.atan2(upper_vector[1], upper_vector[0]),
                                     math.atan2(lower_vector[1], lower_vector[0]))
            pose["rotations"]["leg_" + side + "_thigh"] = thigh
            pose["rotations"]["leg_" + side + "_shin"] = shin
            pose["rotations"]["foot_" + side] = float(angle - thigh - shin)
            records.append({
                "phase": phase, "time": phase * CYCLE_SECONDS, "side": side,
                "support": u < SUPPORT, "contact_local": None if contact is None else contact.tolist(),
                "target_ankle": target.tolist(), "pitch": float(angle), "foot_world_pitch": float(angle),
                "support_id": f"{side}_{math.floor(phase + offset)}",
                "contact_id": None if contact is None else ",".join(str(int(v)) for v in contact),
                "expected_world_contact": None if contact is None else (
                    target + _rotation(angle) @ contact + np.array([STRIDE * phase, 0.0]) - origin).tolist(),
            })
        entry["poses"].append(pose)
    entry["poses"][-1] = json.loads(json.dumps(entry["poses"][0]))
    contacts = {
        "stride": STRIDE, "cycle_seconds": CYCLE_SECONDS, "ground_y": ground,
        "support_fraction": SUPPORT, "sole_profiles": {side: points.tolist() for side, points in sole.items()},
        "records": records, "source_shoe_sha256": input_hashes,
        "motion_reference_policy": "Motion cues only; no source pixels or literal frame timing copied",
        "phase_cues": [{"name": name, "phase": phase, "time": phase * CYCLE_SECONDS} for name, phase in PHASE_CUES],
        "authoring_changes": [
            "Toe-off world pitch18deg; heel contact remains-8deg",
            "Swing clearance62sourcepx with zero endpoint vertical velocity",
            "Continuous monotone knee flexion;40deg early-swing peak",
            "9deg near-arm swing with slight lag; bow/head counter-stabilized",
        ],
    }
    return entry, contacts
