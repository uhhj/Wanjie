extends SceneTree
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var scene:="res://work/minotaur_breaker/candidates/minotaur_breaker_candidate.tscn"
	var report_name:="motion_contract_test.json"
	if "--formal" in OS.get_cmdline_user_args():
		scene="res://scenes/units/odyssey/minotaur_breaker/minotaur_breaker_rig.tscn"
		report_name="formal_motion_contract_test.json"
	var unit=load(scene).instantiate()
	unit.autoplay=false
	unit.root_motion_enabled=false
	root.add_child(unit)
	unit.set_process(false)
	unit.animation_player.callback_mode_process=AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://resources/minotaur_breaker_rig_v1.json"))
	var errors:Array=[]
	var contacts:Dictionary={}
	for side in ["near","far"]:
		var max_drift:=0.0
		var anchor:=Vector2.ZERO
		var active:=false
		var samples:Array=[]
		for i in 281:
			var phase:float=i/280.
			var u:float=fmod(phase+(0. if side=="near" else .5),1.)
			unit.play_animation("walk")
			unit.animation_player.seek(phase*1.4,true)
			unit.position=Vector2(unit.walk_stride*phase,0)
			var foot:Bone2D=unit.get_node("VisualRoot/Skeleton2D/"+str(data.bones["foot_"+side].path))
			var point:Vector2=foot.to_global(Vector2(30,125))
			if u>.03 and u<.59:
				if not active:anchor=point
				active=true
				max_drift=max(max_drift,anchor.distance_to(point))
				samples.append({"phase":phase,"world_sole":[point.x,point.y]})
			else:active=false
		contacts[side]={"max_source_pixel_drift":max_drift,"max_360px_drift":max_drift*360./1435.,"max_288px_drift":max_drift*288./1435.,"samples":samples}
		if max_drift*360./1435.>1.0:errors.append(side+" support foot drift >1 display pixel")
	var events:Dictionary={}
	for name in ["attack_01","skill_01"]:
		var counts:=[0,0]
		var cb_attack:=func():counts[0]+=1
		var cb_skill:=func():counts[1]+=1
		unit.attack_hit.connect(cb_attack)
		unit.skill_hit.connect(cb_skill)
		unit.play_animation(name)
		var duration:float=unit.animation_player.get_animation(name).length
		for i in 121:unit.animation_player.advance(duration/120.)
		var expected:Array=[1,0] if name=="attack_01" else [0,1]
		if counts!=expected:errors.append(name+" event count mismatch")
		events[name]=counts.duplicate()
		unit.attack_hit.disconnect(cb_attack)
		unit.skill_hit.disconnect(cb_skill)
	var report:={"status":"PASS" if errors.is_empty() else "FAIL","scope":"Native bone support-foot trajectories and independent event tracks; visual approval separate","scene_sha256":FileAccess.get_sha256(scene),"walk_contact":contacts,"events_attack_skill":events,"errors":errors}
	var f:=FileAccess.open("res://reports/minotaur_breaker/"+report_name,FileAccess.WRITE)
	f.store_string(JSON.stringify(report,"  ")+"\n")
	print("MINOTAUR_MOTION_CONTRACT ",report.status," near drift ",contacts.near.max_360px_drift," far drift ",contacts.far.max_360px_drift," events ",events)
	unit.queue_free()
	quit(0 if errors.is_empty() else 2)
