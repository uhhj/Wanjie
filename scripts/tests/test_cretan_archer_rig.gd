extends SceneTree

const SCENE := "res://scenes/units/odyssey/cretan_archer/cretan_archer_rig.tscn"
const RIG_DATA := "res://resources/cretan_archer_rig_v1.json"
const CONTACT_DATA := "res://resources/cretan_archer_walk_contacts.json"
const REPORT := "res://reports/cretan_archer/native/headless_tests.json"
const NAMES := ["idle", "walk", "attack_01", "hit", "death"]
var errors: Array = []
var inputs_at_start: Dictionary = {}

func check(condition: bool, message: String) -> void:
	if not condition:
		errors.append(message)
		push_error(message)

func _initialize() -> void:
	call_deferred("run")

func read_json(path: String) -> Variant:
	if not FileAccess.file_exists(path):
		check(false, "Missing required input: " + path)
		return null
	return JSON.parse_string(FileAccess.get_file_as_string(path))

func vec(value: Variant) -> Vector2:
	return Vector2(float(value[0]), float(value[1]))

func contact_rows(data: Variant) -> Array:
	if data is Array:
		return data
	if data is Dictionary:
		for key in ["samples", "records", "rows", "contacts"]:
			if data.get(key) is Array:
				return data[key]
	return []

func row_time(row: Dictionary, length: float) -> float:
	return float(row.get("time", float(row.get("phase", 0.0)) * length))

func bone(unit: Node, data: Dictionary, name: String) -> Bone2D:
	return unit.get_node_or_null("VisualRoot/Skeleton2D/" + str(data.bones[name].path)) as Bone2D

func segment_id(row: Dictionary) -> String:
	# A support interval is never reset for every sample. A fixed material point
	# keeps one anchor until an actual contact-region/support transition occurs.
	var point := vec(row.contact_local)
	return str(row.get("support_id", "")) + ":" + str(row.get("contact_id", "")) + ":" + ("%.3f,%.3f" % [point.x, point.y])

func samples_for_side(rows: Array, side: String, length: float) -> Array:
	var selected: Array = []
	for row in rows:
		if row is Dictionary and str(row.get("side", "")) == side:
			selected.append(row)
	selected.sort_custom(func(a, b): return row_time(a, length) < row_time(b, length))
	return selected

func run() -> void:
	inputs_at_start = artifact_inputs()
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://reports/cretan_archer/native"))
	var version := Engine.get_version_info()
	check(version.major == 4 and version.minor == 7 and version.patch == 2 and version.status == "stable", "Godot 4.7.2 Stable required")
	var data_value = read_json(RIG_DATA)
	if not data_value is Dictionary or not ResourceLoader.exists(SCENE):
		check(false, "Archer scene and rig data must exist before validation")
		write_report({"status":"FAIL", "errors":errors, "engine":version})
		quit(2)
		return
	var data: Dictionary = data_value
	var unit = load(SCENE).instantiate()
	unit.autoplay = false
	unit.root_motion_enabled = false
	root.add_child(unit)
	await process_frame
	unit.set_process(false)
	var player: AnimationPlayer = unit.animation_player
	player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	player.callback_mode_method = AnimationMixer.ANIMATION_CALLBACK_MODE_METHOD_IMMEDIATE
	check(unit.find_children("*", "Skeleton2D", true, false).size() == 1, "One native Skeleton2D required")
	var bones: Array = unit.find_children("*", "Bone2D", true, false)
	check(bones.size() == 26, "Expected shared 23 bones plus bow/arrow/quiver sockets")
	for name in data.bones:
		check(bone(unit, data, name) != null, "Missing Bone2D NodePath: " + str(name))
	for name in NAMES:
		check(player.has_animation(name), "Missing animation " + name)
	check(player.get_animation_list().size() == 5, "Exactly five Archer animations required")
	var texture_count := 0
	for art in unit.find_children("*", "Sprite2D", true, false):
		if art.texture == null:
			check(false, "Missing texture on " + str(art.name))
			continue
		texture_count += 1
		var image: Image = art.texture.get_image()
		check(image != null and not image.is_empty(), "Unreadable texture " + str(art.name))
		if image == null or image.is_empty():
			continue
		if image.is_compressed():
			check(image.decompress() == OK, "Cannot decompress texture for alpha validation")
		check(image.get_width() == 1024 and image.get_height() == 1536, "Same-canvas texture required: " + str(art.name))
		check(image.detect_alpha() != Image.ALPHA_NONE, "Real alpha required: " + str(art.name))
		check(image.get_used_rect().has_area(), "Empty part texture: " + str(art.name))
		check(image.get_pixel(0, 0).a == 0.0, "Opaque canvas background on " + str(art.name))
	check(texture_count == 19, "Expected 19 textured Sprite2D nodes plus native bow string")
	var polygons: Array = unit.find_children("*", "Polygon2D", true, false)
	check(polygons.size() == 8, "Expected eight native weighted joint meshes")
	for art in polygons:
		check(art.texture != null, "Weighted mesh texture missing: " + str(art.name))
		check(art.get_bone_count() >= 2, "Joint mesh must reference actual native bones: " + str(art.name))
		var skeleton: Skeleton2D = art.get_node_or_null(art.skeleton) as Skeleton2D
		check(skeleton != null, "Invalid Polygon2D Skeleton2D path: " + str(art.name))
		var sums := PackedFloat32Array()
		sums.resize(art.polygon.size())
		sums.fill(0.0)
		for index in range(art.get_bone_count()):
			var weights: PackedFloat32Array = art.get_bone_weights(index)
			check(weights.size() == sums.size(), "Vertex/weight count mismatch")
			if skeleton != null:
				check(skeleton.get_node_or_null(art.get_bone_path(index)) is Bone2D, "Joint mesh has invalid bone path")
			for vertex in range(mini(weights.size(), sums.size())):
				sums[vertex] += weights[vertex]
		for total in sums:
			check(absf(total - 1.0) < 0.001, "Joint mesh weights do not sum to one")
	var track_count := 0
	var method_key_count := 0
	var release_time := -1.0
	for name in player.get_animation_list():
		var animation: Animation = player.get_animation(name)
		check((animation.loop_mode != Animation.LOOP_NONE) == (str(name) in ["idle", "walk"]), "Animation loop mismatch: " + str(name))
		for i in range(animation.get_track_count()):
			track_count += 1
			var path: NodePath = animation.track_get_path(i)
			var target: Node = unit.get_node_or_null(NodePath(path.get_concatenated_names()))
			check(target != null, "Invalid animation NodePath " + str(path))
			if animation.track_get_type(i) == Animation.TYPE_METHOD:
				for key in range(animation.track_get_key_count(i)):
					method_key_count += 1
					var event: Dictionary = animation.track_get_key_value(i, key)
					check(str(name) == "attack_01" and "attack_release" in str(event.method), "Unexpected method event")
					if target != null:
						check(target.has_method(str(event.method)), "Missing event relay method")
					release_time = animation.track_get_key_time(i, key)
	check(method_key_count == 1, "Exactly one attack_release method key required")
	if not errors.is_empty():
		write_report({"status":"FAIL", "stage":"resource_and_structure_checks", "engine":version, "errors":errors})
		unit.free()
		quit(2)
		return
	var observed_events := [0]
	check(unit.has_signal("attack_release"), "Root attack_release signal missing")
	if unit.has_signal("attack_release"):
		unit.attack_release.connect(func(): observed_events[0] += 1)
	unit.rest_pose()
	var origin := vec(data.origin)
	for sprite in unit.find_children("*", "Sprite2D", true, false):
		if sprite.name == &"Art_arrow_single":
			check(sprite.to_global(Vector2(282, 725)).distance_to(bone(unit, data, "arrow_socket").global_position) < 0.02, "Arrow nock does not match arrow_socket")
		else:
			check(sprite.global_position.distance_to(-origin) < 0.02, "Rest sprite canvas offset differs: " + str(sprite.name))
	var attack_length: float = player.get_animation("attack_01").length
	var animation_data: Dictionary = read_json("res://resources/cretan_archer_animations_v1.json")
	var nock_time: float = animation_data.attack_01.get("nock_time", 0.0)
	var bow: Sprite2D = unit.find_child("Art_bow", true, false) as Sprite2D
	var arrow: Sprite2D = unit.find_child("Art_arrow_single", true, false) as Sprite2D
	var bow_string: Line2D = unit.find_child("Art_bow_string", true, false) as Line2D
	check(bow != null and arrow != null and bow_string != null, "Bow, controllable string and arrow art nodes required")
	var bow_drift := 0.0
	var nock_drift := 0.0
	var string_nock_drift := 0.0
	var nocked_samples := 0
	unit.play_animation("attack_01")
	for step in range(121):
		var sample_time := attack_length * step / 120.0
		player.seek(sample_time, true)
		bow_drift = maxf(bow_drift, bow.to_global(Vector2(844, 725)).distance_to(bone(unit, data, "bow_socket").global_position))
		nock_drift = maxf(nock_drift, arrow.to_global(Vector2(282, 725)).distance_to(bone(unit, data, "arrow_socket").global_position))
		check(bow_string.points.size() == 3, "Bow string must contain top, nock and bottom control points")
		if bow_string.points.size() == 3 and sample_time >= nock_time and sample_time < release_time:
			string_nock_drift = maxf(string_nock_drift, bow_string.to_global(bow_string.points[1]).distance_to(bone(unit, data, "arrow_socket").global_position))
			nocked_samples += 1
	check(bow_drift < 0.02, "Bow disconnected from grip")
	check(nock_drift < 0.02 and string_nock_drift < 0.02, "Arrow nock disconnected from bow string")
	check(nocked_samples >= 3, "A measurable nocked/drawn interval before release is required")
	player.seek(maxf(0.0, release_time - 0.02), true)
	check(arrow.visible, "Nocked arrow must be visible before release")
	player.seek(minf(attack_length, release_time + 0.02), true)
	check(not arrow.visible, "Arrow must leave the held pose after release")
	observed_events[0] = 0
	unit.play_animation("attack_01")
	for _step in range(int(ceil((attack_length + 0.15) * 120.0))):
		player.advance(1.0 / 120.0)
	check(observed_events[0] == 1 and unit.attack_release_count == 1, "Attack must release exactly once per playback")
	check(player.current_animation == &"idle", "Attack must return to idle")
	unit.play_animation("attack_01")
	for _step in range(int(ceil((attack_length + 0.15) * 120.0))):
		player.advance(1.0 / 120.0)
	check(observed_events[0] == 2 and unit.attack_release_count == 1, "Repeated attack count must reset per playback, with one new release")
	unit.play_animation("hit")
	player.advance(player.get_animation("hit").length + 0.1)
	check(player.current_animation == &"idle", "Hit must return to idle")
	unit.play_animation("idle")
	unit.play_animation("walk")
	player.advance(0.1)
	unit.play_animation("idle")
	check(player.current_animation == &"idle", "idle/walk transitions failed")
	unit.play_animation("death")
	player.advance(player.get_animation("death").length + 0.1)
	check(player.assigned_animation == &"death" and not player.is_playing(), "Death must stop and hold")
	var foot_samples: Array = []
	var foot_metrics: Dictionary = {}
	var plan = read_json(CONTACT_DATA)
	var rows := contact_rows(plan)
	check(not rows.is_empty(), "Foot-contact plan must contain actual support/material-point samples")
	var walk_length: float = player.get_animation("walk").length
	var stride: float = unit.walk_stride
	unit.play_animation("walk")
	for side in ["near", "far"]:
		var side_rows := samples_for_side(rows, side, walk_length)
		var foot := bone(unit, data, "foot_" + side)
		var maximum := 0.0
		var expected_error := 0.0
		var floor_span := 0.0
		var sample_count := 0
		var interval_count := 0
		var anchor := Vector2.ZERO
		var previous_key := ""
		var current_key := ""
		var group_min_y := INF
		var group_max_y := -INF
		for i in range(maxi(0, side_rows.size() - 1)):
			var a: Dictionary = side_rows[i]
			var b: Dictionary = side_rows[i + 1]
			if not a.get("support", false) or not b.get("support", false) or not a.has("contact_local") or not b.has("contact_local"):
				previous_key = ""
				continue
			if segment_id(a) != segment_id(b):
				previous_key = ""
				continue
			current_key = segment_id(a)
			if previous_key != current_key:
				interval_count += 1
				group_min_y = INF
				group_max_y = -INF
			for sub in range(5):
				var t := lerpf(row_time(a, walk_length), row_time(b, walk_length), sub / 4.0)
				player.seek(t, true)
				unit.position.x = stride * t / walk_length
				var point := foot.to_global(vec(a.contact_local))
				var expected := vec(a.expected_world_contact).lerp(vec(b.expected_world_contact), sub / 4.0) if a.has("expected_world_contact") and b.has("expected_world_contact") else point
				expected_error = maxf(expected_error, point.distance_to(expected))
				if previous_key != current_key and sub == 0:
					anchor = point
				maximum = maxf(maximum, point.distance_to(anchor))
				group_min_y = minf(group_min_y, point.y)
				group_max_y = maxf(group_max_y, point.y)
				floor_span = maxf(floor_span, group_max_y - group_min_y)
				sample_count += 1
				foot_samples.append({"time":t, "side":side, "support":true, "support_interval":interval_count, "support_id":a.get("support_id", ""), "contact_id":a.get("contact_id", ""), "contact_local":a.contact_local, "world_position":[point.x, point.y], "anchor":[anchor.x, anchor.y], "expected_world_contact":[expected.x, expected.y], "expected_contact_error_source_px":point.distance_to(expected)})
			previous_key = current_key
		var at_256 := maximum * 256.0 / float(data.body_height)
		check(sample_count >= 20, "Insufficient stable material contact samples: " + side)
		check(at_256 < 1.0, "FAIL_WALK_FOOT_SLIDE: " + side)
		check(expected_error * 256.0 / float(data.body_height) < 1.0, "Contact differs from planned world anchor: " + side)
		check(floor_span * 256.0 / float(data.body_height) < 1.0, "Support foot leaves ground: " + side)
		foot_metrics[side] = {"source_pixels":maximum, "at_256px":at_256, "at_192px":maximum * 192.0 / float(data.body_height), "expected_contact_error_source_px":expected_error, "expected_contact_error_at_256px":expected_error * 256.0 / float(data.body_height), "floor_height_range_source_px":floor_span, "samples":sample_count, "support_intervals":interval_count}
	unit.position = Vector2.ZERO
	unit.root_motion_enabled = true
	unit.play_animation("walk")
	var runtime_contact_error := 0.0
	var runtime_contact_samples := 0
	for step in range(240):
		player.advance(walk_length / 120.0)
		unit._process(walk_length / 120.0)
		var actual_time := player.current_animation_position
		var cycle := int(floor((step + 1) / 120.0))
		if actual_time > walk_length - 0.00001:
			cycle = maxi(0, cycle - 1)
		for side in ["near", "far"]:
			var side_rows := samples_for_side(rows, side, walk_length)
			for i in range(maxi(0, side_rows.size() - 1)):
				var a: Dictionary = side_rows[i]
				var b: Dictionary = side_rows[i + 1]
				if actual_time < row_time(a, walk_length) or actual_time > row_time(b, walk_length):
					continue
				if a.get("support", false) and b.get("support", false) and segment_id(a) == segment_id(b) and a.has("expected_world_contact"):
					var ratio := inverse_lerp(row_time(a, walk_length), row_time(b, walk_length), actual_time)
					var expected := vec(a.expected_world_contact).lerp(vec(b.expected_world_contact), ratio) + Vector2(cycle * stride, 0.0)
					var point := bone(unit, data, "foot_" + side).to_global(vec(a.contact_local))
					runtime_contact_error = maxf(runtime_contact_error, point.distance_to(expected))
					runtime_contact_samples += 1
				break
	var runtime_distance: float = unit.position.x
	check(absf(runtime_distance - 2.0 * stride) < 0.02, "Root motion loses distance across two walk loops")
	check(runtime_contact_samples >= 120, "Insufficient runtime world contact samples")
	check(runtime_contact_error * 256.0 / float(data.body_height) < 1.0, "Runtime root-motion support point drifts from world target")
	player.pause()
	var paused_position: Vector2 = unit.position
	unit._process(0.5)
	check(unit.position == paused_position, "Paused walk must not translate")
	write_report({"status":"PASS" if errors.is_empty() else "FAIL", "engine":version, "errors":errors, "bone_count":bones.size(), "sprite_count":texture_count, "polygon_count":polygons.size(), "animation_tracks":track_count, "method_key_count":method_key_count, "attack_release_count":unit.attack_release_count, "observed_release_events_two_plays":observed_events[0], "attack_release_time":release_time, "nock_time":nock_time, "nocked_samples":nocked_samples, "bow_grip_drift_source_px":bow_drift, "arrow_nock_drift_source_px":nock_drift, "string_nock_drift_source_px":string_nock_drift, "foot_contact_method":"Fixed material foot point within each continuous support/contact region; actual Bone2D.to_global sampled between authored keys", "foot_slide":foot_metrics, "foot_samples":foot_samples, "runtime_walk_distance_two_cycles":runtime_distance, "runtime_expected_distance_two_cycles":stride * 2.0, "runtime_contact_samples":runtime_contact_samples, "runtime_contact_error_source_px":runtime_contact_error, "runtime_contact_error_at_256px":runtime_contact_error * 256.0 / float(data.body_height), "paused_root_motion_pass":unit.position == paused_position})
	unit.free()
	quit(0 if errors.is_empty() else 2)

func artifact_inputs() -> Dictionary:
	var hashes: Dictionary = {}
	for path in [SCENE, RIG_DATA, CONTACT_DATA, "res://resources/cretan_archer_animations_v1.json", "res://resources/cretan_archer_animations_v1.tres", "res://resources/cretan_archer_local_skinning.json", "res://scripts/rig/cretan_archer_rig.gd", "res://scripts/rig/cretan_archer_bow_string.gd", "res://scripts/rig/cretan_archer_event_relay.gd", "res://tools/cretan_archer_parts_manifest.json"]:
		if FileAccess.file_exists(path):
			hashes[path] = FileAccess.get_sha256(path)
	var part_directory := "res://assets/units/odyssey/cretan_archer/parts"
	for filename in DirAccess.get_files_at(part_directory):
		if filename.get_extension().to_lower() == "png":
			var path := part_directory.path_join(filename)
			hashes[path] = FileAccess.get_sha256(path)
	return hashes

func write_report(data: Dictionary) -> void:
	data["artifact_inputs"] = inputs_at_start
	data["inputs_unchanged_during_test"] = inputs_at_start == artifact_inputs()
	if not data.inputs_unchanged_during_test:
		check(false, "Native input changed while tests were running")
		data["status"] = "FAIL_INPUTS_CHANGED_DURING_TEST"
	var file := FileAccess.open(REPORT, FileAccess.WRITE)
	file.store_string(JSON.stringify(data, "\t"))
	print("CRETAN_ARCHER_TESTS ", data.get("status", "FAIL"))
