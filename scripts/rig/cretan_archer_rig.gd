extends Node2D

signal attack_release

const ANIMATION_DATA := "res://resources/cretan_archer_animations_v1.json"
const RIG_DATA := "res://resources/cretan_archer_rig_v1.json"
const ANIMATIONS := ["idle", "walk", "attack_01", "hit", "death"]

@export var autoplay := true
@export var root_motion_enabled := true
@onready var animation_player: AnimationPlayer = $AnimationPlayer
@onready var relay: Node = $RigEventRelay
var attack_release_count := 0
var walk_stride := 0.0
var _walk_clock := -1.0

func _ready() -> void:
	relay.connect("attack_release", _on_attack_release)
	animation_player.animation_finished.connect(_on_animation_finished)
	process_priority = 1
	var animations: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(ANIMATION_DATA))
	walk_stride = float(animations.walk.get("root_motion_source_px_per_cycle", 0.0))
	if autoplay:
		play_animation("idle")

func _on_attack_release() -> void:
	attack_release_count += 1
	attack_release.emit()

func _on_animation_finished(name: StringName) -> void:
	if name == &"attack_01" or name == &"hit":
		play_animation("idle")

func play_animation(name: String) -> void:
	assert(name in ANIMATIONS, "Unsupported Archer animation: " + name)
	if name == "attack_01":
		attack_release_count = 0
	animation_player.stop()
	animation_player.play(name)
	animation_player.advance(0.0)
	_walk_clock = 0.0 if name == "walk" else -1.0

func _process(_delta: float) -> void:
	if not root_motion_enabled or animation_player.assigned_animation != &"walk":
		return
	var now := animation_player.current_animation_position
	if _walk_clock >= 0.0 and animation_player.is_playing():
		var elapsed := now - _walk_clock
		if elapsed < 0.0:
			elapsed += animation_player.current_animation_length
		position += transform.basis_xform(Vector2(walk_stride * elapsed / animation_player.current_animation_length, 0.0))
	_walk_clock = now

func rest_pose() -> void:
	animation_player.stop()
	_walk_clock = -1.0
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(RIG_DATA))
	for bone_name in data.bones:
		var bone := get_node("VisualRoot/Skeleton2D/" + data.bones[bone_name].path) as Bone2D
		bone.apply_rest()
	$VisualRoot.position = Vector2.ZERO
	$VisualRoot.rotation = 0.0
	var arrow := find_child("Art_arrow_single", true, false) as Sprite2D
	arrow.visible = false
	var bow_string := find_child("Art_bow_string", true, false)
	bow_string.set("draw_point", Vector2(-91.45, 0.0))
