extends Node2D

signal attack_hit
signal skill_hit
@export var autoplay := true
@export var root_motion_enabled := true
var root_distance := 0.0
var previous_root_distance := 0.0
var previous_time := 0.0
var walk_stride := 180.0
var animation_player: AnimationPlayer

func _ready() -> void:
	animation_player = $AnimationPlayer
	$RigEventRelay.attack_hit.connect(func(): attack_hit.emit())
	$RigEventRelay.skill_hit.connect(func(): skill_hit.emit())
	animation_player.animation_finished.connect(_finished)
	if autoplay: play_animation("idle")

func play_animation(animation: String) -> void:
	if not animation_player.has_animation(animation): return
	animation_player.stop()
	root_distance = 0.0
	previous_root_distance = 0.0
	previous_time = 0.0
	animation_player.play(animation)
	animation_player.advance(0.0)
	previous_root_distance = root_distance

func _process(_delta: float) -> void:
	if not animation_player.is_playing(): return
	var current := animation_player.current_animation_position
	var change := root_distance - previous_root_distance
	if animation_player.current_animation == "walk" and current < previous_time:
		change += walk_stride
	if root_motion_enabled:
		position += transform.basis_xform(Vector2(change, 0.0))
	previous_root_distance = root_distance
	previous_time = current

func _finished(animation: StringName) -> void:
	if animation in [&"attack_01", &"skill_01", &"hit"]:
		call_deferred("play_animation", "idle")
