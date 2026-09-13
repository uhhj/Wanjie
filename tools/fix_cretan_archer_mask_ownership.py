"""Repair reviewed source-pixel ownership without changing approved art or candidates.

Outputs are alternative candidate masks/PNGs, not formal asset approval. Hidden
anatomy remains absent until the separately recorded local completion is reviewed.
"""
import hashlib
import json
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
BODY = ROOT / "work/cretan_archer/04_complete_body_rgba.png"
INPUT = ROOT / "work/cretan_archer/candidates/parts"
OUTPUT = ROOT / "work/cretan_archer/self_repair/ownership"
REPORT = ROOT / "reports/cretan_archer/self_repair/ownership"
ORDER = ["arm_far_upper", "arm_far_fore", "hand_far", "leg_far_thigh",
         "leg_far_shin", "foot_far", "leg_near_thigh", "leg_near_shin",
         "foot_near", "pelvis", "torso", "head", "arm_near_upper",
         "arm_near_fore", "hand_near"]

# Traced from the approved Body at source coordinates, along the dark garment
# outline. These points describe cloth ownership, not a new garment silhouette.
HEM_EDGE = [
    (399, 943), (405, 937), (409, 939), (415, 935), (418, 938),
    (428, 935), (431, 941), (440, 938), (443, 937), (445, 941),
    (453, 941), (457, 944), (461, 942), (462, 960), (464, 953),
    (468, 962), (472, 958), (476, 966), (479, 963), (483, 973),
    (485, 970), (490, 983), (493, 966), (496, 940),
    (501, 938), (505, 936), (507, 941), (515, 939), (520, 943),
    (524, 940), (529, 947), (538, 943), (542, 950), (548, 947),
    (552, 954), (557, 952), (561, 957), (564, 966), (568, 963),
    (571, 969), (575, 965), (579, 970), (583, 965), (589, 970),
    (592, 965), (596, 969), (600, 964), (605, 967), (609, 964),
    (613, 966), (613, 954), (617, 956), (620, 953), (625, 956),
    (628, 952), (632, 953), (634, 949), (638, 953), (642, 950),
    (647, 951), (651, 954), (655, 952), (658, 954), (668, 956),
]
HEM = [(399, 910), (668, 910)] + list(reversed(HEM_EDGE))
# The dark red underside between legs is a garment tail, not either thigh.
CENTRAL_TAIL = [(515, 944), (520, 941), (532, 946), (535, 994),
                (527, 999), (522, 992), (516, 1002), (510, 997),
                (507, 993), (503, 998), (499, 995), (508, 975)]
OUTER_HEM_FLAPS = [
    [(398, 936), (402, 942), (400, 976), (395, 974), (390, 971),
     (385, 973), (381, 967), (375, 969), (371, 962), (367, 964), (366, 953)],
    [(634, 947), (667, 946), (663, 955), (658, 958), (652, 957),
     (650, 962), (644, 961), (641, 965), (634, 966)],
]
NEAR_SLEEVE = [(400, 355), (423, 357), (442, 369), (459, 389),
               (476, 417), (488, 448), (489, 473), (484, 494),
               (474, 516), (456, 537), (444, 547), (420, 550),
               (385, 520), (340, 511), (347, 431), (366, 380)]
FAR_SLEEVE = [(609, 395), (618, 427), (625, 465), (624, 504),
              (620, 545), (640, 543), (671, 523), (657, 471),
              (647, 432), (630, 407)]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def polygon(points, size):
    image = Image.new("L", size)
    ImageDraw.Draw(image).polygon(points, fill=255)
    return np.asarray(image) > 0


def bbox(mask):
    y, x = np.where(mask)
    return [int(x.min()), int(y.min()), int(x.max()) + 1, int(y.max()) + 1] if len(x) else None


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def compose(parts):
    result = Image.new("RGBA", parts[ORDER[0]].size)
    for name in ORDER:
        result.alpha_composite(parts[name])
    return result


def on_gray(im):
    out = Image.new("RGBA", im.size, (128, 128, 128, 255))
    out.alpha_composite(im)
    return out.convert("RGB")


def run():
    for path in [OUTPUT, OUTPUT / "masks", REPORT]:
        path.mkdir(parents=True, exist_ok=True)
    source_sha = sha(BODY)
    source = Image.open(BODY).convert("RGBA")
    a = np.array(source)
    input_sha = {name: sha(INPUT / (name + ".png")) for name in ORDER}
    originals = {name: Image.open(INPUT / (name + ".png")).convert("RGBA") for name in ORDER}
    masks = {name: np.array(originals[name])[:, :, 3] > 0 for name in ORDER}
    initial_union = np.logical_or.reduce(list(masks.values()))
    changes = []
    transfer_overlay = np.zeros((source.height, source.width, 4), dtype=np.uint8)

    def transfer(donor, receiver, region, reason, color):
        changed = masks[donor] & region
        masks[donor][changed] = False
        masks[receiver][changed] = True
        transfer_overlay[changed] = (*color, 220)
        changes.append({"operation": "transfer_source_ownership", "from": donor,
                        "to": receiver, "reason": reason, "pixels": int(changed.sum()),
                        "bbox": bbox(changed)})

    cloth = polygon(HEM, source.size) | polygon(CENTRAL_TAIL, source.size)
    for flap in OUTER_HEM_FLAPS:
        cloth |= polygon(flap, source.size)
    # A narrow, color-assisted fringe captures remaining ivory/red hem samples
    # next to the traced line. This never changes RGB or source alpha and cannot
    # select remote skin by a global color threshold.
    fringe = np.asarray(Image.fromarray(cloth.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(9))) > 0
    rgb = a[:, :, :3].astype(int)
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    ivory = (r > 100) & (abs(r - g) < 25) & (abs(g - b) < 35)
    dark_red = (r > 65) & (g < r * .48) & (b < r * .48)
    cloth |= fringe & (ivory | dark_red)
    for name in ["leg_near_thigh", "leg_far_thigh"]:
        transfer(name, "pelvis", cloth, "visible hem and central cloth must not rotate with a thigh", (240, 120, 50))
        # Ownership transfer can isolate tiny pieces of the formerly connected
        # cloth edge. Reassign only small components wholly in the reviewed hem
        # rectangle; this is not a background speck/alpha cleanup operation.
        seen = np.zeros(initial_union.shape, dtype=bool)
        fragments = np.zeros_like(seen)
        for y, x in zip(*np.where(masks[name])):
            if seen[y, x]:
                continue
            queue = deque([(int(y), int(x))])
            seen[y, x] = True
            points = []
            while queue:
                py, px = queue.popleft()
                points.append((py, px))
                for dy, dx in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    ny, nx = py + dy, px + dx
                    if 0 <= ny < source.height and 0 <= nx < source.width and masks[name][ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        queue.append((ny, nx))
            if len(points) <= 160 and all(927 <= py <= 1005 and 390 <= px <= 668 for py, px in points):
                for py, px in points:
                    fragments[py, px] = True
        transfer(name, "pelvis", fragments, "small isolated source fragments along traced garment edge", (240, 120, 50))
    transfer("torso", "arm_near_upper", polygon(NEAR_SLEEVE, source.size),
             "white near sleeve follows arm; torso completion remains separately required", (30, 170, 240))
    transfer("torso", "arm_far_upper", polygon(FAR_SLEEVE, source.size),
             "white far sleeve follows arm; keep chest and shoulder strap in torso", (150, 80, 230))

    bridge = np.zeros(initial_union.shape, dtype=bool)
    for x in range(510, 628):
        # The slanted cap starts between y1095 and y1097, not at one global row.
        # Fill only the short gap between existing upper thigh and cap evidence.
        above = np.flatnonzero(masks["leg_far_thigh"][1088:1092, x])
        below = np.flatnonzero(masks["leg_far_thigh"][1092:1103, x])
        if len(above) and len(below):
            start, end = 1088 + int(above[-1]) + 1, 1092 + int(below[0])
            bridge[start:end, x] = masks["leg_far_shin"][start:end, x]
    masks["leg_far_thigh"] |= bridge
    transfer_overlay[bridge] = (80, 240, 100, 220)
    changes.append({"operation": "duplicate_source_for_connected_overlap", "from": "leg_far_shin",
                    "to": "leg_far_thigh", "reason": "bridge three-row gap plus slanted first cap row using each column's existing source pixels",
                    "pixels": int(bridge.sum()), "bbox": bbox(bridge)})

    final_union = np.logical_or.reduce(list(masks.values()))
    assert np.array_equal(initial_union, final_union), "Ownership correction changed source coverage"
    parts = {}
    entries = []
    for name in ORDER:
        pixels = a.copy()
        pixels[:, :, 3] = np.where(masks[name], a[:, :, 3], 0)
        pixels[pixels[:, :, 3] == 0, :3] = 0
        parts[name] = Image.fromarray(pixels)
        part_path = OUTPUT / (name + ".png")
        parts[name].save(part_path)
        Image.fromarray(masks[name].astype(np.uint8) * 255).save(OUTPUT / "masks" / (name + ".png"))
        fg = pixels[:, :, 3] > 0
        rgb_difference = np.abs(pixels[:, :, :3].astype(int) - a[:, :, :3].astype(int))
        assert not bool(np.any(rgb_difference[fg]))
        entries.append({"name": name, "file": str(part_path.relative_to(ROOT)).replace("\\", "/"),
                        "sha256": sha(part_path), "source_rgb_changed_pixels": 0,
                        "canvas": list(source.size), "mode": "RGBA"})

    before = compose(originals)
    after = compose(parts)
    after.save(REPORT / "body_recomposed_0deg.png")
    delta = np.abs(np.array(after).astype(int) - np.array(before).astype(int))
    source_delta = np.abs(np.array(after).astype(int) - a.astype(int))
    comparison = Image.new("RGB", (source.width * 3, source.height + 40), "white")
    d = ImageDraw.Draw(comparison)
    for i, (label, im) in enumerate([("Approved Body", source), ("Original candidate rest", before), ("Ownership corrected rest", after)]):
        comparison.paste(on_gray(im), (i * source.width, 40))
        d.text((i * source.width + 12, 10), label, fill="black")
    comparison.save(REPORT / "body_recomposition_review.png")
    review = on_gray(source).convert("RGBA")
    review.alpha_composite(Image.fromarray(transfer_overlay))
    review.convert("RGB").save(REPORT / "ownership_changes_overlay.png")
    # Exact 256/192 character heights; art bbox spans 1342 source pixels here.
    art_bbox = source.getchannel("A").getbbox()
    art_height = art_bbox[3] - art_bbox[1]
    combat = Image.new("RGB", (900, 600), "#eeeeee")
    dc = ImageDraw.Draw(combat)
    for row, height in enumerate([256, 192]):
        scale = height / art_height
        for col, (label, im) in enumerate([("Approved Body", source), ("Previous", before), ("Corrected ownership", after)]):
            view = im.resize((round(im.width * scale), round(im.height * scale)), Image.Resampling.LANCZOS)
            combat.paste(on_gray(view), (col * 300 + 20, row * 310 + 25))
            dc.text((col * 300 + 20, row * 310 + 5), f"{label} / {height}px", fill="black")
    combat.save(REPORT / "body_rest_combat_review.png")
    detail = Image.new("RGB", (1600, 600), "#eeeeee")
    dd = ImageDraw.Draw(detail)
    for i, name in enumerate(["leg_near_thigh", "leg_far_thigh"]):
        crop = parts[name].crop((310, 900, 710, 1150)).resize((800, 500))
        detail.paste(on_gray(crop), (i * 800, 50))
        dd.text((i * 800 + 20, 10), name, fill="black")
    detail.save(REPORT / "thigh_ownership_detail.png")
    unresolved = [
        {"id": "under_hand_garment", "bbox": [350, 768, 455, 926], "status": "LOCAL_COMPLETION_REQUIRED", "note": "Real skirt pixels hidden by hand cannot be restored by changing ownership."},
        {"id": "hidden_near_hip", "bbox": [392, 807, 523, 994], "status": "LOCAL_COMPLETION_REQUIRED", "note": "Thigh needs continuous skin cap beneath garment; no cloth cap retained."},
        {"id": "hidden_far_hip", "bbox": [514, 807, 642, 994], "status": "LOCAL_COMPLETION_REQUIRED", "note": "Thigh needs continuous skin cap beneath garment."},
        {"id": "torso_under_near_sleeve", "bbox": [389, 354, 496, 592], "status": "LOCAL_COMPLETION_REQUIRED", "note": "Visible sleeve was transferred to upper arm; underlying torso remains intentionally incomplete."},
        {"id": "hem_trace_dark_edge", "bbox": [399, 927, 659, 1001], "status": "COMBAT_SCALE_MOTION_REVIEW_REQUIRED", "note": "Hand-traced dark garment edge may have approximately 1 px source uncertainty; do not globally erode or recolor."},
        {"id": "far_shoulder_backfill", "bbox": [590, 395, 661, 545], "status": "MOTION_REVIEW_REQUIRED", "note": "Far upper arm renders behind torso. Confirm actual shoulder excursion before requesting hidden torso fill."},
    ]
    assert sha(BODY) == source_sha
    assert all(sha(INPUT / (name + ".png")) == digest for name, digest in input_sha.items())
    metrics = {"status": "SOURCE_PIXEL_OWNERSHIP_FIXED_HIDDEN_COMPLETION_PENDING",
               "body_source": str(BODY.relative_to(ROOT)).replace("\\", "/"), "body_sha256": source_sha,
               "input_candidates_unchanged": True, "approved_body_unchanged": True,
               "canvas_width": source.width, "canvas_height": source.height, "part_count": len(parts),
               "source_rgb_changed_pixels": 0, "source_alpha_changed_for_retained_pixels": 0,
               "union_coverage_before": int(initial_union.sum()), "union_coverage_after": int(final_union.sum()),
               "union_lost_pixels": int((initial_union & ~final_union).sum()),
               "union_added_pixels": int((final_union & ~initial_union).sum()),
               "previous_unassigned_source_pixels": int(((a[:, :, 3] > 0) & ~initial_union).sum()),
               "rest_vs_previous_changed_pixels": int(np.any(delta, axis=2).sum()),
               "rest_vs_previous_max_rgba_difference": int(delta.max()),
               "rest_vs_source_max_rgba_difference": int(source_delta.max()),
               "rest_alpha_overlap_note": "Ordinary source-over may increase fractional alpha at duplicate joint pixels; no compensation or forged exact-match image applied.",
               "operations": changes, "parts": entries, "unresolved_regions": unresolved,
               "formal_approval": False, "godot_handoff": "NOT_READY"}
    write_json(REPORT / "metrics.json", metrics)
    write_json(REPORT / "trace_definition.json", {"hem_edge": HEM_EDGE, "central_tail": CENTRAL_TAIL, "outer_hem_flaps": OUTER_HEM_FLAPS,
               "near_sleeve": NEAR_SLEEVE, "far_sleeve": FAR_SLEEVE})
    print(json.dumps({key: metrics[key] for key in ["status", "part_count", "source_rgb_changed_pixels", "union_lost_pixels", "union_added_pixels", "rest_vs_previous_changed_pixels"]}))


if __name__ == "__main__":
    run()
