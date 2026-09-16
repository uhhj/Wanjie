extends Node2D
signal attack_hit
signal command_release
@export var autoplay := true
@export var root_motion_enabled := true
@onready var animation_player: AnimationPlayer = $AnimationPlayer
var attack_hit_count := 0
var command_release_count := 0
var walk_clock := -1.0

func _ready() -> void:
	$RigEventRelay.attack_hit.connect(func(): attack_hit_count += 1; attack_hit.emit())
	$RigEventRelay.command_release.connect(func(): command_release_count += 1; command_release.emit())
	animation_player.animation_finished.connect(func(n):
		if n in [&"attack_01", &"hit", &"skill_command"]:
			play_animation("idle"))
	process_priority = 1
	if autoplay:
		play_animation("idle")

func play_animation(animation: String) -> void:
	assert(animation in ["idle", "walk", "attack_01", "hit", "death", "skill_command"])
	if animation == "attack_01": attack_hit_count = 0
	if animation == "skill_command": command_release_count = 0
	animation_player.stop()
	animation_player.play(animation)
	animation_player.advance(0.0)
	walk_clock = 0.0 if animation == "walk" else -1.0

func _process(_delta: float) -> void:
	if not root_motion_enabled or animation_player.assigned_animation != &"walk": return
	var now := animation_player.current_animation_position
	if walk_clock >= 0.0 and animation_player.is_playing():
		var elapsed := now - walk_clock
		if elapsed < 0.0: elapsed += 1.05
		position += transform.basis_xform(Vector2(280.0 * elapsed / 1.05, 0.0))
	walk_clock = now
