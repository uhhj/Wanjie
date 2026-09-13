"""Compare motion-reference cues with current SHA-bound real Godot captures.

Reference cells may be normalized for legibility. Native 256px render crops are
never resized, interpolated into new poses, retargeted or re-rendered in Python.
The images document phase correspondence; they do not assign visual PASS.
"""
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports/cretan_archer/native"
CAPTURE_FILE = REPORT / "capture_manifest.json"
REFERENCE_MANIFEST = ROOT / "art_source/odyssey/cretan_archer/motion_reference/source_manifest.json"
ANIMATION_FILE = ROOT / "resources/cretan_archer_animations_v1.json"
PARTS_MANIFEST = ROOT / "tools/cretan_archer_parts_manifest.json"
CURRENT_INPUTS = [
    "scenes/units/odyssey/cretan_archer/cretan_archer_rig.tscn",
    "resources/cretan_archer_animations_v1.tres",
    "resources/cretan_archer_rig_v1.json",
    "resources/cretan_archer_animations_v1.json",
    "resources/cretan_archer_local_skinning.json",
    "scripts/rig/cretan_archer_rig.gd",
]
# The supplied strips are illustrations, not equally spaced sprite sheets.
# These review-only horizontal windows were selected from the visible poses.
# They retain each pose's head/feet/bow; neighbouring fragments may remain where
# drawn extremities overlap. No pixels are isolated or reused as production art.
REFERENCE_WINDOWS = {
    "ATTACK_REFERENCE_V1": [(0, 237), (214, 446), (428, 654), (632, 896),
                            (870, 1139), (1118, 1426), (1395, 1652),
                            (1654, 1935), (1941, 2172)],
    "DEATH_REFERENCE_V1": [(0, 285), (260, 545), (505, 808), (725, 1070),
                           (970, 1320), (1245, 1655), (1560, 1920), (1840, 2172)],
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve(path):
    result = (ROOT / str(path).removeprefix("res://")).resolve()
    if not result.is_relative_to(ROOT):
        raise ValueError("Comparison inputs must be within the repository")
    return result


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def font(size):
    return ImageFont.truetype("C:/Windows/Fonts/arial.ttf", size)


def validate_capture():
    capture = read(CAPTURE_FILE)
    if capture.get("status") != "PASS" or capture.get("inputs_unchanged_during_capture") is not True:
        raise ValueError("Actual current GPU capture must pass before phase comparison")
    if capture.get("display_server") == "headless" or "Actual GPU" not in capture.get("source", ""):
        raise ValueError("Comparison requires actual Godot GPU frames, not synthetic poses")
    bindings = capture.get("artifact_inputs", {})
    for name in CURRENT_INPUTS:
        path = resolve(name)
        recorded = bindings.get("res://" + name, bindings.get(name))
        if recorded is None or sha(path) != recorded:
            raise ValueError("Capture is stale or lacks input binding: " + name)
    for name, digest in bindings.items():
        if sha(resolve(name)) != digest:
            raise ValueError("Capture-bound input changed: " + name)
    manifest = read(PARTS_MANIFEST)
    if manifest.get("status") != "PASS" or len(manifest.get("parts", [])) != 20:
        raise ValueError("Formal Archer assets are not approved")
    for part in manifest["parts"]:
        if part.get("status") != "PASS" or sha(resolve(part["file"])) != part["sha256"]:
            raise ValueError("Formal texture changed: " + part["name"])
    return capture


def reference_cell(image, role, index):
    if image.size != (2172, 724):
        raise ValueError("Motion reference dimensions changed; review crop windows")
    left, right = REFERENCE_WINDOWS[role][index - 1]
    box = (left, 0, right, image.height)
    cell = image.crop(box).convert("RGB")
    # Background trimming only, for the motion-reference thumbnail. It never
    # supplies segmentation or production pixels to any rig asset.
    dark = np.min(np.asarray(cell), axis=2) < 140
    yy, xx = np.where(dark)
    if len(xx):
        trim = (max(0, int(xx.min()) - 10), max(0, int(yy.min()) - 10),
                min(cell.width, int(xx.max()) + 11), min(cell.height, int(yy.max()) + 11))
        cell = cell.crop(trim)
    else:
        trim = (0, 0, cell.width, cell.height)
    cell.thumbnail((205, 285), Image.Resampling.LANCZOS)
    return cell, list(box), list(trim)


def native_crop(image, floor_y):
    pixels = np.asarray(image)
    body = pixels[:, :, 3] > 240
    # The capture ground/tick marks use alpha0.85. Opaque art gives a crop anchor;
    # generous padding retains transparent-antialiased weapon/cloth extremities.
    body[int(floor_y) + 1:] = False
    yy, xx = np.where(body)
    if not len(xx):
        raise ValueError("Capture has no visible character")
    box = (max(0, int(xx.min()) - 20), max(0, int(yy.min()) - 18),
           min(image.width, int(xx.max()) + 21), min(image.height, int(floor_y) + 11))
    crop = image.crop(box)
    # No resizing: every native pixel remains one report pixel.
    composite = Image.new("RGBA", crop.size, (232, 235, 238, 255))
    composite.alpha_composite(crop)
    return composite.convert("RGB"), list(box)


def phase_specs(animations):
    attack = animations["attack_01"]
    times = {item["name"]: float(item["time"]) for item in attack.get("key_phases", [])}
    release = float(attack["release_time"])
    attack_specs = [
        (1, "ready", times.get("ready", 0.0), "nearest"),
        (2, "retrieve_from_quiver", times.get("retrieve_from_quiver", .2), "nearest"),
        (3, "bring_arrow_forward", times.get("bring_arrow_forward", .34), "nearest"),
        (4, "nock_and_raise", float(attack["nock_time"]), "at_or_after"),
        (5, "draw_to_face_anchor", times.get("face_anchor_aim", .7), "nearest"),
        (6, "aim_before_release", release - .02, "before_release"),
        (7, "release_follow_through", release, "at_or_after"),
        (8, "controlled_recovery", times.get("recover", float(attack["length"]) * .88), "nearest"),
        (9, "ready_again", float(attack["length"]), "nearest"),
    ]
    death = animations["death"]
    length = float(death["length"])
    kneel_start, kneel_end = [float(v) for v in death["kneeling_hold_seconds"]]
    _, bow_release_end = [float(v) for v in death["bow_release_seconds"]]
    death_specs = [
        (1, "chest_reaction", length * .08, "nearest"),
        (2, "loss_of_balance", length * .20, "nearest"),
        (3, "lower_to_knee", max(0.0, kneel_start - .04), "nearest"),
        (4, "kneeling_support", (kneel_start + kneel_end) * .5, "nearest"),
        (5, "hands_reach_ground", kneel_end + .07, "nearest"),
        (6, "forward_collapse_bow_release", bow_release_end - .08, "nearest"),
        (7, "folded_settle", max(bow_release_end, length - .20), "nearest"),
        (8, "final_pose_hold", length, "nearest"),
    ]
    return {"attack_01": ("ATTACK_REFERENCE_V1", 9, attack_specs),
            "death": ("DEATH_REFERENCE_V1", 8, death_specs)}


def main():
    capture = validate_capture()
    captures_sha = sha(CAPTURE_FILE)
    references = read(REFERENCE_MANIFEST)
    refs = {record["role"]: record for record in references["files"]}
    animations = read(ANIMATION_FILE)
    prepared = []
    output_records = []
    selected_hashes = {}
    reference_hashes = {}
    for animation, (role, cell_count, specs) in phase_specs(animations).items():
        record = refs[role]
        if record["usage"] != "MOTION_ONLY" or record["pixels_in_formal_assets_allowed"] is not False:
            raise ValueError("Motion reference policy mismatch")
        ref_path = resolve(record["file"])
        if sha(ref_path) != record["sha256"]:
            raise ValueError("Motion reference SHA mismatch: " + role)
        reference_hashes[str(ref_path)] = record["sha256"]
        reference = Image.open(ref_path)
        rows = [row for row in capture["frames"] if row["animation"] == animation and row["height"] == 256]
        if len(rows) != 16:
            raise ValueError("Expected 16 actual 256px frames for " + animation)
        panels = []
        max_native_width, max_native_height = 0, 0
        for cell, name, target, selection in specs:
            eligible = rows
            if selection == "at_or_after":
                eligible = [r for r in rows if float(r["time"]) >= target - 1e-8]
            elif selection == "before_release":
                eligible = [r for r in rows if float(r["time"]) < float(animations["attack_01"]["release_time"])]
            if not eligible:
                raise ValueError("No actual capture in requested phase: " + name)
            row = min(eligible, key=lambda r: (round(abs(float(r["time"]) - target), 9), -float(r["time"])))
            frame_path = resolve(row["path"])
            if row.get("clipped") or sha(frame_path) != row["sha256"]:
                raise ValueError("Selected frame clipped or stale: " + str(frame_path))
            selected_hashes[str(frame_path)] = row["sha256"]
            with Image.open(frame_path) as frame:
                if frame.mode != "RGBA":
                    raise ValueError("Expected actual RGBA capture")
                native, crop_box = native_crop(frame, float(capture["floor_y"]))
            cue, cell_box, ref_trim = reference_cell(reference, role, cell)
            max_native_width = max(max_native_width, native.width)
            max_native_height = max(max_native_height, native.height)
            panel_record = {"animation": animation, "phase": name, "reference_cell": cell,
                            "authored_target_time": target, "selected_actual_time": row["time"],
                            "time_difference": float(row["time"]) - target,
                            "selection_rule": selection, "frame": row["path"], "frame_sha256": row["sha256"],
                            "native_crop_box": crop_box, "native_resize_applied": False,
                            "reference_cell_box": cell_box, "reference_trim_box": ref_trim,
                            "reference_window_selection": "visible pose extent, not equal-width cells",
                            "reference_thumbnail_only_normalized": True}
            panels.append((name, target, row, cue, native, panel_record))
        card_width = max(680, 240 + max_native_width + 24)
        card_height = max(365, max_native_height + 94)
        columns = 2
        sheet = Image.new("RGB", (card_width * columns, 86 + card_height * math.ceil(len(panels) / columns)), "#f5f5f3")
        draw = ImageDraw.Draw(sheet)
        draw.text((18, 12), f"Cretan Archer | {animation} | motion cues vs actual Godot 256px", font=font(23), fill="#182331")
        draw.text((18, 43), "Timing is authored, not copied uniformly from the strip. Native crops are 1:1 pixels; no synthesized poses.", font=font(15), fill="#374151")
        detail = ("Nock/release use the first eligible captured frame; exact event time is validated separately."
                  if animation == "attack_01" else
                  "Kneeling, hand support and settling use nearest real captured times; ground contact is validated separately.")
        draw.text((18, 63), "Reference correspondence is approximate. " + detail, font=font(13), fill="#596475")
        for index, (name, target, row, cue, native, panel_record) in enumerate(panels):
            x, y = (index % columns) * card_width, 86 + (index // columns) * card_height
            draw.rectangle((x + 7, y + 5, x + card_width - 7, y + card_height - 5), outline="#c9d0d5", width=1)
            draw.text((x + 18, y + 14), f"{index + 1}. {name.replace('_', ' ')}", font=font(18), fill="#172638")
            draw.text((x + 18, y + 41), f"Reference cell {panel_record['reference_cell']} / cue only", font=font(13), fill="#435469")
            draw.text((x + 240, y + 41), f"Godot 256px | actual t={float(row['time']):.3f}s | target={target:.3f}s", font=font(13), fill="#435469")
            sheet.paste(cue, (x + 18 + (205 - cue.width) // 2, y + 65))
            sheet.paste(native, (x + 240, y + 65))
            output_records.append(panel_record)
        filename = "attack_reference_comparison.png" if animation == "attack_01" else "death_reference_comparison.png"
        prepared.append((REPORT / filename, sheet))
    # Bind comparisons to immutable capture/ref inputs; do not publish a new
    # report if source data changed while assembling its panels.
    validate_capture()
    if sha(CAPTURE_FILE) != captures_sha:
        raise ValueError("Capture manifest changed while comparison was assembled")
    for filename, digest in {**selected_hashes, **reference_hashes}.items():
        if sha(Path(filename)) != digest:
            raise ValueError("Selected input changed while assembling comparison")
    for filename, image in prepared:
        image.save(filename)
    payload = {"status": "COMPARISONS_GENERATED_VISUAL_REVIEW_REQUIRED", "capture_manifest_sha256": captures_sha,
               "capture_inputs": capture["artifact_inputs"], "selected_frame_sha256": selected_hashes,
               "motion_reference_manifest_sha256": sha(REFERENCE_MANIFEST), "reference_sha256": reference_hashes,
               "native_display_height": 256, "native_pixels_resized": False,
               "frame_synthesis_performed": False, "pixel_similarity_is_gate": False,
               "outputs": [{"file": p.relative_to(ROOT).as_posix(), "sha256": sha(p)} for p, _ in prepared],
               "phase_panels": output_records}
    (REPORT / "motion_reference_comparison_manifest.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "phase_panels": len(output_records), "outputs": payload["outputs"]}))


if __name__ == "__main__":
    main()
