extends SceneTree
const SCENE := "res://scenes/units/odyssey/roman_centurion/roman_centurion_rig.tscn"
var errors: Array = []
func _initialize() -> void: call_deferred("run")
func check(ok: bool, message: String) -> void:
	if not ok: errors.append(message)
func run() -> void:
	var unit = load(SCENE).instantiate()
	unit.autoplay = false
	unit.root_motion_enabled = false
	root.add_child(unit)
	await process_frame
	unit.set_process(false)
	var player: AnimationPlayer = unit.animation_player
	player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	player.callback_mode_method = AnimationMixer.ANIMATION_CALLBACK_MODE_METHOD_IMMEDIATE
	check(unit.find_children("*","Bone2D",true,false).size()==23,"Bone count")
	check(unit.find_children("*","Sprite2D",true,false).size()==21,"Sprite count")
	check(player.get_animation_list().size()==6,"Animation count")
	for name in player.get_animation_list():
		var animation := player.get_animation(name)
		for i in animation.get_track_count():
			var path := animation.track_get_path(i)
			check(unit.has_node(NodePath(str(path).split(":")[0])),"Invalid track: "+str(path))
		unit.play_animation(name)
		for i in 240: player.advance(animation.length/240.0)
		if name == &"attack_01": check(unit.attack_hit_count==1,"Attack event count")
		if name == &"skill_command": check(unit.command_release_count==1,"Command event count")
		if name == &"death": check(player.assigned_animation==&"death","Death must not recover")
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://resources/roman_centurion_rig_v1.json"))
	var contacts: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://resources/roman_centurion_walk_contacts.json"))
	var max_error := 0.0
	var anchors: Dictionary = {}
	var drift := 0.0
	unit.play_animation("walk")
	for row in contacts.samples:
		player.seek(float(row.time),true)
		unit.position = Vector2(280.0*float(row.time)/1.05,0)
		var bone := unit.get_node("VisualRoot/Skeleton2D/"+data.bones["foot_"+row.side].path) as Bone2D
		var contact := bone.to_global(Vector2(row.contact_local[0],row.contact_local[1]))+Vector2(605,1476)
		var expected := Vector2(row.expected_world_contact[0],row.expected_world_contact[1])
		max_error = maxf(max_error,contact.distance_to(expected))
		if row.support:
			var key := str(row.side)+str(row.support_id)
			if not anchors.has(key): anchors[key] = contact
			drift = maxf(drift,contact.distance_to(anchors[key]))
	check(max_error<1.0,"Walk target FK mismatch")
	check(drift*256.0/1425.0<1.0,"Walk planted material point slide")
	var dense_anchors: Dictionary = {}
	var dense_drift := 0.0
	var samples: Array = []
	for i in 257:
		var phase := i/256.0
		player.seek(phase*1.05,true)
		unit.position = Vector2(phase*280.0,0)
		for side in ["near","far"]:
			var offset := 0.5 if side=="near" else 0.0
			var u := fposmod(phase+offset,1.0)
			if u>=0.6: continue
			var bone := unit.get_node("VisualRoot/Skeleton2D/"+data.bones["foot_"+side].path) as Bone2D
			var point := Vector2(13,123) if side=="near" else Vector2(45,91)
			var contact := bone.to_global(point)+Vector2(605,1476)
			var key: String = str(side)+str(floori(phase+offset))
			if not dense_anchors.has(key): dense_anchors[key]=contact
			dense_drift=maxf(dense_drift,contact.distance_to(dense_anchors[key]))
			samples.append({"phase":phase,"side":side,"support_id":key,"world":[contact.x,contact.y]})
	check(dense_drift*256.0/1425.0<1.0,"Interpolated support-foot slide")
	var debug_file := FileAccess.open("res://reports/roman_centurion/native/walk_foot_contacts.json",FileAccess.WRITE)
	debug_file.store_string(JSON.stringify({"samples":samples,"max_source_drift":dense_drift},"\t"))
	var report := {"status":"PASS" if errors.is_empty() else "FAIL","engine":Engine.get_version_info(),"bones":23,"sprites":21,"native_meshes":10,"animation_count":6,"attack_hit":unit.attack_hit_count,"command_release":unit.command_release_count,"walk_max_source_error":max_error,"walk_max_support_drift_source":drift,"walk_max_support_drift_256px":drift*256.0/1425.0,"interpolated_support_drift_256px":dense_drift*256.0/1425.0,"scene_sha256":FileAccess.get_sha256(SCENE),"errors":errors}
	var file := FileAccess.open("res://reports/roman_centurion/native/headless_tests.json",FileAccess.WRITE)
	file.store_string(JSON.stringify(report,"\t"))
	print(JSON.stringify(report))
	unit.free()
	quit(0 if errors.is_empty() else 2)
