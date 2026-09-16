extends SceneTree

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://resources/minotaur_breaker_rig_v1.json"))
	var packed: PackedScene = load("res://scenes/rigs/biped_large_rig_v1.tscn")
	var skeleton: Skeleton2D = packed.instantiate()
	root.add_child(skeleton)
	var errors: Array = []
	var version: Dictionary = Engine.get_version_info()
	if version.major != 4 or version.minor != 7 or version.patch != 2 or str(version.status) != "stable":
		errors.append("Wrong required engine version")
	var bones := skeleton.find_children("*", "Bone2D", true, false)
	if bones.size() != data.bones.size():
		errors.append("Bone count mismatch")
	for name in data.bones:
		var record: Dictionary = data.bones[name]
		var bone := skeleton.get_node_or_null(NodePath(record.path)) as Bone2D
		if bone == null:
			errors.append("Missing bone " + name)
			continue
		var expected := Vector2(record.pivot[0], record.pivot[1])
		if bone.global_position.distance_to(expected) > 0.001:
			errors.append("Rest position mismatch " + name)
		if not bone.transform.is_equal_approx(bone.rest):
			errors.append("Rest transform mismatch " + name)
		if bone.length <= 0.0:
			errors.append("Invalid bone length " + name)
	var relay := Node.new()
	relay.set_script(load("res://scripts/rig/minotaur_event_relay.gd"))
	root.add_child(relay)
	var counts := [0, 0]
	relay.attack_hit.connect(func(): counts[0] += 1)
	relay.skill_hit.connect(func(): counts[1] += 1)
	relay._event_attack_hit()
	relay._event_skill_hit()
	if counts != [1, 1]:
		errors.append("Separate relay signals failed")
	var report := {"status":"PASS" if errors.is_empty() else "FAIL", "scope":"Structural scaffold and signal isolation only; not animation approval", "godot":version.string, "bone_count":bones.size(), "rest_pivots_checked":data.bones.size(), "relay_counts":counts, "errors":errors}
	var file := FileAccess.open("res://reports/minotaur_breaker/structure_test.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  ") + "\n")
	print(JSON.stringify(report))
	skeleton.queue_free()
	relay.queue_free()
	quit(0 if errors.is_empty() else 1)
