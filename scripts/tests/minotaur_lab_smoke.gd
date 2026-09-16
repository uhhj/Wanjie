extends SceneTree
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var lab=load("res://scenes/tests/minotaur_breaker_rig_lab.tscn").instantiate()
	root.add_child(lab)
	await process_frame
	var errors:Array=[]
	if lab.picker.item_count!=6:errors.append("Missing animation options")
	lab.unit.animation_player.callback_mode_process=AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	lab.unit.set_process(false)
	lab._control("Pause")
	if lab.unit.animation_player.is_playing():errors.append("Pause failed")
	lab._control("Play")
	if not lab.unit.animation_player.is_playing():errors.append("Play failed")
	lab.mana_demo=true
	lab.mana_ticks=0
	for cycle in 4:
		lab.unit.play_animation("attack_01")
		var attack_length:float=lab.unit.animation_player.get_animation("attack_01").length
		for frame in 121:lab.unit.animation_player.advance(attack_length/120.)
		await process_frame
	if lab.unit.animation_player.assigned_animation!="skill_01":errors.append("Full demo mana did not trigger skill")
	var skill_length:float=lab.unit.animation_player.get_animation("skill_01").length
	for frame in 121:lab.unit.animation_player.advance(skill_length/120.)
	await process_frame
	if lab.attacks!=4 or lab.skills!=1:errors.append("Demo event counts incorrect")
	lab.unit.play_animation("death")
	for frame in 121:lab.unit.animation_player.advance(1.7/120.)
	await process_frame
	if lab.unit.animation_player.assigned_animation!="death":errors.append("Death unexpectedly restored")
	lab.unit.position.x=1550.
	lab._process(0)
	if lab.follow_camera.position.x<=lab.get_viewport_rect().size.x/2.:errors.append("Charge camera did not follow")
	if lab.unit.position.x!=1550.:errors.append("Camera changed actual world position")
	var report:={"status":"PASS" if errors.is_empty() else "FAIL","checks":["six choices","pause","resume","four demo normal hits trigger one skill","death holds"],"attack_events":lab.attacks,"skill_events":lab.skills,"scope":"Lab call/state smoke, no damage or production mana constants","errors":errors}
	var f:=FileAccess.open("res://reports/minotaur_breaker/lab_smoke.json",FileAccess.WRITE)
	f.store_string(JSON.stringify(report,"  ")+"\n")
	print("MINOTAUR_LAB_SMOKE ",JSON.stringify(report))
	lab.queue_free()
	quit(0 if errors.is_empty() else 2)
