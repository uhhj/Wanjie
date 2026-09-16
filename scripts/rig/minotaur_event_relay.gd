extends Node
signal attack_hit
signal skill_hit

func _event_attack_hit() -> void:
	attack_hit.emit()

func _event_skill_hit() -> void:
	skill_hit.emit()
