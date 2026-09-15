extends SceneTree
var errors: Array = []

func check(condition: bool, message: String) -> void:
	if not condition:
		errors.append(message)
		push_error(message)

# Measured frozen shoe lower profile; validate whichever material point touches
# the floor while the foot rolls, rather than treating a raised heel as sliding.
const SOLE = [Vector2(-65,104),Vector2(-15,120),Vector2(32,127),Vector2(78,123),Vector2(106,116)]
func contact_index(foot: Bone2D) -> int:
	var index := 0
	for i in range(1,SOLE.size()):
		if foot.to_global(SOLE[i]).y>foot.to_global(SOLE[index]).y:
			index = i
	return index

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var unit = load("res://scenes/units/odyssey/roman_guard/roman_guard_rig.tscn").instantiate()
	unit.autoplay = false
	unit.root_motion_enabled = false
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
	var attack_foot_drift := 0.0
	unit.play_animation("attack_01")
	var foot_anchors: Dictionary = {}
	for side in ["near","far"]:
		var foot: Bone2D = unit.get_node("VisualRoot/Skeleton2D/"+data.bones["foot_"+side].path)
		foot_anchors[side] = foot.to_global(Vector2(0,100))
	for frame in range(241):
		player.seek(player.get_animation("attack_01").length*frame/240.0,true)
		for side in ["near","far"]:
			var foot: Bone2D = unit.get_node("VisualRoot/Skeleton2D/"+data.bones["foot_"+side].path)
			attack_foot_drift=maxf(attack_foot_drift,foot.to_global(Vector2(0,100)).distance_to(foot_anchors[side]))
	check(attack_foot_drift*256.0/float(data.body_height)<1.0,"Attack planted sole drift")
	var sword_drift := 0.0
	unit.play_animation("attack_01")
	for i in range(81):
		player.seek(player.get_animation("attack_01").length*i/80.0,true)
		var hand = unit.get_node("VisualRoot/Skeleton2D/"+data.bones.hand_near.path) as Bone2D
		var sword = unit.find_child("Art_sword",true,false) as Sprite2D
		sword_drift = max(sword_drift,hand.to_global(Vector2(-1,32)).distance_to(sword.to_global(Vector2(328,867))))
	check(sword_drift<0.001,"Sword disconnected from grip")
	var polygon = unit.find_child("Art_leg_near_shin",true,false) as Polygon2D
	check(polygon.get_bone_count()==2,"Near shin must use actual two-bone Polygon2D binding")
	check(unit.find_children("*","Polygon2D",true,false).size()==4,"Near knee, two shoulders and far ankle must have four native meshes")
	for part in ["arm_near_upper","arm_far_upper"]:
		check(unit.find_child("Art_"+part+"_skinned",true,false).visible,"Attack shoulder skin must be active")
	unit.rest_pose()
	for sprite in unit.find_children("*","Sprite2D",true,false):
		check(sprite.global_position.distance_to(Vector2(-530,-1460))<0.001,"Rest sprite offset mismatch: "+str(sprite.name))
	unit.play_animation("attack_01")
	for i in range(int(ceil(player.get_animation("attack_01").length*120))+15):
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
	player.seek(.3,true)
	check(unit.get_node("DeathBlood").phase > 0.0 and unit.get_node("DeathBlood").phase < 1.0,"Death blood accent must be active mid-burst")
	print("BLOOD phase=",unit.get_node("DeathBlood").phase," z=",unit.get_node("DeathBlood").z_index)
	unit.play_animation("death")
	player.advance(1.2)
	check(player.assigned_animation==&"death" and not player.is_playing(),"Death must stop and hold")
	var foot_rows: Array = []
	unit.play_animation("walk")
	for i in range(121):
		var t = i/120.0
		player.seek(t,true)
		unit.position.x = unit.walk_stride*t
		for side in ["near","far"]:
			var foot: Bone2D = unit.get_node("VisualRoot/Skeleton2D/"+data.bones["foot_"+side].path)
			var support = t<.5 if side=="near" else t>=.5 and t<1.0
			var contact := contact_index(foot)
			var point = foot.to_global(SOLE[contact])
			foot_rows.append({"time":t,"side":side,"support":support,"contact_index":contact,"world_position":[point.x,point.y]})
	var maxima: Dictionary = {}
	for side in ["near","far"]:
		var anchors: Dictionary = {}
		var maximum := 0.0
		var floor_min := INF
		var floor_max := -INF
		for row in foot_rows:
			if row.side==side and row.support:
				var point := Vector2(row.world_position[0],row.world_position[1])
				if not anchors.has(row.contact_index):
					anchors[row.contact_index] = point
				maximum = maxf(maximum,point.distance_to(anchors[row.contact_index]))
				floor_min = minf(floor_min,point.y)
				floor_max = maxf(floor_max,point.y)
		check((floor_max-floor_min)*256.0/float(data.body_height)<1.0,"Rolling foot must stay on floor: "+side)
		maxima[side] = {"source_pixels":maximum,"at_256px":maximum*256.0/float(data.body_height),"floor_height_range_source_px":floor_max-floor_min,"contact_regions_tested":anchors.size()}
		check(maxima[side].at_256px<1.0,"FAIL_WALK_FOOT_SLIDE: "+side)
	# Exercise the actual runtime root-motion consumer across two loop boundaries,
	# independently of the direct-seek pose measurements above.
	unit.position = Vector2.ZERO
	unit.root_motion_enabled = true
	unit.play_animation("walk")
	var runtime_max := 0.0
	var planted: Dictionary = {}
	for i in range(240):
		player.advance(1.0/120.0)
		unit._process(1.0/120.0)
		var t := (i+1)/120.0
		var phase := fmod(t,1.0)
		var side := "near" if phase < .5 else "far"
		# Exclude the instant of contact exchange from the previous support block.
		if is_zero_approx(fmod(t,.5)):
			continue
		var foot: Bone2D = unit.get_node("VisualRoot/Skeleton2D/"+data.bones["foot_"+side].path)
		var contact := contact_index(foot)
		var key := str(int(t*2.0))+":"+str(contact)
		var point := foot.to_global(SOLE[contact])
		if not planted.has(key):
			planted[key] = point
		runtime_max = maxf(runtime_max,point.distance_to(planted[key]))
	check(absf(unit.position.x-2.0*unit.walk_stride)<0.01,"Root motion lost distance across walk loop")
	check(runtime_max*256.0/float(data.body_height)<1.0,"Runtime planted foot drift")
	player.pause()
	var paused_position: Vector2 = unit.position
	unit._process(.5)
	check(unit.position==paused_position,"Paused walk must not translate")
	var file = FileAccess.open("res://reports/native_rig_v2/headless_tests.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"status":"PASS" if errors.is_empty() else "FAIL","engine":Engine.get_version_info(),"errors":errors,"bone_count":23,"sprite_count":unit.find_children("*","Sprite2D",true,false).size(),"polygon_count":unit.find_children("*","Polygon2D",true,false).size(),"animation_tracks":track_count,"attack_hit_count":unit.attack_hit_count,"attack_planted_sole_drift_at_256px":attack_foot_drift*256.0/float(data.body_height),"sword_grip_max_drift_source_px":sword_drift,"runtime_walk_distance_two_cycles":unit.position.x,"runtime_support_drift_at_256px":runtime_max*256.0/float(data.body_height),"foot_contact_method":"Material contact points on frozen shoe lower profile; every support region locked, floor height independently checked","foot_slide":maxima,"foot_samples":foot_rows},"\t"))
	print("NATIVE_TESTS ","PASS" if errors.is_empty() else "FAIL", " event=",unit.attack_hit_count," foot=",maxima)
	unit.free()
	quit(0 if errors.is_empty() else 2)
