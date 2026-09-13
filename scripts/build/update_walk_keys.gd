extends SceneTree
## Export just the revised Walk resource; no rig/other-animation serialization.
func _initialize() -> void:
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://resources/human_medium_rig_v1.json"))
	var entry: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://resources/roman_guard_animations_v1.json")).walk
	var library: AnimationLibrary = load("res://resources/roman_guard_animations_v1.tres")
	var walk: Animation = library.get_animation("walk").duplicate(true)
	var values: Dictionary = {}
	for bone in data.bones:
		var prefix: String = "VisualRoot/Skeleton2D/"+data.bones[bone].path
		values[prefix+":rotation"] = []
		for pose in entry.poses:
			values[prefix+":rotation"].append(deg_to_rad(float(pose.rotations[bone])))
	for key in ["VisualRoot/Skeleton2D/pelvis:position","VisualRoot:rotation","VisualRoot:position","VisualRoot/Skeleton2D/"+data.bones.head.path+"/Art_helmet:rotation","VisualRoot/Skeleton2D/"+data.bones.arm_near_upper.path+":position"]:
		values[key] = []
	for side in ["near","far"]:
		values["VisualRoot/Skeleton2D/"+data.bones["leg_"+side+"_thigh"].path+":position"] = []
	for pose in entry.poses:
		values["VisualRoot/Skeleton2D/pelvis:position"].append(vec(data.bones.pelvis.local_position)+vec(pose.pelvis_offset))
		values["VisualRoot:rotation"].append(deg_to_rad(float(pose.visual_rotation)))
		values["VisualRoot:position"].append(vec(pose.visual_offset))
		values["VisualRoot/Skeleton2D/"+data.bones.head.path+"/Art_helmet:rotation"].append(deg_to_rad(float(pose.helmet_rotation)))
		values["VisualRoot/Skeleton2D/"+data.bones.arm_near_upper.path+":position"].append(vec(data.bones.arm_near_upper.local_position)+vec(pose.shoulder_offset))
		for side in ["near","far"]:
			values["VisualRoot/Skeleton2D/"+data.bones["leg_"+side+"_thigh"].path+":position"].append(vec(data.bones["leg_"+side+"_thigh"].local_position)+vec(pose.hip_offsets[side]))
	for track in range(walk.get_track_count()):
		var path := str(walk.track_get_path(track))
		if not values.has(path):
			continue
		assert(walk.track_get_key_count(track)==entry.times.size())
		for i in range(entry.times.size()):
			walk.track_set_key_value(track,i,values[path][i])
	var output = "res://reports/walk_reference_v1/walk_animation.tres" if "--walk-reference" in OS.get_cmdline_user_args() else "res://reports/walk_polish_v1/walk_animation.tres"
	assert(ResourceSaver.save(walk,output)==OK)
	print("WALK KEY VALUES EXPORTED; existing tracks and all other animations retained")
	quit()

func vec(a: Array) -> Vector2:
	return Vector2(float(a[0]),float(a[1]))
