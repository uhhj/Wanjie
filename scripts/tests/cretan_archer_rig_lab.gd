extends Node2D

const UNIT_SCENE := "res://scenes/units/odyssey/cretan_archer/cretan_archer_rig.tscn"
const RIG_FILE := "res://resources/cretan_archer_rig_v1.json"
const ANIMATIONS := ["idle", "walk", "attack_01", "hit", "death"]

var unit
var animation_picker: OptionButton
var speed_picker: OptionButton
var scale_picker: OptionButton
var status_label: Label
var debug_options: Dictionary = {}
var combat_ground_line: Line2D
var body_height := 1.0
var start_position := Vector2(640.0, 620.0)

func _ready() -> void:
	RenderingServer.set_default_clear_color(Color(0.86, 0.87, 0.88))
	_build_controls()
	if not ResourceLoader.exists(UNIT_SCENE) or not FileAccess.file_exists(RIG_FILE):
		status_label.text = "Archer Rig unavailable. Complete formal asset gate and native build first."
		return
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(RIG_FILE))
	body_height = float(data.body_height)
	unit = load(UNIT_SCENE).instantiate()
	unit.autoplay = false
	unit.position = start_position
	unit.scale = Vector2.ONE * 256.0 / body_height
	add_child(unit)
	var debug = unit.get_node("DebugRoot")
	debug.z_as_relative = false
	debug.z_index = 4095
	for option in debug_options:
		debug.set(option, false)
	# This Lab overlay stays one screen pixel wide at both combat scales.
	# The reusable unit's source-space debug line becomes subpixel when scaled.
	combat_ground_line = Line2D.new()
	combat_ground_line.name = "CombatGroundLine"
	combat_ground_line.points = PackedVector2Array([start_position + Vector2(-220, 0), start_position + Vector2(220, 0)])
	combat_ground_line.width = 1.25
	combat_ground_line.default_color = Color(0.1, 0.7, 0.35)
	combat_ground_line.z_as_relative = false
	combat_ground_line.z_index = 4095
	combat_ground_line.visible = false
	add_child(combat_ground_line)
	unit.play_animation("idle")

func _build_controls() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	var panel := PanelContainer.new()
	panel.position = Vector2(20, 20)
	panel.custom_minimum_size = Vector2(320, 0)
	layer.add_child(panel)
	var margin := MarginContainer.new()
	for side in ["left", "right", "top", "bottom"]:
		margin.add_theme_constant_override("margin_" + side, 14)
	panel.add_child(margin)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 10)
	margin.add_child(column)
	var title := Label.new()
	title.text = "Cretan Archer Native Rig Lab"
	column.add_child(title)
	animation_picker = OptionButton.new()
	animation_picker.name = "AnimationDropdown"
	for animation in ANIMATIONS:
		animation_picker.add_item(animation)
	column.add_child(animation_picker)
	var buttons := HBoxContainer.new()
	column.add_child(buttons)
	for entry in [["Play", _play], ["Pause", _pause], ["Restart", _restart]]:
		var button := Button.new()
		button.text = entry[0]
		button.name = entry[0] + "Button"
		button.pressed.connect(entry[1])
		buttons.add_child(button)
	speed_picker = OptionButton.new()
	speed_picker.name = "SpeedDropdown"
	for value in [0.5, 1.0, 2.0]:
		speed_picker.add_item(str(value) + "x")
		speed_picker.set_item_metadata(speed_picker.item_count - 1, value)
	speed_picker.select(1)
	speed_picker.item_selected.connect(_change_speed)
	column.add_child(speed_picker)
	scale_picker = OptionButton.new()
	scale_picker.name = "CombatScaleDropdown"
	for height in [256, 192]:
		scale_picker.add_item(str(height) + "px character height")
		scale_picker.set_item_metadata(scale_picker.item_count - 1, height)
	scale_picker.item_selected.connect(_change_scale)
	column.add_child(scale_picker)
	for entry in [["Skeleton visible", "show_bones"], ["Pivots visible", "show_pivots"], ["Ground line", "show_ground"], ["Sockets visible", "show_sockets"]]:
		var toggle := CheckBox.new()
		toggle.text = entry[0]
		toggle.name = str(entry[1])
		toggle.toggled.connect(_change_debug.bind(str(entry[1])))
		column.add_child(toggle)
		debug_options[entry[1]] = toggle
	var recenter := Button.new()
	recenter.text = "Recenter"
	recenter.pressed.connect(_recenter)
	column.add_child(recenter)
	status_label = Label.new()
	status_label.name = "RuntimeStatus"
	status_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	status_label.custom_minimum_size = Vector2(290, 85)
	column.add_child(status_label)

func selected_animation() -> String:
	return animation_picker.get_item_text(animation_picker.selected)

func _play() -> void:
	if unit == null:
		return
	var name := selected_animation()
	var player: AnimationPlayer = unit.animation_player
	if str(player.assigned_animation) == name and not player.is_playing() and player.current_animation_position < player.current_animation_length:
		player.play()
	else:
		unit.play_animation(name)
	_change_speed(speed_picker.selected)

func _pause() -> void:
	if unit != null:
		unit.animation_player.pause()

func _restart() -> void:
	if unit != null:
		_recenter()
		unit.play_animation(selected_animation())
		_change_speed(speed_picker.selected)

func _recenter() -> void:
	if unit != null:
		unit.position = start_position

func _change_speed(index: int) -> void:
	if unit != null:
		unit.animation_player.speed_scale = float(speed_picker.get_item_metadata(index))

func _change_scale(index: int) -> void:
	if unit != null:
		unit.scale = Vector2.ONE * float(scale_picker.get_item_metadata(index)) / body_height

func _change_debug(enabled: bool, property: String) -> void:
	if unit == null:
		return
	var debug = unit.get_node("DebugRoot")
	debug.set(property, enabled)
	if property == "show_ground" and combat_ground_line != null:
		combat_ground_line.visible = enabled
	var any_enabled := false
	for toggle in debug_options.values():
		any_enabled = any_enabled or toggle.button_pressed
	debug.visible = any_enabled

func _process(_delta: float) -> void:
	if unit == null:
		return
	var player: AnimationPlayer = unit.animation_player
	status_label.text = "Current: %s\nTime: %.3f / %.3f s\nattack_release count: %d\n%s" % [str(player.assigned_animation), player.current_animation_position, player.current_animation_length, unit.attack_release_count, "Playing" if player.is_playing() else "Paused / held"]
