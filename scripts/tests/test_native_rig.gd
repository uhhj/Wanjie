extends SceneTree
var errors: Array = []

func check(condition: bool, message: String) -> void:
	if not condition:
		errors.append(message)
		push_error(message)

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var unit = load("res://scenes/units/odyssey/roman_guard/roman_guard_rig.tscn").instantiate()
	unit.autoplay = false
	root.add_child(unit)
	await process_frame
	var player: AnimationPlayer = unit.animation_player
	player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://resources/human_medium_rig_v1.json"))
	check(Engine.get_version_info().string.begins_with("4.7.2-stable"),"Exact engine version mismatch")
	check(player.get_animation_list().size()==5,"Exactly five animations required")
	check(unit.find_children("*","Bone2D",true,false).size()==23,"23 native Bone2D nodes expected")
	var track_count := 0
	var event_count := 0
	for name in player.get_animation_list():
		var anim = player.get_animation(name)
		for i in range(anim.get_track_count()):
			var path = anim.track_get_path(i)
			check(unit.has_node(NodePath(path.get_concatenated_names())),"Invalid track node: "+str(path))
			if anim.track_get_type(i)==Animation.TYPE_METHOD:
				event_count += anim.track_get_key_count(i)
				check(name==&"attack_01","Unexpected method event")
			track_count += 1
	check(event_count==1,"Attack must contain exactly one method key")
	var polygon = unit.find_child("Art_leg_near_shin",true,false) as Polygon2D
	check(polygon.get_bone_count()==2,"Near shin must use actual two-bone Polygon2D binding")
	unit.rest_pose()
	for sprite in unit.find_children("*","Sprite2D",true,false):
		check(sprite.global_position.distance_to(Vector2(-530,-1460))<0.001,"Rest sprite offset mismatch: "+str(sprite.name))
	unit.play_animation("attack_01")
	for i in range(110):
		player.advance(1.0/120.0)
	check(unit.attack_hit_count==1,"attack_hit emitted "+str(unit.attack_hit_count)+" times")
	check(player.current_animation==&"idle","Attack must return to idle")
	unit.play_animation("hit")
	player.advance(.4)
	check(player.current_animation==&"idle","Hit must return to idle")
	unit.play_animation("walk")
	player.advance(.25)
	unit.play_animation("idle")
	check(player.current_animation==&"idle","walk -> idle transition failed")
	unit.play_animation("death")
	player.advance(1.2)
	check(player.assigned_animation==&"death" and not player.is_playing(),"Death must stop and hold")
	var foot_rows: Array = []
	unit.play_animation("walk")
	for i in range(121):
		var t = i/120.0
		player.seek(t,true)
		for side in ["near","far"]:
			var foot: Bone2D = unit.get_node("VisualRoot/Skeleton2D/"+data.bones["foot_"+side].path)
			var support = t<.5 if side=="near" else t>=.5 and t<1.0
			var point = foot.to_global(Vector2(33,119) if side=="near" else Vector2(60,99))
			foot_rows.append({"time":t,"side":side,"support":support,"world_position":[point.x,point.y]})
	var maxima: Dictionary = {}
	for side in ["near","far"]:
		var positions: Array = []
		for row in foot_rows:
			if row.side==side and row.support:
				positions.append(Vector2(row.world_position[0],row.world_position[1]))
		var maximum := 0.0
		for p in positions:
			maximum = max(maximum,p.distance_to(positions[0]))
		maxima[side] = {"source_pixels":maximum,"at_256px":maximum*256.0/float(data.body_height)}
		check(maxima[side].at_256px<1.0,"FAIL_WALK_FOOT_SLIDE: "+side)
	var file = FileAccess.open("res://reports/native_rig_v2/headless_tests.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"status":"PASS" if errors.is_empty() else "FAIL","engine":Engine.get_version_info(),"errors":errors,"bone_count":23,"sprite_count":unit.find_children("*","Sprite2D",true,false).size(),"polygon_count":1,"animation_tracks":track_count,"attack_hit_count":unit.attack_hit_count,"foot_slide":maxima,"foot_samples":foot_rows},"\t"))
	print("NATIVE_TESTS ","PASS" if errors.is_empty() else "FAIL", " event=",unit.attack_hit_count," foot=",maxima)
	unit.free()
	quit(0 if errors.is_empty() else 2)
