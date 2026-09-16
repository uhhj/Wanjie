extends Node
signal attack_hit
signal command_release

func _event_attack_hit() -> void:
	attack_hit.emit()

func _event_command_release() -> void:
	command_release.emit()
