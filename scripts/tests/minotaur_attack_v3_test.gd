extends SceneTree
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var scene:="res://work/minotaur_breaker/candidates/minotaur_breaker_candidate.tscn"
	if "--formal" in OS.get_cmdline_user_args():scene="res://scenes/units/odyssey/minotaur_breaker/minotaur_breaker_rig.tscn"
	var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://resources/minotaur_breaker_rig_v1.json"))
	var unit=load(scene).instantiate();unit.autoplay=false;root.add_child(unit);unit.set_process(false)
	unit.animation_player.callback_mode_process=AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	var nodes:Dictionary={}
	for bone in data.bones:nodes[bone]=unit.get_node("VisualRoot/Skeleton2D/"+str(data.bones[bone].path))
	var errors:Array=[];var grip_error:=0.;var previous_angle:=0.;var recovery_travel:=0.
	unit.play_animation("attack_01")
	for i in 105:
		unit.animation_player.seek(.22+i*.01,true)
		grip_error=maxf(grip_error,nodes.axe_socket.to_global(Vector2(-49,460)).distance_to(nodes.axe_support_socket.global_position))
	if grip_error>.01:errors.append("Lower-shaft two-hand grip drift")
	unit.animation_player.seek(.98,true)
	var reach:Dictionary={}
	for side in ["near","far"]:
		var upper:Vector2=nodes["arm_"+side+"_upper"].global_position
		var elbow:Vector2=nodes["arm_"+side+"_fore"].global_position
		var wrist:Vector2=nodes["hand_"+side].global_position
		reach[side]=upper.distance_to(wrist)/(upper.distance_to(elbow)+elbow.distance_to(wrist))
		if reach[side]<.87:errors.append(side+" strike arm insufficiently extended")
	var blade:Vector2=nodes.axe_socket.to_global(Vector2(19,-220))
	var blade_forward:float=blade.x-nodes.pelvis.global_position.x
	if blade_forward<650:errors.append("Effective axe reach too short")
	for i in 85:
		unit.animation_player.seek(1.26+i*.01,true)
		var angle:float=nodes.axe_socket.global_rotation
		if i>0:
			var delta:=wrapf(angle-previous_angle,-PI,PI)
			recovery_travel+=absf(delta)
			if delta>.005:errors.append("Recovery reverses into extra spin")
		previous_angle=angle
	if rad_to_deg(recovery_travel)>145:errors.append("Recovery angular travel excessive")
	var counts:=[0]
	unit.attack_hit.connect(func():counts[0]+=1)
	unit.play_animation("attack_01")
	for i in 211:unit.animation_player.advance(.01)
	if counts[0]!=1:errors.append("Attack event count incorrect")
	unit.play_animation("idle");unit.animation_player.advance(0)
	var rest:Array=data.bones.axe_socket.local_position
	if nodes.axe_socket.position.distance_to(Vector2(rest[0],rest[1]))>.001:errors.append("Axe grip offset failed to reset")
	var result:={"status":"PASS" if errors.is_empty() else "FAIL","scene_sha256":FileAccess.get_sha256(scene),"two_hand_grip_error_source_px":grip_error,"arm_extension_ratio":reach,"blade_forward_reach_source_px":blade_forward,"recovery_total_degrees":rad_to_deg(recovery_travel),"attack_hit_count":counts[0],"errors":errors}
	var prefix:="formal_" if "--formal" in OS.get_cmdline_user_args() else ""
	FileAccess.open("res://reports/minotaur_breaker/"+prefix+"attack_v3_test.json",FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	print(JSON.stringify(result));unit.queue_free();quit(0 if errors.is_empty() else 2)
