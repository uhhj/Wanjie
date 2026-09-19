extends SceneTree
## Skill V3 candidate checks: pommel grip keeps the axe outside the body during
## the charge, deeper lean, single skill event, socket reset. Visual approval separate.
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
	# Charge window: hand holds the pommel end, axe trails behind, torso leans 56 degrees.
	var hand_error:=0.;var lean_min:=180.;var blade_forward_max:=-1e9
	for i in 271:
		var t:=.70+i*.01
		if t>3.40:break
		unit.animation_player.seek(t,true)
		var hand:Vector2=nodes.hand_far.global_position
		hand_error=maxf(hand_error,Vector2(-86.0,-625.0).distance_to(hand))
		lean_min=minf(lean_min,rad_to_deg(nodes.torso.global_rotation))
		var blade:Vector2=nodes.axe_socket.to_global(Vector2(19,-220))
		blade_forward_max=maxf(blade_forward_max,blade.x-nodes.pelvis.global_position.x)
		var rest:Array=data.bones.axe_socket.local_position
		if absf(nodes.axe_socket.position.y-(rest[1]-455.0))>1.0:errors.append("Pommel slide lost at "+String.num(t,2))
	if hand_error>30.0:errors.append("Far hand left the trailing pommel grip: "+String.num(hand_error,1))
	if lean_min<52.0:errors.append("Charge lean shallower than designed: "+String.num(lean_min,1))
	if blade_forward_max>-250.0:errors.append("Axe blade crosses the body plane during charge")
	# Root motion preserved: 2880 source px over the charge.
	unit.play_animation("skill_01");var travelled:=0.
	for i in 420:
		unit.animation_player.advance(.01);travelled=unit.root_distance
	if absf(travelled-2880.0)>1.0:errors.append("Charge root distance changed")
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
	if nodes.axe_socket.position.distance_to(Vector2(rest[0],rest[1]))>.001:errors.append("Axe slide failed to reset")
	var result:={"status":"PASS" if errors.is_empty() else "FAIL","scene_sha256":FileAccess.get_sha256(scene),"far_hand_tracking_error_source_px":hand_error,"min_charge_lean_deg":lean_min,"blade_max_forward_offset_source_px":blade_forward_max,"root_distance_source_px":travelled,"skill_hit_count":counts[1],"errors":errors}
	var prefix:="formal_" if "--formal" in OS.get_cmdline_user_args() else ""
	FileAccess.open("res://reports/minotaur_breaker/"+prefix+"skill_v3_test.json",FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	print(JSON.stringify(result));unit.queue_free();quit(0 if errors.is_empty() else 2)
