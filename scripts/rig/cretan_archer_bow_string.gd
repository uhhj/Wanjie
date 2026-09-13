extends Line2D

# Socket-local attachment geometry, measured from the approved bow.
@export var top_anchor := Vector2(-54.0, -575.0)
@export var bottom_anchor := Vector2(-125.0, 515.0)
@export var draw_point := Vector2(-91.45, 0.0):
	set(value):
		draw_point = value
		_refresh_points()

func _ready() -> void:
	# Keep the serialized combat-readable source width. Resetting it to2 here
	# reduced the line below one display pixel and produced apparent dashes.
	default_color = Color(0.22, 0.16, 0.10, 1.0)
	antialiased = true
	_refresh_points()

func _refresh_points() -> void:
	points = PackedVector2Array([top_anchor, draw_point, bottom_anchor])
