extends SceneTree

const SCENE := "res://scenes/units/odyssey/cretan_archer/cretan_archer_rig.tscn"
const FOLDER := "res://reports/cretan_archer/animations"
const VIEW_SIZE := Vector2i(800, 560)
const FLOOR_Y := 470.0
const ROOT_X := 350.0
const NAMES := ["idle", "walk", "attack_01", "hit", "death"]

func _initialize() -> void:
	call_deferred("lab_startup_smoke" if "--lab-startup" in OS.get_cmdline_user_args() else "capture")

func lab_startup_smoke() -> void:
	if DisplayServer.get_name() == "headless":
		push_error("Rig Lab smoke requires real GPU rendering")
		quit(2)
		return
	var lab_scene := "res://scenes/tests/cretan_archer_rig_lab.tscn"
	var lab_script := "res://scripts/tests/cretan_archer_rig_lab.gd"
	var inputs := artifact_inputs()
	inputs[lab_scene] = FileAccess.get_sha256(lab_scene)
	inputs[lab_script] = FileAccess.get_sha256(lab_script)
	DisplayServer.window_set_size(Vector2i(1280, 720))
	root.content_scale_size = Vector2i(1280, 720)
	var lab = load(lab_scene).instantiate()
	root.add_child(lab)
	await process_frame
	var errors: Array = []
	if lab.unit == null:
		errors.append("Lab did not instantiate Archer unit")
	if lab.animation_picker.item_count != 5 or lab.speed_picker.item_count != 3 or lab.scale_picker.item_count != 2:
		errors.append("Lab dropdown choices missing")
	for name in ["PlayButton", "PauseButton", "RestartButton", "RuntimeStatus"]:
		if lab.find_child(name, true, false) == null:
			errors.append("Missing UI control: " + name)
	var event_count := [0]
	if lab.unit != null:
		lab.unit.attack_release.connect(func(): event_count[0] += 1)
		lab._pause()
		var paused_time: float = lab.unit.animation_player.current_animation_position
		var paused_root: Vector2 = lab.unit.position
		for frame in range(6):
			await process_frame
		if lab.unit.animation_player.is_playing() or absf(lab.unit.animation_player.current_animation_position - paused_time) > 0.0001 or lab.unit.position.distance_to(paused_root) > 0.0001:
			errors.append("Lab Pause did not hold playback/root position")
		lab._play()
		if not lab.unit.animation_player.is_playing():
			errors.append("Lab Play did not resume")
		lab.speed_picker.select(2)
		lab._change_speed(2)
		if lab.unit.animation_player.speed_scale != 2.0:
			errors.append("Lab speed selector did not apply 2x")
		lab.speed_picker.select(1)
		lab._change_speed(1)
		lab.scale_picker.select(1)
		lab._change_scale(1)
		if absf(lab.unit.scale.x * lab.body_height - 192.0) > 0.01:
			errors.append("Lab scale selector did not apply 192px")
		lab.scale_picker.select(0)
		lab._change_scale(0)
		lab.animation_picker.select(2)
		lab._restart()
		var deadline := Time.get_ticks_msec() + 3500
		while Time.get_ticks_msec() < deadline:
			await process_frame
			if event_count[0] > 0 and str(lab.unit.animation_player.assigned_animation) == "idle":
				break
		if event_count[0] != 1 or lab.unit.attack_release_count != 1:
			errors.append("Lab attack playback did not emit exactly one release")
		if str(lab.unit.animation_player.assigned_animation) != "idle":
			errors.append("Lab attack did not return to idle")
		for property in lab.debug_options:
			lab.debug_options[property].button_pressed = true
			if not lab.unit.get_node("DebugRoot").get(property):
				errors.append("Lab debug toggle not applied: " + property)
		if lab.unit.get_node("DebugRoot").z_index != 4095 or not lab.combat_ground_line.visible or lab.combat_ground_line.width < 1.0:
			errors.append("Lab debug overlay is obscured or ground line is subpixel")
	await process_frame
	await RenderingServer.frame_post_draw
	var folder := "res://reports/cretan_archer/native"
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(folder))
	var screenshot := folder + "/rig_lab_startup.png"
	root.get_texture().get_image().save_png(screenshot)
	var end_inputs := artifact_inputs()
	end_inputs[lab_scene] = FileAccess.get_sha256(lab_scene)
	end_inputs[lab_script] = FileAccess.get_sha256(lab_script)
	if inputs != end_inputs:
		errors.append("Lab inputs changed during smoke")
	var report := {"status":"PASS" if errors.is_empty() else "FAIL", "engine":Engine.get_version_info(), "renderer":RenderingServer.get_video_adapter_name(), "display_server":DisplayServer.get_name(), "viewport":[1280, 720], "dropdown_animation_count":lab.animation_picker.item_count, "attack_release_observed":event_count[0], "checks":["startup", "all UI controls", "pause holds playback and root", "play resumes", "2x speed", "192px scale", "restart attack exactly one release then idle", "all debug toggles"], "screenshot":screenshot, "screenshot_sha256":FileAccess.get_sha256(screenshot), "artifact_inputs":inputs, "inputs_unchanged_during_smoke":inputs == end_inputs, "errors":errors}
	var file := FileAccess.open(folder + "/rig_lab_startup.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "\t"))
	print("CRETAN_RIG_LAB_SMOKE ", report.status)
	lab.free()
	quit(0 if errors.is_empty() else 2)

func capture() -> void:
	if DisplayServer.get_name() == "headless":
		push_error("Capture requires real GPU rendering; do not run --headless")
		quit(2)
		return
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(FOLDER))
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://reports/cretan_archer/native"))
	var inputs_at_start := artifact_inputs()
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://resources/cretan_archer_rig_v1.json"))
	var heights := [256, 192]
	var viewports: Array = []
	var units: Array = []
	for height in heights:
		var viewport := SubViewport.new()
		viewport.size = VIEW_SIZE
		viewport.transparent_bg = true
		viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		root.add_child(viewport)
		var ground := Line2D.new()
		ground.points = PackedVector2Array([Vector2(24.0, FLOOR_Y + 1.0), Vector2(VIEW_SIZE.x - 24.0, FLOOR_Y + 1.0)])
		ground.width = 1.0
		ground.default_color = Color(0.50, 0.53, 0.55, 0.85)
		viewport.add_child(ground)
		var unit = load(SCENE).instantiate()
		unit.autoplay = false
		unit.root_motion_enabled = false
		unit.position = Vector2(ROOT_X, FLOOR_Y)
		unit.scale = Vector2.ONE * float(height) / float(data.body_height)
		viewport.add_child(unit)
		unit.set_process(false)
		unit.animation_player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
		var tick_spacing: float = unit.walk_stride * unit.scale.x / 2.0
		for tick in range(-8, 10):
			var x: float = ROOT_X + tick * tick_spacing
			if x <= 24.0 or x >= VIEW_SIZE.x - 24.0:
				continue
			var marker := Line2D.new()
			marker.points = PackedVector2Array([Vector2(x, FLOOR_Y + 2.0), Vector2(x, FLOOR_Y + 7.0)])
			marker.width = 1.0
			marker.default_color = Color(0.60, 0.63, 0.65, 0.85)
			viewport.add_child(marker)
		viewports.append(viewport)
		units.append(unit)
	await process_frame
	await RenderingServer.frame_post_draw
	var records: Array = []
	var clipping: Array = []
	var lengths: Dictionary = {}
	for name in ["rest_pose"] + NAMES:
		var length: float = 0.0 if name == "rest_pose" else units[0].animation_player.get_animation(name).length
		lengths[name] = length
		var count := 1 if name == "rest_pose" else 16
		for frame in range(count):
			var denominator := count if name in ["idle", "walk"] else maxi(1, count - 1)
			var time := length * frame / float(denominator)
			for unit in units:
				unit.position = Vector2(ROOT_X, FLOOR_Y)
				if name == "rest_pose":
					unit.rest_pose()
				else:
					unit.play_animation(name)
					unit.animation_player.seek(time, true)
				if name == "walk":
					unit.position.x += unit.walk_stride * (time / length) * unit.scale.x
			await process_frame
			await RenderingServer.frame_post_draw
			for index in range(heights.size()):
				var image: Image = viewports[index].get_texture().get_image()
				var bounds := image.get_used_rect()
				var clipped := bounds.position.x < 4 or bounds.position.y < 4 or bounds.end.x > VIEW_SIZE.x - 4 or bounds.end.y > VIEW_SIZE.y - 4
				var path := "%s/%s_%d_%03d.png" % [FOLDER, name, heights[index], frame]
				assert(image.save_png(path) == OK)
				var row := {"animation":name, "height":heights[index], "time":time, "frame":frame, "path":path, "sha256":FileAccess.get_sha256(path), "viewport":[VIEW_SIZE.x, VIEW_SIZE.y], "used_rect":[bounds.position.x, bounds.position.y, bounds.size.x, bounds.size.y], "clipped":clipped, "root_position":[units[index].position.x, units[index].position.y], "root_motion_source_px":units[index].walk_stride * time / length if name == "walk" else 0.0}
				records.append(row)
				if clipped:
					clipping.append(row)
		print("CRETAN_CAPTURED ", name, " ", count, " actual Godot frames per scale")
	var manifest := {"status":"PASS" if clipping.is_empty() else "FAIL_CLIPPED_CAPTURE", "engine":Engine.get_version_info(), "renderer":RenderingServer.get_video_adapter_name(), "display_server":DisplayServer.get_name(), "source":"Actual GPU SubViewport frames. Python may assemble reports, never synthesize motion.", "body_height_source":data.body_height, "viewport":[VIEW_SIZE.x, VIEW_SIZE.y], "floor_y":FLOOR_Y, "root_x":ROOT_X, "frames_per_animation_per_scale":16, "animation_lengths":lengths, "ground_landmarks":"Fixed world-space floor ticks; Walk root progresses across them, camera remains fixed", "clipped_frames":clipping, "frames":records}
	manifest["artifact_inputs"] = inputs_at_start
	var inputs_unchanged := inputs_at_start == artifact_inputs()
	manifest["inputs_unchanged_during_capture"] = inputs_unchanged
	if not inputs_unchanged:
		manifest["status"] = "FAIL_INPUTS_CHANGED_DURING_CAPTURE"
	var file := FileAccess.open("res://reports/cretan_archer/native/capture_manifest.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(manifest, "\t"))
	for viewport in viewports:
		viewport.free()
	quit(0 if clipping.is_empty() and inputs_unchanged else 2)

func artifact_inputs() -> Dictionary:
	var hashes: Dictionary = {}
	for path in [SCENE, "res://resources/cretan_archer_animations_v1.tres", "res://resources/cretan_archer_rig_v1.json", "res://resources/cretan_archer_animations_v1.json", "res://resources/cretan_archer_local_skinning.json", "res://scripts/rig/cretan_archer_rig.gd", "res://scripts/rig/cretan_archer_bow_string.gd", "res://scripts/rig/cretan_archer_event_relay.gd", "res://tools/cretan_archer_parts_manifest.json"]:
		if FileAccess.file_exists(path):
			hashes[path] = FileAccess.get_sha256(path)
	var part_directory := "res://assets/units/odyssey/cretan_archer/parts"
	for filename in DirAccess.get_files_at(part_directory):
		if filename.get_extension().to_lower() == "png":
			var path := part_directory.path_join(filename)
			hashes[path] = FileAccess.get_sha256(path)
	return hashes
