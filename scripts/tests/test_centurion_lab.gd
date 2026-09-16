extends SceneTree
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var lab = load("res://scenes/tests/roman_centurion_rig_lab.tscn").instantiate()
	root.add_child(lab)
	await process_frame
	var errors: Array = []
	if lab.picker.item_count!=6: errors.append("Expected six animation choices")
	var player: AnimationPlayer = lab.unit.animation_player
	player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	player.callback_mode_method = AnimationMixer.ANIMATION_CALLBACK_MODE_METHOD_IMMEDIATE
	lab.picker.select(5)
	lab.restart()
	for i in 190: player.advance(.01)
	if lab.unit.command_release_count!=1: errors.append("Lab command event must occur once")
	if player.assigned_animation!=&"idle": errors.append("Command must return to idle")
	lab.picker.select(2)
	lab.restart()
	for i in 120: player.advance(.01)
	if lab.unit.attack_hit_count!=1: errors.append("Lab attack event must occur once")
	player.pause()
	var t := player.current_animation_position
	await process_frame
	await process_frame
	if player.current_animation_position!=t: errors.append("Pause did not hold time")
	for name in ["Skeleton","Pivots","Sockets","Ground line"]: lab.toggle_debug(true,name)
	if not (lab.debug_bones and lab.debug_pivots and lab.debug_sockets and lab.ground): errors.append("Debug switches failed")
	var f := FileAccess.open("res://reports/roman_centurion/native/rig_lab_tests.json",FileAccess.WRITE)
	f.store_string(JSON.stringify({"status":"PASS" if errors.is_empty() else "FAIL","errors":errors,"checks":["six animation choices","restart","attack event once","command event once","return idle","pause","four debug toggles"]},"\t"))
	print("CENTURION_LAB ",errors)
	lab.free()
	quit(0 if errors.is_empty() else 2)
