extends SceneTree
const SCENE := "res://work/minotaur_breaker/candidates/minotaur_breaker_candidate.tscn"
const FOLDER := "res://reports/minotaur_breaker/actions_v2/frames"
const NAMES := ["attack_01","skill_01"]
func inputs() -> Dictionary:
	var result:Dictionary={}
	for file in [SCENE,"res://scripts/rig/minotaur_breaker_rig.gd","res://scripts/rig/minotaur_event_relay.gd","res://resources/minotaur_breaker_animation_candidates.json","res://resources/minotaur_breaker_rig_v1.json","res://resources/minotaur_breaker_skinning_candidates.json","res://work/minotaur_breaker/candidates/manifest.json"]:
		result[file]=FileAccess.get_sha256(file)
	return result
func _initialize() -> void:call_deferred("run")
func run() -> void:
	if DisplayServer.get_name() == "headless":
		push_error("Real GPU capture required")
		quit(2)
		return
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(FOLDER))
	var initial_inputs:=inputs()
	var packed: PackedScene = load(SCENE)
	var views: Array = []
	var units: Array = []
	var heights := [360,288]
	var names := NAMES.duplicate()
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--height="):heights=[int(argument.trim_prefix("--height="))]
		if argument.begins_with("--only="):names=[argument.trim_prefix("--only=")]
	for height in heights:
		var view := SubViewport.new()
		view.size = Vector2i(1440,560)
		view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		root.add_child(view)
		var bg := ColorRect.new()
		bg.size = Vector2(1440,560)
		bg.color = Color(.85,.86,.87)
		view.add_child(bg)
		var ground := Line2D.new()
		ground.points = PackedVector2Array([Vector2(20,475),Vector2(1420,475)])
		ground.width = 1
		ground.default_color = Color(.5,.5,.5)
		view.add_child(ground)
		var unit = packed.instantiate()
		unit.autoplay = false
		unit.root_motion_enabled = false
		unit.scale = Vector2.ONE*float(height)/1435.
		unit.position = Vector2(260,475)
		view.add_child(unit)
		unit.set_process(false)
		unit.animation_player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
		views.append(view)
		units.append(unit)
	var frames: Array = []
	var events: Dictionary = {}
	for name in names:
		var length: float = units[0].animation_player.get_animation(name).length
		for i in 32:
			var t := length*i/31.0
			for unit in units:
				unit.play_animation(name)
				unit.animation_player.seek(t,true)
				unit.position = Vector2(260+unit.root_distance*unit.scale.x,475)
			await process_frame
			await RenderingServer.frame_post_draw
			for j in heights.size():
				var path := "%s/%s_%d_%02d.png"%[FOLDER,name,heights[j],i]
				assert(views[j].get_texture().get_image().save_png(path)==OK)
				frames.append({"animation":name,"height":heights[j],"frame":i,"time":t,"path":path,"sha256":FileAccess.get_sha256(path)})
		print("CAPTURED_MINOTAUR ",name)
	# Test method tracks by advancing continuously; screenshot seek does not test events.
	for name in ["attack_01","skill_01"]:
		var counter := [0,0]
		var unit = units[0]
		var attack_callback := func():counter[0]+=1
		var skill_callback := func():counter[1]+=1
		unit.attack_hit.connect(attack_callback)
		unit.skill_hit.connect(skill_callback)
		unit.play_animation(name)
		var length: float = unit.animation_player.get_animation(name).length
		for i in 120:unit.animation_player.advance(length/120.)
		events[name] = counter.duplicate()
		unit.attack_hit.disconnect(attack_callback)
		unit.skill_hit.disconnect(skill_callback)
	var prior_path:="res://reports/minotaur_breaker/actions_v2_capture_manifest.json"
	if FileAccess.file_exists(prior_path):
		var prior:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(prior_path))
		if prior.get("artifact_inputs",{})==initial_inputs:
			for row in prior.frames:
				if int(row.height) not in heights or str(row.animation) not in names:frames.append(row)
	var report := {"status":"CAPTURED_NOT_VISUALLY_APPROVED","engine":Engine.get_version_info().string,"renderer":RenderingServer.get_video_adapter_name(),"scene_sha256":FileAccess.get_sha256(SCENE),"frames":frames,"events_attack_skill":events,"source":"Actual Godot GPU SubViewport frames; heights may be captured sequentially to limit memory"}
	report["artifact_inputs"]=initial_inputs
	report["inputs_unchanged_during_capture"]=initial_inputs==inputs()
	if initial_inputs!=inputs():report.status="FAIL_INPUTS_CHANGED_DURING_CAPTURE"
	var f := FileAccess.open("res://reports/minotaur_breaker/actions_v2_capture_manifest.json",FileAccess.WRITE)
	f.store_string(JSON.stringify(report,"  ")+"\n")
	print("MINOTAUR_EVENTS ",events)
	quit()

