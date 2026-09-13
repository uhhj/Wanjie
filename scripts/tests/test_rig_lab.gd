extends SceneTree

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var lab = load("res://scenes/tests/roman_guard_rig_lab.tscn").instantiate()
	root.add_child(lab)
	await process_frame
	assert(lab.animation_choice.item_count==5)
	var unit = lab.unit
	unit.animation_player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	lab.animation_choice.select(2)
	for button in lab.find_children("*","Button",true,false):
		if button.text=="Restart":
			button.pressed.emit()
	unit.animation_player.advance(.81)
	assert(unit.attack_hit_count==1)
	assert(unit.animation_player.current_animation==&"idle")
	lab.animation_choice.select(1)
	lab.play_selected()
	assert(unit.animation_player.current_animation==&"walk")
	for button in lab.find_children("*","Button",true,false):
		if button.text=="Pause":
			button.pressed.emit()
	assert(not unit.animation_player.is_playing())
	lab.play_selected()
	assert(unit.animation_player.is_playing())
	for check in lab.find_children("*","CheckBox",true,false):
		check.button_pressed = true
	var debug = unit.get_node("DebugRoot")
	assert(debug.visible and debug.show_bones and debug.show_pivots and debug.show_ground and debug.show_sockets)
	lab.free()
	var stress = load("res://scenes/tests/roman_guard_stress_test.tscn").instantiate()
	root.add_child(stress)
	await process_frame
	for count in [1,10,20,30,50]:
		stress.count = count
		stress.populate()
		assert(stress.units.size()==count)
	stress.free()
	var file = FileAccess.open("res://reports/native_rig_v2/rig_lab_tests.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"status":"PASS","dropdown":5,"play_pause_restart":"PASS","debug_controls":"PASS","attack_per_play":1,"stress_quantities":[1,10,20,30,50]},"\t"))
	print("RIG_LAB_TESTS PASS")
	quit()
