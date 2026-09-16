extends Node2D
const SCENE := "res://scenes/units/odyssey/minotaur_breaker/minotaur_breaker_rig.tscn"
const NAMES := ["idle","walk","attack_01","skill_01","hit","death"]
var unit
var picker: OptionButton
var status: Label
var attacks := 0
var skills := 0
var debug: Node2D
var mana_demo := false
var mana_ticks := 0
var mana_bar: ProgressBar
func _ready() -> void:
	RenderingServer.set_default_clear_color(Color(.85,.86,.87))
	unit = load(SCENE).instantiate()
	unit.autoplay = false
	unit.scale = Vector2.ONE*360./1435.
	unit.position = Vector2(800,700)
	add_child(unit)
	unit.attack_hit.connect(_attack_event)
	unit.skill_hit.connect(func(): skills+=1)
	unit.animation_player.animation_finished.connect(_demo_finished)
	debug = Node2D.new()
	debug.set_script(load("res://scripts/rig/rig_debug.gd"))
	debug.z_as_relative = false
	debug.z_index = 4095
	debug.visible = false
	unit.add_child(debug)
	var layer := CanvasLayer.new()
	add_child(layer)
	var panel := PanelContainer.new()
	panel.position = Vector2(20,20)
	panel.custom_minimum_size = Vector2(340,0)
	layer.add_child(panel)
	var box := VBoxContainer.new()
	panel.add_child(box)
	var title := Label.new()
	title.text = "Minotaur Native Rig Lab V1\nSingle-unit approved; dense stress limits documented"
	box.add_child(title)
	picker = OptionButton.new()
	for name in NAMES:picker.add_item(name)
	box.add_child(picker)
	for text in ["Play","Pause","Restart"]:
		var button := Button.new()
		button.text = text
		button.pressed.connect(_control.bind(text))
		box.add_child(button)
	var speed := OptionButton.new()
	for text in ["0.5x","1x","2x"]:speed.add_item(text)
	speed.select(1)
	speed.item_selected.connect(func(i):unit.animation_player.speed_scale=[.5,1.,2.][i])
	box.add_child(speed)
	var sizes := OptionButton.new()
	for text in ["360px","288px"]:sizes.add_item(text)
	sizes.item_selected.connect(func(i):unit.scale=Vector2.ONE*[360.,288.][i]/1435.)
	box.add_child(sizes)
	for setting in ["show_bones","show_pivots","show_ground","show_sockets"]:
		debug.set(setting,false)
		var toggle := CheckBox.new()
		toggle.text = setting
		toggle.toggled.connect(func(on):debug.visible=true;debug.set(setting,on))
		box.add_child(toggle)
	status = Label.new()
	box.add_child(status)
	var mana_toggle:=CheckBox.new()
	mana_toggle.text="Mana trigger demo (4 attacks, not balance)"
	mana_toggle.toggled.connect(func(on):mana_demo=on;mana_ticks=0)
	box.add_child(mana_toggle)
	mana_bar=ProgressBar.new()
	mana_bar.max_value=4
	mana_bar.custom_minimum_size=Vector2(320,20)
	box.add_child(mana_bar)
	unit.play_animation("idle")
func _attack_event() -> void:
	attacks+=1
	if mana_demo:mana_ticks=mini(4,mana_ticks+1)
func _demo_finished(animation:StringName) -> void:
	if mana_demo and animation==&"attack_01" and mana_ticks==4:
		mana_ticks=0
		unit.call_deferred("play_animation","skill_01")
func _control(action: String) -> void:
	if action == "Pause":unit.animation_player.pause()
	elif action == "Play" and unit.animation_player.assigned_animation == picker.get_item_text(picker.selected):unit.animation_player.play()
	else:
		unit.position = Vector2(800,700)
		attacks=0;skills=0
		unit.play_animation(picker.get_item_text(picker.selected))
func _process(_delta:float) -> void:
	if unit==null:return
	if mana_bar!=null:mana_bar.value=mana_ticks
	status.text="Animation: %s\nTime: %.3f\nattack_hit: %d\nskill_hit: %d\nFPS: %d"%[unit.animation_player.assigned_animation,unit.animation_player.current_animation_position,attacks,skills,Engine.get_frames_per_second()]
