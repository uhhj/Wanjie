extends Node

signal attack_release

func _event_attack_release() -> void:
	attack_release.emit()
