extends Node2D
const SCENE = preload("res://scenes/units/odyssey/roman_centurion/roman_centurion_rig.tscn")
const NAMES = ["idle","walk","attack_01","hit","death","skill_command"]
var unit: Node2D
var picker: OptionButton
var status: Label
var debug_bones := false
var debug_pivots := false
var debug_sockets := false
var ground := true
func _ready() -> void:
	unit = SCENE.instantiate()
	unit.scale = Vector2.ONE*256.0/1425.0
	unit.position = Vector2(650,780)
	add_child(unit)
	var layer := CanvasLayer.new()
	add_child(layer)
	var panel := VBoxContainer.new()
	panel.position = Vector2(24,24)
	panel.custom_minimum_size = Vector2(360,400)
	layer.add_child(panel)
	var title := Label.new()
	title.text = "Roman Centurion | Native Rig Lab V1"
	panel.add_child(title)
	picker = OptionButton.new()
	for n in NAMES: picker.add_item(n)
	panel.add_child(picker)
	picker.item_selected.connect(func(_i): restart())
	var buttons := HBoxContainer.new()
	panel.add_child(buttons)
	for name in ["Play","Pause","Restart"]:
		var button := Button.new()
		button.text = name
		buttons.add_child(button)
		if name=="Play": button.pressed.connect(func(): unit.animation_player.play())
		elif name=="Pause": button.pressed.connect(func(): unit.animation_player.pause())
		else: button.pressed.connect(restart)
	var speed := OptionButton.new()
	for text in ["0.5x","1x","2x"]: speed.add_item(text)
	speed.select(1)
	speed.item_selected.connect(func(i): unit.animation_player.speed_scale=[.5,1.,2.][i])
	panel.add_child(speed)
	var display := OptionButton.new()
	display.add_item("256 px")
	display.add_item("192 px")
	display.item_selected.connect(func(i): unit.scale=Vector2.ONE*[256.,192.][i]/1425.)
	panel.add_child(display)
	for text in ["Skeleton","Pivots","Sockets","Ground line"]:
		var check := CheckBox.new()
		check.text = text
		check.button_pressed = text=="Ground line"
		check.toggled.connect(toggle_debug.bind(text))
		panel.add_child(check)
	status = Label.new()
	panel.add_child(status)
func toggle_debug(on: bool, text: String) -> void:
	match text:
		"Skeleton": debug_bones=on
		"Pivots": debug_pivots=on
		"Sockets": debug_sockets=on
		"Ground line": ground=on
func restart() -> void:
	unit.position = Vector2(650,780)
	unit.play_animation(NAMES[picker.selected])
func _process(_delta: float) -> void:
	if unit.position.x>1600: unit.position.x=650
	status.text = "%s | %.2fs\nattack_hit: %d | command_release: %d\nFPS: %d" % [unit.animation_player.assigned_animation,unit.animation_player.current_animation_position,unit.attack_hit_count,unit.command_release_count,Engine.get_frames_per_second()]
	queue_redraw()
func _draw() -> void:
	if ground: draw_line(Vector2(420,781),Vector2(1840,781),Color.GRAY,1)
	if unit==null: return
	for bone in unit.find_children("*","Bone2D",true,false):
		var pt: Vector2 = bone.global_position
		if debug_pivots: draw_circle(pt,3,Color.YELLOW)
		if debug_sockets and "socket" in str(bone.name): draw_circle(pt,5,Color.CYAN)
		if debug_bones and bone.get_parent() is Bone2D: draw_line(bone.get_parent().global_position,pt,Color.GREEN,1)
