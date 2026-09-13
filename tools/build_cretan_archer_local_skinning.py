"""Build Archer-only local native meshes without changing any texture pixel."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
RIG_FILE = ROOT / "resources/cretan_archer_rig_v1.json"
OUTPUT = ROOT / "resources/cretan_archer_local_skinning.json"
FORMAL = Path("assets/units/odyssey/cretan_archer/parts")
REPAIRED = Path("work/cretan_archer/self_repair/repaired_parts")
GRID_STEP = 8
SPECS = [
    ("arm_near_upper", "torso", "arm_near_upper", "source_y", 455, 505),
    ("arm_far_upper", "torso", "arm_far_upper", "source_y", 505, 595),
    ("arm_near_fore", "arm_near_upper", "arm_near_fore", "forearm_axis", -15, 40),
    ("arm_far_fore", "arm_far_upper", "arm_far_fore", "forearm_axis", -15, 40),
    ("leg_near_shin", "leg_near_thigh", "leg_near_shin", "source_y", 1090, 1160),
    ("leg_far_shin", "leg_far_thigh", "leg_far_shin", "source_y", 1100, 1170),
    ("foot_near", "leg_near_shin", "foot_near", "source_y", 1330, 1390),
    ("foot_far", "leg_far_shin", "foot_far", "source_y", 1330, 1378),
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path):
    return path.relative_to(ROOT).as_posix()


def mesh_grid(alpha):
    yy, xx = np.where(alpha > 0)
    if not len(xx):
        raise ValueError("Empty part cannot be natively bound")
    x0, y0 = int(xx.min() // GRID_STEP * GRID_STEP), int(yy.min() // GRID_STEP * GRID_STEP)
    x1 = min(alpha.shape[1], int(xx.max() // GRID_STEP * GRID_STEP + GRID_STEP))
    y1 = min(alpha.shape[0], int(yy.max() // GRID_STEP * GRID_STEP + GRID_STEP))
    vertices, triangles, lookup = [], [], {}
    for y in range(y0, y1, GRID_STEP):
        for x in range(x0, x1, GRID_STEP):
            right, bottom = min(x + GRID_STEP, alpha.shape[1]), min(y + GRID_STEP, alpha.shape[0])
            if not alpha[y:bottom + 1, x:right + 1].any():
                continue
            indices = []
            for point in [(x, y), (right, y), (right, bottom), (x, bottom)]:
                if point not in lookup:
                    lookup[point] = len(vertices)
                    vertices.append(point)
                indices.append(lookup[point])
            triangles.extend([[indices[0], indices[1], indices[2]], [indices[0], indices[2], indices[3]]])
    return np.asarray(vertices, dtype=float), triangles


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parts-dir", help="Repository-relative PNG folder; defaults to formal PASS assets, otherwise repaired candidates")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "tools/cretan_archer_parts_manifest.json").read_text(encoding="utf-8"))
    rig = json.loads(RIG_FILE.read_text(encoding="utf-8"))
    folder = (ROOT / (args.parts_dir or (FORMAL if manifest.get("status") == "PASS" else REPAIRED))).resolve()
    if not folder.is_relative_to(ROOT):
        raise ValueError("Part inputs must remain within the Wanjie repository")
    records, source_hashes = [], {}
    for part, stationary, moving, mode, start, end in SPECS:
        image_path = folder / (part + ".png")
        digest = sha(image_path)
        source_hashes[image_path] = digest
        image = Image.open(image_path)
        if image.format != "PNG" or image.mode != "RGBA" or image.size != (1024, 1536):
            raise ValueError("Expected same-canvas RGBA source: " + str(image_path))
        points, triangles = mesh_grid(np.asarray(image)[:, :, 3])
        pivot = np.asarray(rig["bones"][moving]["pivot"], dtype=float)
        axis = None
        if mode == "forearm_axis":
            side = "near" if "near" in part else "far"
            wrist = np.asarray(rig["bones"]["hand_" + side]["pivot"], dtype=float)
            axis = wrist - pivot
            if np.linalg.norm(axis) < 1:
                raise ValueError("Degenerate forearm axis")
            axis /= np.linalg.norm(axis)
            distance = (points - pivot) @ axis
        else:
            distance = points[:, 1]
        t = np.clip((distance - start) / (end - start), 0.0, 1.0)
        moving_weights = t * t * (3.0 - 2.0 * t)
        stationary_weights = 1.0 - moving_weights
        extra = {}
        additional_weights = np.zeros_like(moving_weights)
        if part == "arm_near_upper":
            # Keep the approved torso/upper shoulder blend, while the lower bare
            # arm follows the forearm at the bracer seam during cheek-height draw.
            # This changes bone influence only: the texture and UV remain exact.
            fore_t = np.clip((points[:, 1] - 575.0) / 75.0, 0.0, 1.0)
            fore_mix = fore_t * fore_t * (3.0 - 2.0 * fore_t)
            additional_weights = moving_weights * fore_mix
            moving_weights = moving_weights * (1.0 - fore_mix)
            extra = {
                "additional_bone": "arm_near_fore",
                "additional_pivot": rig["bones"]["arm_near_fore"]["pivot"],
                "additional_weights": additional_weights.tolist(),
                "additional_weight_coordinate": "source_y",
                "additional_weight_transition": [575, 650],
            }
        assert np.allclose(moving_weights + stationary_weights + additional_weights, 1.0)
        assert np.isfinite(points).all() and np.isfinite(moving_weights).all()
        records.append({
            "part": part, "source_file": relative(image_path),
            "texture_file": (FORMAL / (part + ".png")).as_posix(),
            "texture_sha256": digest, "canvas": list(image.size), "grid_step": GRID_STEP,
            "stationary_bone": stationary, "moving_bone": moving,
            "stationary_pivot": rig["bones"][stationary]["pivot"],
            "moving_pivot": rig["bones"][moving]["pivot"],
            "weight_coordinate": mode, "weight_transition": [start, end],
            "forearm_axis": None if axis is None else axis.tolist(),
            "vertices": points.astype(int).tolist(), "uv": points.astype(int).tolist(),
            "triangles": triangles, "stationary_weights": stationary_weights.tolist(),
            "moving_weights": moving_weights.tolist(),
            "rgb_changed_pixels": 0, "alpha_changed_pixels": 0,
            **extra,
        })
    assert all(sha(path) == digest for path, digest in source_hashes.items())
    payload = {"unit_id": "OD_UNIT_02_CRETAN_ARCHER", "rig_id": "HUMAN_MEDIUM_RIG_V1",
               "status": "NATIVE_BINDINGS_PREPARED_MOTION_REVIEW_REQUIRED",
               "rig_file": relative(RIG_FILE), "rig_sha256": sha(RIG_FILE),
               "source_stage": "FORMAL" if folder == (ROOT / FORMAL).resolve() else "REPAIRED_CANDIDATE",
               "grid_step": GRID_STEP, "texture_changes": 0, "meshes": records}
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"mesh_count": len(records), "grid_step": GRID_STEP,
                      "vertices": sum(len(r["vertices"]) for r in records),
                      "triangles": sum(len(r["triangles"]) for r in records),
                      "source_stage": payload["source_stage"], "texture_changes": 0}))


if __name__ == "__main__":
    main()
