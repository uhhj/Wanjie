extends SceneTree

func _initialize() -> void:
	call_deferred("build")

func own_tree(node: Node, scene_root: Node) -> void:
	for child in node.get_children():
		child.owner = scene_root
		own_tree(child, scene_root)

func vector(value: Array) -> Vector2:
	return Vector2(float(value[0]), float(value[1]))

func value_track(anim: Animation, path: String, times: Array, values: Array) -> void:
	var track = anim.add_track(Animation.TYPE_VALUE)
	anim.track_set_path(track, NodePath(path))
	anim.value_track_set_update_mode(track, Animation.UPDATE_CONTINUOUS)
	for i in range(times.size()):
		anim.track_insert_key(track, float(times[i]), values[i])

func build() -> void:
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://resources/human_medium_rig_v1.json"))
	var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://tools/roman_guard_parts_manifest.json"))
	var origin = vector(data.origin)
	var unit = Node2D.new()
	unit.name = "RomanGuard"
	unit.set_script(load("res://scripts/rig/roman_guard_rig.gd"))
	unit.autoplay = false
	var visual = Node2D.new()
	visual.name = "VisualRoot"
	unit.add_child(visual)
	var skeleton = load("res://scenes/rigs/human_medium_rig_v1.tscn").instantiate()
	# Bake a single owned copy from the generic rig; do not duplicate inherited nodes.
	skeleton.scene_file_path = ""
	skeleton.name = "Skeleton2D"
	skeleton.position = -origin
	visual.add_child(skeleton)
	var attach = {"head":"head", "helmet":"head", "torso":"torso", "pelvis":"pelvis", "sword":"sword_socket", "shield":"shield_socket", "cape_back":"cape_root", "cape_front":"torso"}
	for draw in manifest.draw_passes:
		var name: String = draw.part
		if name == "leg_near_shin":
			continue
		var key = name
		if name == "cape":
			key = "cape_back" if "back" in draw.clip_mask else "cape_front"
		var bone_name: String = attach.get(key, name)
		var bone = skeleton.get_node(data.bones[bone_name].path)
		var sprite = Sprite2D.new()
		sprite.name = "Art_" + key
		sprite.texture = load("res://assets/units/odyssey/roman_guard/parts/" + name + ".png")
		sprite.centered = false
		sprite.position = -vector(data.bones[bone_name].pivot)
		if name == "cape":
			var material = ShaderMaterial.new()
			material.shader = load("res://scripts/rig/mask_clip.gdshader")
			material.set_shader_parameter("clip_mask", load("res://resources/masks/" + key + "_region.png"))
			sprite.material = material
		bone.add_child(sprite)
	var mesh: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/units/odyssey/roman_guard/near_knee_skinning_v1.json"))
	var polygon = Polygon2D.new()
	polygon.name = "Art_leg_near_shin"
	polygon.position = -origin
	var vertices = PackedVector2Array()
	for p in mesh.vertices:
		vertices.append(vector(p))
	polygon.polygon = vertices
	polygon.uv = vertices
	var triangles: Array = []
	for t in mesh.triangles:
		triangles.append(PackedInt32Array(t))
	polygon.polygons = triangles
	polygon.texture = load("res://assets/units/odyssey/roman_guard/parts/leg_near_shin.png")
	polygon.skeleton = NodePath("../Skeleton2D")
	polygon.add_bone(NodePath(data.bones.knee_near.path), PackedFloat32Array(mesh.stationary_socket_weights))
	polygon.add_bone(NodePath(data.bones.leg_near_shin.path), PackedFloat32Array(mesh.shin_weights))
	visual.add_child(polygon)
	for part in ["arm_near_upper","arm_far_upper","foot_far"]:
		var local_mesh: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://resources/"+part+"_local_skinning.json"))
		var skin = Polygon2D.new()
		skin.name = "Art_"+part+"_skinned"
		skin.position = -origin
		var points = PackedVector2Array()
		for p in local_mesh.vertices:
			points.append(vector(p))
		skin.polygon = points
		var source_uv = PackedVector2Array()
		for p in local_mesh.uv:
			source_uv.append(vector(p))
		skin.uv = source_uv
		var faces: Array = []
		for triangle in local_mesh.triangles:
			faces.append(PackedInt32Array(triangle))
		skin.polygons = faces
		skin.texture = load("res://"+local_mesh.texture_file)
		skin.skeleton = NodePath("../Skeleton2D")
		skin.add_bone(NodePath(data.bones[local_mesh.stationary_bone].path),PackedFloat32Array(local_mesh.stationary_weights))
		skin.add_bone(NodePath(data.bones[local_mesh.moving_bone].path),PackedFloat32Array(local_mesh.moving_weights))
		skin.visible = false
		visual.add_child(skin)
	var player = AnimationPlayer.new()
	player.name = "AnimationPlayer"
	player.callback_mode_method = AnimationMixer.ANIMATION_CALLBACK_MODE_METHOD_IMMEDIATE
	unit.add_child(player)
	var relay = Node.new()
	relay.name = "RigEventRelay"
	relay.set_script(load("res://scripts/rig/rig_event_relay.gd"))
	unit.add_child(relay)
	var blood = Node2D.new()
	blood.name = "DeathBlood"
	blood.set_script(load("res://scripts/rig/death_blood.gd"))
	unit.add_child(blood)
	var ground = Marker2D.new()
	ground.name = "GroundMarker"
	unit.add_child(ground)
	var debug = Node2D.new()
	debug.name = "DebugRoot"
	debug.set_script(load("res://scripts/rig/rig_debug.gd"))
	debug.visible = false
	unit.add_child(debug)
	var animations: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://resources/roman_guard_animations_v1.json"))
	var library = AnimationLibrary.new()
	for animation_name in animations:
		var entry: Dictionary = animations[animation_name]
		var anim = Animation.new()
		anim.resource_name = animation_name
		anim.length = float(entry.length)
		anim.loop_mode = Animation.LOOP_LINEAR if entry.loop else Animation.LOOP_NONE
		var times: Array = entry.times
		for bone_name in data.bones:
			var values: Array = []
			for pose in entry.poses:
				values.append(deg_to_rad(float(pose.rotations[bone_name])))
			value_track(anim,"VisualRoot/Skeleton2D/" + data.bones[bone_name].path + ":rotation", times, values)
		var positions: Array = []
		var visual_rotations: Array = []
		var visual_positions: Array = []
		var helmet_rotations: Array = []
		for pose in entry.poses:
			positions.append(vector(data.bones.pelvis.local_position) + vector(pose.pelvis_offset))
			visual_rotations.append(deg_to_rad(float(pose.visual_rotation)))
			visual_positions.append(vector(pose.visual_offset))
			helmet_rotations.append(deg_to_rad(float(pose.helmet_rotation)))
		value_track(anim,"VisualRoot/Skeleton2D/pelvis:position",times,positions)
		var shoulder_positions: Array = []
		for pose in entry.poses:
			shoulder_positions.append(vector(data.bones.arm_near_upper.local_position)+vector(pose.shoulder_offset))
		value_track(anim,"VisualRoot/Skeleton2D/"+data.bones.arm_near_upper.path+":position",times,shoulder_positions)
		for part in ["arm_near_upper","arm_far_upper","foot_far"]:
			var use_skin: bool = animation_name=="walk" or (animation_name=="attack_01" and part!="foot_far")
			value_track(anim,"VisualRoot/Art_"+part+"_skinned:visible",[0.0],[use_skin])
			anim.value_track_set_update_mode(anim.get_track_count()-1,Animation.UPDATE_DISCRETE)
			value_track(anim,"VisualRoot/Skeleton2D/"+data.bones[part].path+"/Art_"+part+":visible",[0.0],[not use_skin])
			anim.value_track_set_update_mode(anim.get_track_count()-1,Animation.UPDATE_DISCRETE)
		for side in ["near","far"]:
			var hip_positions: Array = []
			var bone_name = "leg_"+side+"_thigh"
			for pose in entry.poses:
				hip_positions.append(vector(data.bones[bone_name].local_position)+vector(pose.hip_offsets[side]))
			value_track(anim,"VisualRoot/Skeleton2D/"+data.bones[bone_name].path+":position",times,hip_positions)
		value_track(anim,"VisualRoot:rotation",times,visual_rotations)
		value_track(anim,"VisualRoot:position",times,visual_positions)
		value_track(anim,"DeathBlood:phase",[0.0,0.12,0.65,1.1] if animation_name=="death" else [0.0],[-1.0,0.0,1.0,1.0] if animation_name=="death" else [-1.0])
		value_track(anim,"VisualRoot/Skeleton2D/"+data.bones.head.path+"/Art_helmet:rotation",times,helmet_rotations)
		if entry.has("method_events"):
			var idx = anim.add_track(Animation.TYPE_METHOD)
			anim.track_set_path(idx,NodePath("RigEventRelay"))
			for event in entry.method_events:
				anim.track_insert_key(idx,event.time,{"method":event.method,"args":[]})
		library.add_animation(animation_name,anim)
	ResourceSaver.save(library,"res://resources/roman_guard_animations_v1.tres")
	player.add_animation_library("",library)
	own_tree(unit,unit)
	unit.autoplay = true
	var packed = PackedScene.new()
	assert(packed.pack(unit)==OK)
	assert(ResourceSaver.save(packed,"res://scenes/units/odyssey/roman_guard/roman_guard_rig.tscn")==OK)
	unit.free()
	print("BUILT: native 23-bone rig, 20 Sprite2D + 4 weighted Polygon2D (mode-specific draws); 5 animations")
	quit()
