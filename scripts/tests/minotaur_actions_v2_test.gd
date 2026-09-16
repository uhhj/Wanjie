extends SceneTree
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var scene:="res://work/minotaur_breaker/candidates/minotaur_breaker_candidate.tscn"
	if "--formal" in OS.get_cmdline_user_args():scene="res://scenes/units/odyssey/minotaur_breaker/minotaur_breaker_rig.tscn"
	var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://resources/minotaur_breaker_rig_v1.json"))
	var unit=load(scene).instantiate();unit.autoplay=false;unit.root_motion_enabled=false;root.add_child(unit);unit.set_process(false)
	unit.animation_player.callback_mode_process=AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	var nodes:Dictionary={}
	for bone in data.bones:nodes[bone]=unit.get_node("VisualRoot/Skeleton2D/"+str(data.bones[bone].path))
	var errors:Array=[];var grip_error:=0.0
	unit.play_animation("attack_01")
	for i in 127:
		unit.animation_player.seek(.22+i*.01,true)
		var expected:Vector2=nodes.axe_socket.to_global(Vector2(-18,150))
		grip_error=max(grip_error,expected.distance_to(nodes.axe_support_socket.global_position))
	if grip_error>1:errors.append("Two-hand grip drift >1 source px")
	unit.animation_player.seek(.70,true)
	var both_hands_above_head:bool=nodes.axe_socket.global_position.y<nodes.head.global_position.y and nodes.axe_support_socket.global_position.y<nodes.head.global_position.y
	if not both_hands_above_head:errors.append("Overhead pose hands not above head anchor")
	var raised_blade:Vector2=nodes.axe_socket.to_global(Vector2(19,-220))
	unit.animation_player.seek(1.10,true)
	var lowered_blade:Vector2=nodes.axe_socket.to_global(Vector2(19,-220))
	var blade_drop:float=lowered_blade.y-raised_blade.y
	if blade_drop<650:errors.append("Downward axe arc too small")
	var drift:Dictionary={}
	for side in ["near","far"]:
		var active:=false;var last_cycle:=-1;var anchor:=Vector2.ZERO;var maximum:=0.0
		unit.play_animation("skill_01")
		for i in 577:
			var t:float=.60+i*.005;var phase:float=(t-.6)/.48+(0 if side=="near" else .5);var u:=fmod(phase,1.)
			unit.animation_player.seek(t,true);unit.position=Vector2(unit.root_distance,0)
			var point:Vector2=nodes["foot_"+side].to_global(Vector2(30,125))
			if u>.03 and u<.52:
				if not active or int(floor(phase))!=last_cycle:anchor=point
				active=true;last_cycle=int(floor(phase));maximum=max(maximum,point.distance_to(anchor))
			else:active=false
		drift[side]=maximum*360./1435.
		if drift[side]>1:errors.append(side+" charge support drift >1 display px")
	unit.animation_player.seek(4.2,true)
	var distance:float=unit.root_distance
	if abs(distance-2880)>1:errors.append("Charge distance mismatch")
	var events:Dictionary={}
	for name in ["attack_01","skill_01"]:
		var counts:=[0,0]
		var attack:=func():counts[0]+=1
		var skill:=func():counts[1]+=1
		unit.attack_hit.connect(attack);unit.skill_hit.connect(skill);unit.play_animation(name)
		var duration:float=unit.animation_player.current_animation_length
		for i in 601:unit.animation_player.advance(duration/600.)
		if counts!=([1,0] if name=="attack_01" else [0,1]):errors.append(name+" event mismatch")
		events[name]=counts.duplicate();unit.attack_hit.disconnect(attack);unit.skill_hit.disconnect(skill)
	# Exercise actual root-motion integration, including the return to idle.
	unit.position=Vector2.ZERO;unit.scale=Vector2.ONE*360./1435.;unit.root_motion_enabled=true
	unit.play_animation("skill_01")
	for i in 420:
		unit.animation_player.advance(.01)
		unit._process(.01)
	var integrated_distance:float=unit.position.x
	if abs(integrated_distance-2880.*360./1435.)>.1:errors.append("Runtime root motion integration mismatch")
	unit.play_animation("idle");unit.animation_player.advance(0)
	unit._process(0)
	if abs(unit.position.x-integrated_distance)>.01:errors.append("Idle reset teleported unit")
	for bone in ["arm_near_upper","arm_far_upper"]:
		var expected:=Vector2(data.bones[bone].local_position[0],data.bones[bone].local_position[1])
		if nodes[bone].position.distance_to(expected)>.001:errors.append("Shoulder position did not reset")
	var report:={"status":"PASS" if errors.is_empty() else "FAIL","scene_sha256":FileAccess.get_sha256(scene),"both_hands_above_head_anchor":both_hands_above_head,"two_hand_grip_max_source_px":grip_error,"axe_downward_travel_source_px":blade_drop,"charge_distance_source_px":distance,"charge_distance_360px":distance*360/1435,"charge_support_drift_360px":drift,"events":events,"errors":errors}
	report["runtime_integrated_distance_360px"]=integrated_distance
	var prefix:="formal_" if "--formal" in OS.get_cmdline_user_args() else ""
	var file:=FileAccess.open("res://reports/minotaur_breaker/"+prefix+"actions_v2_test.json",FileAccess.WRITE);file.store_string(JSON.stringify(report,"  ")+"\n")
	print(JSON.stringify(report));unit.queue_free();quit(0 if errors.is_empty() else 2)
