extends SceneTree

const RIG_FILE := "res://resources/cretan_archer_rig_v1.json"
const ANIMATION_FILE := "res://resources/cretan_archer_animations_v1.json"
const SKINNING_FILE := "res://resources/cretan_archer_local_skinning.json"
const MANIFEST_FILE := "res://tools/cretan_archer_parts_manifest.json"
const OUTPUT_SCENE := "res://scenes/units/odyssey/cretan_archer/cretan_archer_rig.tscn"
const OUTPUT_LIBRARY := "res://resources/cretan_archer_animations_v1.tres"
const EXPECTED_PARTS := ["head", "torso", "pelvis", "arm_near_upper", "arm_near_fore", "hand_near", "arm_far_upper", "arm_far_fore", "hand_far", "leg_near_thigh", "leg_near_shin", "foot_near", "leg_far_thigh", "leg_far_shin", "foot_far", "bow", "bow_string", "quiver", "cloak", "arrow_single"]

func _initialize() -> void:
	call_deferred("build")

func vector(value: Array) -> Vector2:
	return Vector2(float(value[0]), float(value[1]))

func read_json(path: String) -> Dictionary:
	assert(FileAccess.file_exists(path), "Missing required file: " + path)
	var result = JSON.parse_string(FileAccess.get_file_as_string(path))
	assert(result is Dictionary, "Expected JSON object: " + path)
	return result

func own_tree(node: Node, scene_root: Node) -> void:
	for child in node.get_children():
		child.owner = scene_root
		own_tree(child, scene_root)

func value_track(anim: Animation, path: String, times: Array, values: Array, discrete := false) -> void:
	assert(times.size() == values.size(), "Track time/value count mismatch: " + path)
	var index := anim.add_track(Animation.TYPE_VALUE)
	anim.track_set_path(index, NodePath(path))
	anim.value_track_set_update_mode(index, Animation.UPDATE_DISCRETE if discrete else Animation.UPDATE_CONTINUOUS)
	for i in range(times.size()):
		anim.track_insert_key(index, float(times[i]), values[i])

func ensure_bone(skeleton: Skeleton2D, records: Dictionary, name: String) -> Bone2D:
	var record: Dictionary = records[name]
	if skeleton.has_node(NodePath(record.path)):
		return skeleton.get_node(NodePath(record.path)) as Bone2D
	var parent: Node = skeleton
	if not str(record.parent).is_empty():
		parent = ensure_bone(skeleton, records, str(record.parent))
	var bone := Bone2D.new()
	bone.name = name
	parent.add_child(bone)
	return bone

func set_order(node: CanvasItem, name: String, draw_order: Array) -> void:
	assert(name in draw_order, "Missing centralized draw order: " + name)
	node.z_as_relative = false
	node.z_index = draw_order.find(name) * 2

func build() -> void:
	var manifest := read_json(MANIFEST_FILE)
	if manifest.get("status", "") != "PASS":
		push_error("STOP: Archer formal part manifest must be PASS before native scene assembly")
		quit(2)
		return
	var part_files: Dictionary = {}
	for part in manifest.parts:
		assert(part.name not in part_files, "Duplicate part: " + str(part.name))
		assert(part.get("status", "") == "PASS", "Part not formally approved: " + str(part.name))
		part_files[part.name] = "res://" + str(part.file).trim_prefix("res://")
		assert(FileAccess.file_exists(part_files[part.name]), "Missing formal part: " + str(part.name))
		assert(FileAccess.get_sha256(part_files[part.name]) == part.sha256, "Formal part SHA mismatch: " + str(part.name))
	assert(part_files.size() == EXPECTED_PARTS.size(), "Exactly20 approved Archer parts required")
	for name in EXPECTED_PARTS:
		assert(name in part_files and FileAccess.file_exists(part_files[name]), "Missing approved part: " + name)
	var data := read_json(RIG_FILE)
	var animations := read_json(ANIMATION_FILE)
	assert(animations.size() == 5, "Exactly five animations required")
	for name in ["idle", "walk", "attack_01", "hit", "death"]:
		assert(name in animations, "Missing animation: " + name)
	var origin := vector(data.origin)
	var unit := Node2D.new()
	unit.name = "CretanArcher"
	unit.set_script(load("res://scripts/rig/cretan_archer_rig.gd"))
	unit.set("autoplay", false)
	var visual := Node2D.new()
	visual.name = "VisualRoot"
	unit.add_child(visual)
	var skeleton := load("res://scenes/rigs/human_medium_rig_v1.tscn").instantiate() as Skeleton2D
	skeleton.scene_file_path = ""
	skeleton.name = "Skeleton2D"
	skeleton.position = -origin
	visual.add_child(skeleton)
	# Adapt only the owned unit copy. Shared skeleton and Roman resources stay unchanged.
	for name in data.bones:
		var bone := ensure_bone(skeleton, data.bones, name)
		var record: Dictionary = data.bones[name]
		bone.position = vector(record.local_position)
		bone.rest = Transform2D(0.0, bone.position)
		bone.rotation = 0.0
		bone.set_autocalculate_length_and_angle(false)
		bone.length = float(record.length)
		bone.bone_angle = float(record.bone_angle)
	assert(skeleton.find_children("*", "Bone2D", true, false).size() == data.bones.size(), "Unexpected inherited/missing bone")
	for name in EXPECTED_PARTS:
		var bone_name: String = str(data.attachments.get(name, name))
		assert(bone_name in data.bones, "Invalid part attachment: " + name)
		var bone := skeleton.get_node(NodePath(data.bones[bone_name].path)) as Bone2D
		if name == "bow_string":
			var string := Line2D.new()
			string.name = "Art_bow_string"
			string.set_script(load("res://scripts/rig/cretan_archer_bow_string.gd"))
			# A subpixel source-width string broke into dashes at combat scale.
			string.width = 8.0
			string.default_color = Color(0.22, 0.16, 0.10, 1.0)
			string.antialiased = true
			string.points = PackedVector2Array([Vector2(-54.0, -575.0), Vector2(-91.45, 0.0), Vector2(-125.0, 515.0)])
			set_order(string, name, data.draw_order)
			bone.add_child(string)
			continue
		var sprite := Sprite2D.new()
		sprite.name = "Art_" + name
		sprite.texture = load(part_files[name])
		assert(sprite.texture != null, "Texture failed to load: " + name)
		sprite.centered = false
		sprite.position = -Vector2(282.0, 725.0) if name == "arrow_single" else -vector(data.bones[bone_name].pivot)
		sprite.scale = Vector2.ONE
		sprite.visible = name != "arrow_single"
		set_order(sprite, name, data.draw_order)
		bone.add_child(sprite)
	# Local native deformation closes moving shoulder/elbow/knee/ankle boundaries
	# without replacing a single approved texture or UV coordinate.
	var skinning := read_json(SKINNING_FILE)
	assert(FileAccess.get_sha256(RIG_FILE) == skinning.rig_sha256, "Stale Archer skinning rig coordinates")
	assert(skinning.meshes.size() == 8, "Exactly8 Archer local bindings expected")
	for record in skinning.meshes:
		var name: String = record.part
		assert(name in part_files, "Unknown skinned Archer part: " + name)
		assert(FileAccess.get_sha256(part_files[name]) == record.texture_sha256, "Skinning texture SHA mismatch: " + name)
		assert(record.vertices.size() == record.uv.size(), "Vertex/UV count mismatch")
		assert(record.vertices == record.uv, "Archer skinning must preserve original source UVs")
		var mesh := Polygon2D.new()
		mesh.name = "Art_" + name + "_skinned"
		mesh.position = -origin
		var vertices := PackedVector2Array()
		var uv := PackedVector2Array()
		for point in record.vertices:
			vertices.append(vector(point))
		for point in record.uv:
			uv.append(vector(point))
		mesh.polygon = vertices
		mesh.uv = uv
		var triangles: Array = []
		for triangle in record.triangles:
			triangles.append(PackedInt32Array(triangle))
		mesh.polygons = triangles
		mesh.texture = load(part_files[name])
		mesh.skeleton = NodePath("../Skeleton2D")
		mesh.add_bone(NodePath(data.bones[record.stationary_bone].path), PackedFloat32Array(record.stationary_weights))
		mesh.add_bone(NodePath(data.bones[record.moving_bone].path), PackedFloat32Array(record.moving_weights))
		if record.has("additional_bone"):
			assert(record.additional_bone in data.bones, "Invalid additional skinning bone: " + name)
			assert(record.additional_weights.size() == record.vertices.size(), "Additional skinning weight count mismatch: " + name)
			mesh.add_bone(NodePath(data.bones[record.additional_bone].path), PackedFloat32Array(record.additional_weights))
		set_order(mesh, name, data.draw_order)
		visual.add_child(mesh)
		var original := unit.find_child("Art_" + name, true, false) as Sprite2D
		assert(original != null, "Missing original sprite for local binding: " + name)
		original.visible = false
	var player := AnimationPlayer.new()
	player.name = "AnimationPlayer"
	player.callback_mode_method = AnimationMixer.ANIMATION_CALLBACK_MODE_METHOD_IMMEDIATE
	unit.add_child(player)
	var relay := Node.new()
	relay.name = "RigEventRelay"
	relay.set_script(load("res://scripts/rig/cretan_archer_event_relay.gd"))
	unit.add_child(relay)
	var marker := Marker2D.new()
	marker.name = "GroundMarker"
	unit.add_child(marker)
	var debug := Node2D.new()
	debug.name = "DebugRoot"
	debug.set_script(load("res://scripts/rig/rig_debug.gd"))
	debug.visible = false
	unit.add_child(debug)
	var library := AnimationLibrary.new()
	var total_events := 0
	for animation_name in animations:
		var entry: Dictionary = animations[animation_name]
		var anim := Animation.new()
		anim.resource_name = animation_name
		anim.length = float(entry.length)
		anim.loop_mode = Animation.LOOP_LINEAR if entry.loop else Animation.LOOP_NONE
		var times: Array = entry.times
		for bone_name in data.bones:
			if bone_name == "arrow_socket":
				continue
			var values: Array = []
			for pose in entry.poses:
				values.append(deg_to_rad(float(pose.rotations[bone_name])))
			value_track(anim, "VisualRoot/Skeleton2D/" + data.bones[bone_name].path + ":rotation", times, values)
		var pelvis_positions: Array = []
		var visual_positions: Array = []
		var visual_rotations: Array = []
		var string_points: Array = []
		var bow_positions: Array = []
		var arrow_visibility: Array = []
		var arrow_rotations: Array = []
		for pose in entry.poses:
			pelvis_positions.append(vector(data.bones.pelvis.local_position) + vector(pose.pelvis_offset))
			visual_positions.append(vector(pose.visual_offset))
			visual_rotations.append(deg_to_rad(float(pose.visual_rotation)))
			string_points.append(vector(pose.bow_draw_point))
			bow_positions.append(vector(data.bones.bow_socket.local_position) + vector(pose.get("bow_offset", [0.0, 0.0])))
			arrow_visibility.append(bool(pose.arrow_visible))
			arrow_rotations.append(deg_to_rad(float(pose.arrow_rotation)))
		value_track(anim, "VisualRoot/Skeleton2D/" + data.bones.pelvis.path + ":position", times, pelvis_positions)
		value_track(anim, "VisualRoot:position", times, visual_positions)
		value_track(anim, "VisualRoot:rotation", times, visual_rotations)
		for side in ["near", "far"]:
			var hip_positions: Array = []
			var shoulder_positions: Array = []
			var hip_name: String = "leg_" + side + "_thigh"
			var shoulder_name: String = "arm_" + side + "_upper"
			for pose in entry.poses:
				hip_positions.append(vector(data.bones[hip_name].local_position) + vector(pose.hip_offsets[side]))
				var offsets: Dictionary = pose.get("shoulder_offsets", {})
				shoulder_positions.append(vector(data.bones[shoulder_name].local_position) + vector(offsets.get(side, [0.0, 0.0])))
			value_track(anim, "VisualRoot/Skeleton2D/" + data.bones[hip_name].path + ":position", times, hip_positions)
			value_track(anim, "VisualRoot/Skeleton2D/" + data.bones[shoulder_name].path + ":position", times, shoulder_positions)
		var bow_path: String = "VisualRoot/Skeleton2D/" + data.bones.bow_socket.path
		var arrow_path: String = "VisualRoot/Skeleton2D/" + data.bones.arrow_socket.path
		value_track(anim, bow_path + ":position", times, bow_positions)
		value_track(anim, bow_path + "/Art_bow_string:draw_point", times, string_points)
		value_track(anim, arrow_path + ":position", times, string_points)
		value_track(anim, arrow_path + ":rotation", times, arrow_rotations)
		value_track(anim, arrow_path + "/Art_arrow_single:visible", times, arrow_visibility, true)
		if entry.has("method_events"):
			var index := anim.add_track(Animation.TYPE_METHOD)
			anim.track_set_path(index, NodePath("RigEventRelay"))
			for event in entry.method_events:
				assert(animation_name == "attack_01" and str(event.method) == "_event_attack_release", "Unexpected Archer event")
				anim.track_insert_key(index, float(event.time), {"method": event.method, "args": []})
				total_events += 1
		library.add_animation(animation_name, anim)
	assert(total_events == 1, "Exactly one attack_release method key required")
	assert(ResourceSaver.save(library, OUTPUT_LIBRARY) == OK)
	player.add_animation_library("", library)
	own_tree(unit, unit)
	unit.set("autoplay", true)
	var packed := PackedScene.new()
	assert(packed.pack(unit) == OK)
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT_SCENE.get_base_dir()))
	assert(ResourceSaver.save(packed, OUTPUT_SCENE) == OK)
	print("BUILT_ARCHER_NATIVE bones=", data.bones.size(), " parts=20 native_meshes=8 animations=5 attack_release_keys=", total_events)
	unit.free()
	quit()
