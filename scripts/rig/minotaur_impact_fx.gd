extends Node2D
## Deterministic ground-impact dust driven by an AnimationPlayer value track.
## progress: 0 before contact, eases 0->1 over the burst window, stays 1 (invisible).

const DUST := Color(0.60, 0.52, 0.42)
const DUST_DARK := Color(0.42, 0.36, 0.29)
const PUFF_COUNT := 12

var progress := 0.0:
	set(value):
		progress = value
		queue_redraw()

func _puff(i: int) -> Dictionary:
	# Fixed pseudo-random fan so every frame renders identically.
	var fi := float(i)
	var angle: float = deg_to_rad(150.0 + 62.0 * fi / float(PUFF_COUNT - 1) + 9.0 * sin(fi * 2.3))
	var speed: float = 120.0 + 210.0 * absf(sin(fi * 1.7 + 0.5))
	var size: float = 7.0 + 11.0 * absf(cos(fi * 1.3 + 0.2))
	return {"angle": angle, "speed": speed, "size": size}

func _draw() -> void:
	if progress <= 0.0 or progress >= 1.0:
		return
	var e: float = 1.0 - pow(1.0 - progress, 2.0)  # ease-out travel
	var fade: float = pow(1.0 - progress, 1.35)
	# Ground shockwave arc opening upward from the contact point.
	var radius: float = 26.0 + 240.0 * e
	draw_arc(Vector2.ZERO, radius, deg_to_rad(158.0), deg_to_rad(22.0), 26,
		Color(DUST_DARK.r, DUST_DARK.g, DUST_DARK.b, 0.85 * fade), 5.0 * (1.0 - progress) + 1.5)
	draw_arc(Vector2.ZERO, radius * 0.62, deg_to_rad(166.0), deg_to_rad(14.0), 20,
		Color(DUST.r, DUST.g, DUST.b, 0.7 * fade), 3.5 * (1.0 - progress) + 1.0)
	# Rising dust puffs on ballistic paths.
	for i in PUFF_COUNT:
		var puff: Dictionary = _puff(i)
		var travel: float = puff["speed"] * e
		var gravity_drop: float = 320.0 * progress * progress
		var pos := Vector2(cos(puff["angle"]) * travel, sin(puff["angle"]) * travel + gravity_drop)
		var size: float = puff["size"] * (0.55 + 0.75 * progress)
		draw_circle(pos, size, Color(DUST.r, DUST.g, DUST.b, 0.8 * fade))
		draw_circle(pos + Vector2(size * 0.4, -size * 0.3), size * 0.55,
			Color(DUST.r + 0.05, DUST.g + 0.05, DUST.b + 0.05, 0.6 * fade))
	# Small dark debris chips flying higher.
	var chip_base := PackedVector2Array([Vector2(-4, -2), Vector2(3, -4), Vector2(5, 2), Vector2(-2, 4)])
	for i in 5:
		var fi := float(i)
		var chip_angle: float = deg_to_rad(118.0 + 26.0 * fi + 6.0 * cos(fi * 3.1))
		var travel: float = (250.0 + 130.0 * sin(fi * 2.9 + 1.1)) * e
		var pos := Vector2(cos(chip_angle) * travel, sin(chip_angle) * travel - 40.0 * progress)
		var scale_f: float = 1.0 - 0.4 * progress
		var pts := PackedVector2Array()
		for point in chip_base:
			pts.append(point * scale_f + pos)
		draw_colored_polygon(pts, Color(DUST_DARK.r, DUST_DARK.g, DUST_DARK.b, 0.9 * fade))
