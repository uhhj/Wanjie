extends Node2D
const RIG = preload("res://scenes/units/odyssey/roman_guard/roman_guard_rig.tscn")
var units: Array = []
var mode := "walk"
var count := 20
var label: Label
var rng = RandomNumberGenerator.new()
var benchmark := false

func _ready() -> void:
	rng.seed = 7402
	benchmark = "--benchmark" in OS.get_cmdline_user_args()
	var layer = CanvasLayer.new()
	add_child(layer)
	var box = HBoxContainer.new()
	box.position = Vector2(15,10)
	layer.add_child(box)
	var quantities = OptionButton.new()
	for n in [1,10,20,30,50]:
		quantities.add_item(str(n))
	quantities.select(2)
	quantities.item_selected.connect(func(i): count = [1,10,20,30,50][i]; populate())
	box.add_child(quantities)
	var modes = OptionButton.new()
	for n in ["idle","walk","attack_loop","hit_loop","death_once"]:
		modes.add_item(n)
	modes.select(1)
	modes.item_selected.connect(func(i): mode = modes.get_item_text(i); populate())
	box.add_child(modes)
	var back = Button.new()
	back.text = "Rig Lab"
	back.pressed.connect(func(): get_tree().change_scene_to_file("res://scenes/tests/roman_guard_rig_lab.tscn"))
	box.add_child(back)
	label = Label.new()
	box.add_child(label)
	populate()
	if benchmark:
		call_deferred("run_benchmark")

func animation_name() -> String:
	return {"attack_loop":"attack_01","hit_loop":"hit","death_once":"death"}.get(mode,mode)

func populate() -> void:
	for unit in units:
		unit.free()
	units.clear()
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://resources/human_medium_rig_v1.json"))
	for i in range(count):
		var unit = RIG.instantiate()
		unit.autoplay = false
		unit.position = Vector2(100+(i%10)*190,245+(i/10)*195)
		unit.scale = Vector2.ONE * 192.0 / float(data.body_height)
		add_child(unit)
		unit.animation_player.animation_finished.connect(func(n):
			if (mode == "attack_loop" and n == &"attack_01") or (mode == "hit_loop" and n == &"hit"):
				unit.play_animation(animation_name()))
		unit.play_animation(animation_name())
		unit.animation_player.seek(rng.randf()*unit.animation_player.current_animation_length,true)
		units.append(unit)

func _process(_delta: float) -> void:
	label.text = "  FPS %.1f | Units %d | Nodes %d | %s" % [Engine.get_frames_per_second(),count,get_tree().get_node_count(),mode]

func run_benchmark() -> void:
	DisplayServer.window_set_size(Vector2i(1920,1080))
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	var records: Array = []
	for amount in [20,50]:
		for test_mode in ["idle","walk","attack_loop","hit_loop","death_once"]:
			count = amount
			mode = test_mode
			populate()
			await get_tree().create_timer(1.5).timeout
			var start = Time.get_ticks_usec()
			var first_frame = Engine.get_frames_drawn()
			await get_tree().create_timer(3.0).timeout
			var seconds = (Time.get_ticks_usec()-start)/1000000.0
			var frames = Engine.get_frames_drawn()-first_frame
			var size = get_viewport().get_visible_rect().size
			var row = {"units":count,"mode":mode,"elapsed_seconds":seconds,"rendered_frames":frames,"fps":frames/seconds,"node_count":get_tree().get_node_count(),"viewport":[size.x,size.y],"renderer":RenderingServer.get_video_adapter_name()}
			records.append(row)
			print("BENCHMARK ",JSON.stringify(row))
	var file = FileAccess.open("res://reports/native_rig_v2/stress_results.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"status":"COMPLETED","engine":Engine.get_version_info(),"desktop_only":true,"vsync":false,"results":records},"\t"))
	get_tree().quit()
