extends Node
signal attack_hit

func _event_attack_hit() -> void:
	attack_hit.emit()
