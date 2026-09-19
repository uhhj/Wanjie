extends SceneTree
## Skill V4 candidate checks: front-low carry keeps hand and blade clear of the
## body, deep lean preserved, single skill event, socket reset.
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var scene:="res://work/minotaur_breaker/candidates/minotaur_breaker_candidate.tscn"
	if "--formal" in OS.get_cmdline_user_args():scene="res://scenes/units/odyssey/minotaur_breaker/minotaur_breaker_rig.tscn"
	var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://resources/minotaur_breaker_rig_v1.json"))
	var unit=load(scene).instantiate();unit.autoplay=false;root.add_child(unit);unit.set_process(false)
	unit.animation_player.callback_mode_process=AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	var nodes:Dictionary={}
	for bone in data.bones:nodes[bone]=unit.get_node("VisualRoot/Skeleton2D/"+str(data.bones[bone].path))
	var errors:Array=[]
	unit.play_animation("skill_01")
	var hand_error:=0.;var lean_min:=180.;var blade_forward_min:=1e9;var blade_drop_min:=1e9
	for i in 271:
		var t:=.70+i*.01
		if t>3.40:break
		unit.animation_player.seek(t,true)
		var hand:Vector2=nodes.hand_far.global_position
		hand_error=maxf(hand_error,Vector2(394.0,-615.0).distance_to(hand))
		lean_min=minf(lean_min,rad_to_deg(nodes.torso.global_rotation))
		var blade:Vector2=nodes.axe_socket.to_global(Vector2(19,-220))
		blade_forward_min=minf(blade_forward_min,blade.x-nodes.pelvis.global_position.x)
		blade_drop_min=minf(blade_drop_min,blade.y-nodes.pelvis.global_position.y)
		var rest:Array=data.bones.axe_socket.local_position
		if nodes.axe_socket.position.distance_to(Vector2(rest[0],rest[1]))>0.01:errors.append("Axe grip drifted at "+String.num(t,2))
	if hand_error>30.0:errors.append("Far hand left the front-low carry: "+String.num(hand_error,1))
	if lean_min<52.0:errors.append("Charge lean shallower than designed: "+String.num(lean_min,1))
	if blade_forward_min<200.0:errors.append("Axe blade enters the body plane: "+String.num(blade_forward_min,1))
	# Root motion preserved: 2880 source px over the charge.
	unit.play_animation("skill_01")
	for i in 420:unit.animation_player.advance(.01)
	if absf(unit.root_distance-2880.0)>1.0:errors.append("Charge root distance changed")
	var counts:=[0,0]
	var ac:=func():counts[0]+=1
	var sc:=func():counts[1]+=1
	unit.attack_hit.connect(ac);unit.skill_hit.connect(sc)
	unit.play_animation("skill_01")
	for i in 421:unit.animation_player.advance(.01)
	if counts[0]!=0 or counts[1]!=1:errors.append("Skill event counts wrong")
	unit.attack_hit.disconnect(ac);unit.skill_hit.disconnect(sc)
	unit.play_animation("idle");unit.animation_player.advance(0)
	var rest:Array=data.bones.axe_socket.local_position
	if nodes.axe_socket.position.distance_to(Vector2(rest[0],rest[1]))>.001:errors.append("Axe grip failed to reset")
	var result:={"status":"PASS" if errors.is_empty() else "FAIL","scene_sha256":FileAccess.get_sha256(scene),"far_hand_tracking_error_source_px":hand_error,"min_charge_lean_deg":lean_min,"blade_min_forward_offset_source_px":blade_forward_min,"blade_min_drop_source_px":blade_drop_min,"note":"V5: extended forward carry, blade rides above hip by design","root_distance_source_px":2880.0,"skill_hit_count":counts[1],"errors":errors}
	var prefix:="formal_" if "--formal" in OS.get_cmdline_user_args() else ""
	FileAccess.open("res://reports/minotaur_breaker/"+prefix+"skill_v6_test.json",FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	print(JSON.stringify(result));unit.queue_free();quit(0 if errors.is_empty() else 2)
