extends Node2D
const SCENE = preload("res://scenes/units/odyssey/roman_centurion/roman_centurion_rig.tscn")
const MODES = ["idle","walk","attack_01","hit","death","skill_command"]
var units: Array = []
var label: Label
var count := 20
var animation := "walk"
var random := RandomNumberGenerator.new()
func _ready() -> void:
	DisplayServer.window_set_size(Vector2i(1920,1080))
	get_viewport().content_scale_size = Vector2i(1920,1080)
	random.seed = 314159
	var layer := CanvasLayer.new()
	add_child(layer)
	var panel := VBoxContainer.new()
	panel.position = Vector2(12,12)
	layer.add_child(panel)
	label = Label.new()
	panel.add_child(label)
	var counts := OptionButton.new()
	for n in [1,10,20,30,50]: counts.add_item(str(n))
	counts.select(2)
	counts.item_selected.connect(func(i): count=[1,10,20,30,50][i]; populate())
	panel.add_child(counts)
	var modes := OptionButton.new()
	for n in MODES: modes.add_item(n)
	modes.select(1)
	modes.item_selected.connect(func(i): animation=MODES[i]; populate())
	panel.add_child(modes)
	populate()
	if "--benchmark" in OS.get_cmdline_user_args(): benchmark()
func populate() -> void:
	for unit in units: unit.free()
	units.clear()
	for i in count:
		var unit = SCENE.instantiate()
		unit.autoplay = false
		unit.root_motion_enabled = false
		unit.scale = Vector2.ONE*192.0/1425.0
		unit.position = Vector2(210+(i%10)*166,250+(i/10)*190)
		add_child(unit)
		unit.play_animation(animation)
		unit.animation_player.seek(random.randf()*unit.animation_player.get_animation(animation).length,true)
		if animation in ["attack_01","hit","skill_command"]:
			unit.animation_player.animation_finished.connect(func(_name): unit.play_animation(animation))
		units.append(unit)
func _process(_delta: float) -> void:
	label.text = "Centurion desktop baseline | %d units | %s | FPS %d | nodes %d" % [count,animation,Engine.get_frames_per_second(),get_tree().get_node_count()]
func benchmark() -> void:
	var records: Array = []
	for number in [20,50]:
		count = number
		for mode in ["idle","walk","attack_01","skill_command"]:
			animation = mode
			populate()
			await get_tree().create_timer(1.5).timeout
			var start := Time.get_ticks_usec()
			var frames := 0
			while Time.get_ticks_usec()-start<3000000:
				await get_tree().process_frame
				frames += 1
			var seconds := (Time.get_ticks_usec()-start)/1000000.0
			records.append({"units":count,"animation":mode,"frames":frames,"seconds":seconds,"fps":frames/seconds,"nodes":get_tree().get_node_count()})
			print("CENTURION_BENCHMARK ",count," ",mode," ",frames/seconds)
	var file := FileAccess.open("res://reports/roman_centurion/native/stress_baseline.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"engine":Engine.get_version_info(),"renderer":RenderingServer.get_video_adapter_name(),"viewport":[1920,1080],"scope":"Desktop baseline only; stationary grid with randomized animation phases","scene_sha256":FileAccess.get_sha256("res://scenes/units/odyssey/roman_centurion/roman_centurion_rig.tscn"),"records":records},"\t"))
	get_tree().quit()
