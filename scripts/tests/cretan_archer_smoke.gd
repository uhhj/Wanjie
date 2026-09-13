extends SceneTree

const SCENE := "res://scenes/units/odyssey/cretan_archer/cretan_archer_rig.tscn"
const FOLDER := "res://reports/cretan_archer/native"
var units: Array = []
var release_events := [0]

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var inputs_at_start := artifact_inputs()
	if DisplayServer.get_name() == "headless":
		push_error("Desktop smoke requires real rendering; headless FPS is not a measurement")
		quit(2)
		return
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(FOLDER))
	DisplayServer.window_set_size(Vector2i(1920, 1080))
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	Engine.max_fps = 0
	root.content_scale_size = Vector2i(1920, 1080)
	var mode := "walk"
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--mode="):
			mode = argument.trim_prefix("--mode=")
	if mode not in ["idle", "walk", "attack_loop", "hit_loop", "death_once"]:
		push_error("Unsupported smoke mode: " + mode)
		quit(2)
		return
	var animation: String = {"attack_loop":"attack_01", "hit_loop":"hit", "death_once":"death"}.get(mode, mode)
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://resources/cretan_archer_rig_v1.json"))
	var stage := Node2D.new()
	root.add_child(stage)
	var background := ColorRect.new()
	background.color = Color(0.88, 0.89, 0.87)
	background.size = Vector2(1920, 1080)
	stage.add_child(background)
	var label := Label.new()
	label.position = Vector2(20, 12)
	label.add_theme_color_override("font_color", Color(0.08, 0.09, 0.08))
	label.add_theme_font_size_override("font_size", 22)
	stage.add_child(label)
	var rng := RandomNumberGenerator.new()
	rng.seed = 74202
	for i in range(20):
		var unit = load(SCENE).instantiate()
		unit.autoplay = false
		unit.root_motion_enabled = mode == "walk"
		unit.position = Vector2(170 + (i % 5) * 340, 270 + (i / 5) * 235)
		unit.scale = Vector2.ONE * 192.0 / float(data.body_height)
		stage.add_child(unit)
		unit.attack_release.connect(func(): release_events[0] += 1)
		if mode in ["attack_loop", "hit_loop"]:
			unit.animation_player.animation_finished.connect(func(name):
				if str(name) == animation:
					unit.call_deferred("play_animation", animation))
		unit.play_animation(animation)
		# Start at a random phase without introducing an initial root-motion jump.
		var phase: float = rng.randf() * unit.animation_player.current_animation_length
		unit.animation_player.advance(phase)
		units.append(unit)
	await process_frame
	await RenderingServer.frame_post_draw
	var warmup_end := Time.get_ticks_usec() + 2000000
	while Time.get_ticks_usec() < warmup_end:
		update_units(label, mode)
		await process_frame
	var start := Time.get_ticks_usec()
	var first_frame := Engine.get_frames_drawn()
	var sample_start := start
	var sample_first_frame := first_frame
	var samples: Array = []
	var captured := false
	while (Time.get_ticks_usec() - start) < 20000000:
		update_units(label, mode)
		await process_frame
		var now := Time.get_ticks_usec()
		if now - sample_start >= 1000000:
			var elapsed := (now - sample_start) / 1000000.0
			var drawn := Engine.get_frames_drawn() - sample_first_frame
			samples.append({"time_seconds":(now - start) / 1000000.0, "elapsed_seconds":elapsed, "rendered_frames":drawn, "fps":drawn / elapsed, "node_count":get_node_count(), "draw_calls":Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)})
			sample_start = now
			sample_first_frame = Engine.get_frames_drawn()
		if not captured and now - start > 10000000:
			await RenderingServer.frame_post_draw
			root.get_texture().get_image().save_png(FOLDER + "/smoke_20_" + mode + ".png")
			captured = true
	var seconds := (Time.get_ticks_usec() - start) / 1000000.0
	var frames := Engine.get_frames_drawn() - first_frame
	var viewport := root.get_visible_rect().size
	var complete := frames > 0 and seconds >= 20.0 and units.size() == 20 and viewport == Vector2(1920, 1080)
	var report := {"status":"COMPLETED" if complete else "FAIL", "engine":Engine.get_version_info(), "renderer":RenderingServer.get_video_adapter_name(), "display_server":DisplayServer.get_name(), "desktop_only":true, "mobile_performance_claimed":false, "units":20, "mode":mode, "unit_height_px":192, "viewport":[viewport.x, viewport.y], "warmup_seconds":2.0, "measured_seconds":seconds, "rendered_frames":frames, "fps":frames / seconds, "vsync":false, "node_count":get_node_count(), "observed_attack_release_events":release_events[0], "samples":samples, "walk_spatial_wrap":"Benchmark only: units wrap after leaving the right viewport boundary; foot validation is tested separately without wraps."}
	report["artifact_inputs"] = inputs_at_start
	report["inputs_unchanged_during_smoke"] = inputs_at_start == artifact_inputs()
	if not report.inputs_unchanged_during_smoke:
		complete = false
		report["status"] = "FAIL_INPUTS_CHANGED_DURING_SMOKE"
	var file := FileAccess.open(FOLDER + "/smoke_20_" + mode + ".json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "\t"))
	print("CRETAN_SMOKE ", JSON.stringify({"status":report.status, "units":20, "mode":mode, "fps":report.fps, "seconds":seconds}))
	quit(0 if complete else 2)

func artifact_inputs() -> Dictionary:
	var hashes: Dictionary = {}
	for path in [SCENE, "res://resources/cretan_archer_animations_v1.tres", "res://resources/cretan_archer_animations_v1.json", "res://resources/cretan_archer_rig_v1.json", "res://resources/cretan_archer_local_skinning.json", "res://scripts/rig/cretan_archer_rig.gd", "res://scripts/rig/cretan_archer_bow_string.gd", "res://scripts/rig/cretan_archer_event_relay.gd", "res://tools/cretan_archer_parts_manifest.json"]:
		if FileAccess.file_exists(path):
			hashes[path] = FileAccess.get_sha256(path)
	var part_directory := "res://assets/units/odyssey/cretan_archer/parts"
	for filename in DirAccess.get_files_at(part_directory):
		if filename.get_extension().to_lower() == "png":
			var path := part_directory.path_join(filename)
			hashes[path] = FileAccess.get_sha256(path)
	return hashes

func update_units(label: Label, mode: String) -> void:
	for unit in units:
		if unit.position.x > 1770.0:
			unit.position.x -= 1660.0
	label.text = "CRETAN ARCHER | 20 units | %s | FPS %.1f | Nodes %d | Desktop baseline" % [mode, Engine.get_frames_per_second(), get_node_count()]
