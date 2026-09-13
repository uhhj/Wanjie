extends Node2D
signal attack_hit
const DrawOrder = preload("res://scripts/rig/roman_guard_draw_order.gd")
@export var autoplay := true
@onready var animation_player: AnimationPlayer = $AnimationPlayer
@onready var relay = $RigEventRelay
var attack_hit_count := 0
@export var root_motion_enabled := true
var _walk_clock := -1.0
var walk_stride := 240.0

func _ready() -> void:
	DrawOrder.apply(self)
	relay.attack_hit.connect(_on_attack_hit)
	animation_player.animation_finished.connect(_on_finished)
	process_priority = 1
	var animations: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://resources/roman_guard_animations_v1.json"))
	walk_stride = float(animations.walk.root_motion_source_px_per_cycle)
	if autoplay:
		play_animation("idle")

func _on_attack_hit() -> void:
	attack_hit_count += 1
	attack_hit.emit()

func _on_finished(name: StringName) -> void:
	if name == &"attack_01" or name == &"hit":
		play_animation("idle")

func play_animation(name: String) -> void:
	assert(name in ["idle", "walk", "attack_01", "hit", "death"])
	if name == "attack_01":
		attack_hit_count = 0
	animation_player.stop()
	animation_player.play(name)
	animation_player.advance(0.0)
	_walk_clock = 0.0 if name=="walk" else -1.0

func _process(_delta: float) -> void:
	if not root_motion_enabled or animation_player.assigned_animation != &"walk":
		return
	var now := animation_player.current_animation_position
	if _walk_clock >= 0.0 and animation_player.is_playing():
		var elapsed := now-_walk_clock
		if elapsed < 0.0:
			elapsed += animation_player.current_animation_length
		position += transform.basis_xform(Vector2(walk_stride*elapsed/animation_player.current_animation_length,0))
	_walk_clock = now

func rest_pose() -> void:
	animation_player.stop()
	var data = JSON.parse_string(FileAccess.get_file_as_string("res://resources/human_medium_rig_v1.json"))
	for name in data.bones:
		var bone = get_node("VisualRoot/Skeleton2D/" + data.bones[name].path) as Bone2D
		bone.apply_rest()
	$VisualRoot.position = Vector2.ZERO
	$VisualRoot.rotation = 0.0
	$DeathBlood.phase = -1.0
	for part in ["arm_near_upper","arm_far_upper","foot_far"]:
		find_child("Art_"+part,true,false).visible = true
		find_child("Art_"+part+"_skinned",true,false).visible = false
