extends Node2D
signal attack_hit
const DrawOrder = preload("res://scripts/rig/roman_guard_draw_order.gd")
@export var autoplay := true
@onready var animation_player: AnimationPlayer = $AnimationPlayer
@onready var relay = $RigEventRelay
var attack_hit_count := 0

func _ready() -> void:
	DrawOrder.apply(self)
	relay.attack_hit.connect(_on_attack_hit)
	animation_player.animation_finished.connect(_on_finished)
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

func rest_pose() -> void:
	animation_player.stop()
	var data = JSON.parse_string(FileAccess.get_file_as_string("res://resources/human_medium_rig_v1.json"))
	for name in data.bones:
		var bone = get_node("VisualRoot/Skeleton2D/" + data.bones[name].path) as Bone2D
		bone.apply_rest()
	$VisualRoot.position = Vector2.ZERO
	$VisualRoot.rotation = 0.0
