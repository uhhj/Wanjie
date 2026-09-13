extends Node2D
const RIG = preload("res://scenes/units/odyssey/roman_guard/roman_guard_rig.tscn")
var unit: Node2D
var animation_choice: OptionButton
var status_label: Label

func button(text: String, callback: Callable, parent: Node) -> void:
	var b = Button.new()
	b.text = text
	b.pressed.connect(callback)
	parent.add_child(b)

func _ready() -> void:
	unit = RIG.instantiate()
	unit.position = Vector2(1050,750)
	unit.scale = Vector2.ONE * 256.0 / 1435.0
	add_child(unit)
	var canvas = CanvasLayer.new()
	add_child(canvas)
	var panel = PanelContainer.new()
	panel.position = Vector2(35,35)
	panel.custom_minimum_size = Vector2(360,550)
	canvas.add_child(panel)
	var box = VBoxContainer.new()
	box.add_theme_constant_override("separation",12)
	panel.add_child(box)
	var title = Label.new()
	title.text = "ROMAN GUARD / Native Rig Lab V2"
	box.add_child(title)
	animation_choice = OptionButton.new()
	for n in ["idle","walk","attack_01","hit","death"]:
		animation_choice.add_item(n)
	box.add_child(animation_choice)
	button("Play",play_selected,box)
	button("Pause",func(): unit.animation_player.pause(),box)
	button("Restart",func(): unit.play_animation(animation_choice.get_item_text(animation_choice.selected)),box)
	var speeds = OptionButton.new()
	for text in ["0.5x","1x","2x"]:
		speeds.add_item(text)
	speeds.select(1)
	speeds.item_selected.connect(func(i): unit.animation_player.speed_scale = [0.5,1.0,2.0][i])
	box.add_child(speeds)
	var sizes = OptionButton.new()
	for text in ["256px character", "192px character", "512px inspection"]:
		sizes.add_item(text)
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://resources/human_medium_rig_v1.json"))
	unit.scale = Vector2.ONE * 256.0 / float(data.body_height)
	sizes.item_selected.connect(func(i): unit.scale = Vector2.ONE * [256.0,192.0,512.0][i] / float(data.body_height))
	box.add_child(sizes)
	var debug = unit.get_node("DebugRoot")
	for entry in [["Skeleton visible","show_bones"],["Pivot visible","show_pivots"],["Ground line","show_ground"],["Sockets visible","show_sockets"]]:
		debug.set(entry[1],false)
		var check = CheckBox.new()
		check.text = entry[0]
		check.toggled.connect(func(enabled): debug.set(entry[1],enabled); debug.visible = debug.show_bones or debug.show_pivots or debug.show_ground or debug.show_sockets)
		box.add_child(check)
	status_label = Label.new()
	box.add_child(status_label)
	button("Stress Test",func(): get_tree().change_scene_to_file("res://scenes/tests/roman_guard_stress_test.tscn"),box)
	var note = Label.new()
	note.position = Vector2(660,900)
	note.text = "Frozen assets / native Skeleton2D + Bone2D + AnimationPlayer\nNear knee: independent plate + approved Polygon2D weights"
	canvas.add_child(note)

func play_selected() -> void:
	var selected = animation_choice.get_item_text(animation_choice.selected)
	if unit.animation_player.assigned_animation == selected and not unit.animation_player.is_playing():
		unit.animation_player.play()
	else:
		unit.play_animation(selected)

func _process(_delta: float) -> void:
	if is_instance_valid(unit):
		if unit.position.x > 1750.0:
			unit.position.x = 650.0 # Lab runway boundary; no change to the gait itself.
		status_label.text = "Current: %s\nTime: %.3f\nattack_hit counter: %d" % [unit.animation_player.current_animation,unit.animation_player.current_animation_position,unit.attack_hit_count]
