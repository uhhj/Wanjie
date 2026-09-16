extends Node2D
const SCENE := "res://scenes/units/odyssey/minotaur_breaker/minotaur_breaker_rig.tscn"
var units: Array = []
var label: Label
var count := 20
var mode := "walk"
var automated := false
func _ready() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--units="):count=int(argument.trim_prefix("--units="))
		if argument.begins_with("--mode="):mode=argument.trim_prefix("--mode=")
		automated = automated or argument == "--measure"
	if DisplayServer.get_name()=="headless":
		push_error("Real desktop renderer required for FPS")
		get_tree().quit(2)
		return
	DisplayServer.window_set_size(Vector2i(1920,1080))
	get_tree().root.content_scale_size=Vector2i(1920,1080)
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	Engine.max_fps=0
	RenderingServer.set_default_clear_color(Color(.80,.82,.81))
	var layer:=CanvasLayer.new()
	add_child(layer)
	label=Label.new()
	label.position=Vector2(20,15)
	label.add_theme_color_override("font_color",Color.BLACK)
	label.add_theme_font_size_override("font_size",22)
	layer.add_child(label)
	var menu:=HBoxContainer.new()
	menu.position=Vector2(20,50)
	layer.add_child(menu)
	var amounts:=OptionButton.new()
	for n in [1,10,20,30,50]:amounts.add_item(str(n))
	amounts.select([1,10,20,30,50].find(count))
	amounts.item_selected.connect(func(i):count=[1,10,20,30,50][i];populate())
	menu.add_child(amounts)
	var modes:=OptionButton.new()
	for n in ["idle","walk","attack_loop","skill_loop","hit_loop","death_once"]:modes.add_item(n)
	modes.select(["idle","walk","attack_loop","skill_loop","hit_loop","death_once"].find(mode))
	modes.item_selected.connect(func(i):mode=modes.get_item_text(i);populate())
	menu.add_child(modes)
	populate()
	if automated:measure()
func populate() -> void:
	for unit in units:unit.queue_free()
	units.clear()
	var packed:PackedScene=load(SCENE)
	var rng:=RandomNumberGenerator.new()
	rng.seed=74204
	var columns:=5 if count<=20 else 10
	var animation:String={"attack_loop":"attack_01","skill_loop":"skill_01","hit_loop":"hit","death_once":"death"}.get(mode,mode)
	for i in count:
		var unit=packed.instantiate()
		unit.autoplay=false
		unit.root_motion_enabled=mode in ["walk","skill_loop"]
		unit.scale=Vector2.ONE*288./1435.
		unit.position=Vector2(140+(i%columns)*(1700./columns),350+(i/columns)*(180. if count>20 else 230.))
		# Reserve a complete draw-order range per row, so limbs do not interleave units.
		unit.z_index=(i/columns)*64
		add_child(unit)
		if mode.ends_with("_loop"):
			unit.animation_player.animation_finished.connect(func(name):
				if str(name)==animation:unit.call_deferred("play_animation",animation))
		unit.play_animation(animation)
		unit.animation_player.advance(rng.randf()*unit.animation_player.current_animation_length*.9)
		unit.previous_root_distance=unit.root_distance
		unit.previous_time=unit.animation_player.current_animation_position
		units.append(unit)
func _process(_delta:float) -> void:
	if label!=null:label.text="MINOTAUR V1 | %s | Units %d | FPS %d | Nodes %d"%[mode,count,Engine.get_frames_per_second(),get_tree().get_node_count()]
	for unit in units:
		if unit.position.x>1850:unit.position.x=70
func measure() -> void:
	await get_tree().create_timer(2).timeout
	var begin:=Time.get_ticks_usec()
	var first:=Engine.get_frames_drawn()
	await get_tree().create_timer(8).timeout
	var elapsed:float=(Time.get_ticks_usec()-begin)/1000000.
	var fps:float=(Engine.get_frames_drawn()-first)/elapsed
	await RenderingServer.frame_post_draw
	var folder:="res://reports/minotaur_breaker/stress"
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(folder))
	var stem:="%s/%d_%s"%[folder,count,mode]
	get_viewport().get_texture().get_image().save_png(stem+".png")
	var report:={"status":"DESKTOP_FORMAL_MEASURED","units":count,"mode":mode,"fps":fps,"seconds":elapsed,"viewport":[1920,1080],"display_height":288,"renderer":RenderingServer.get_video_adapter_name(),"godot":Engine.get_version_info().string,"scene_sha256":FileAccess.get_sha256(SCENE),"node_count":get_tree().get_node_count(),"occlusion_review":"PENDING","mobile_performance_claim":false}
	var f:=FileAccess.open(stem+".json",FileAccess.WRITE)
	f.store_string(JSON.stringify(report,"  ")+"\n")
	print("MINOTAUR_STRESS ",JSON.stringify(report))
	get_tree().quit()
