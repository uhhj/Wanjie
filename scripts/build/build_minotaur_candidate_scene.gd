extends SceneTree

func _initialize() -> void: call_deferred("build")
func read_json(path: String) -> Dictionary:
	return JSON.parse_string(FileAccess.get_file_as_string(path))
func vec(v: Array) -> Vector2:return Vector2(float(v[0]),float(v[1]))
func own(node: Node, scene: Node) -> void:
	for child in node.get_children():
		child.owner = scene
		own(child,scene)
func track(a: Animation,path: String,times: Array,values: Array) -> void:
	var index := a.add_track(Animation.TYPE_VALUE)
	a.track_set_path(index,NodePath(path))
	for i in times.size():a.track_insert_key(index,float(times[i]),values[i])

func build() -> void:
	var data := read_json("res://resources/minotaur_breaker_rig_v1.json")
	var manifest := read_json("res://work/minotaur_breaker/candidates/manifest.json")
	assert(manifest.status == "CANDIDATE_ONLY")
	var animations := read_json("res://resources/minotaur_breaker_animation_candidates.json")
	var unit := Node2D.new()
	unit.name = "MinotaurBreakerCandidate"
	unit.set_script(load("res://scripts/rig/minotaur_breaker_rig.gd"))
	unit.set("autoplay",false)
	var visual := Node2D.new()
	visual.name = "VisualRoot"
	unit.add_child(visual)
	var skeleton := load("res://scenes/rigs/biped_large_rig_v1.tscn").instantiate() as Skeleton2D
	skeleton.scene_file_path = ""
	skeleton.position = -vec(data.origin)
	visual.add_child(skeleton)
	for part in manifest.parts:
		var file := "res://" + str(part.file)
		assert(FileAccess.get_sha256(file) == part.sha256)
		var bone_name: String = data.attachments.get(part.name,part.name)
		var record: Dictionary = data.bones[bone_name]
		var sprite := Sprite2D.new()
		sprite.name = "Art_" + str(part.name)
		# Direct PNG loading keeps review candidates outside the imported formal asset set.
		var texture := ImageTexture.create_from_image(Image.load_from_file(file))
		var texture_file := "res://work/minotaur_breaker/candidates/native_parts/"+str(part.name)+".res"
		assert(ResourceSaver.save(texture,texture_file,ResourceSaver.FLAG_COMPRESS)==OK)
		sprite.texture = load(texture_file)
		sprite.centered = false
		sprite.position = -vec(record.pivot)
		var bounds := texture.get_image().get_used_rect()
		sprite.region_enabled = true
		sprite.region_rect = Rect2(bounds)
		sprite.position += Vector2(bounds.position)
		sprite.z_as_relative = true
		sprite.z_index = data.draw_order.find(part.name)*2
		skeleton.get_node(NodePath(record.path)).add_child(sprite)
	var skinning := read_json("res://resources/minotaur_breaker_skinning_candidates.json")
	for record in skinning.meshes:
		var original := unit.find_child("Art_"+str(record.part),true,false) as Sprite2D
		assert(original != null)
		var mesh := Polygon2D.new()
		mesh.name = "Mesh_"+str(record.part)
		mesh.position = -vec(data.origin)
		var vertices := PackedVector2Array()
		for point in record.vertices:vertices.append(vec(point))
		mesh.polygon = vertices
		mesh.uv = vertices
		var triangles: Array = []
		for triangle in record.triangles:triangles.append(PackedInt32Array(triangle))
		mesh.polygons = triangles
		mesh.texture = original.texture
		mesh.skeleton = NodePath("../Skeleton2D")
		for bone in record.weights:mesh.add_bone(NodePath(data.bones[bone].path),PackedFloat32Array(record.weights[bone]))
		mesh.z_as_relative = true
		mesh.z_index = original.z_index
		visual.add_child(mesh)
		original.visible = false
	var player := AnimationPlayer.new()
	player.name = "AnimationPlayer"
	player.callback_mode_method = AnimationMixer.ANIMATION_CALLBACK_MODE_METHOD_IMMEDIATE
	unit.add_child(player)
	var relay := Node.new()
	relay.name = "RigEventRelay"
	relay.set_script(load("res://scripts/rig/minotaur_event_relay.gd"))
	unit.add_child(relay)
	var library := AnimationLibrary.new()
	for name in animations:
		var e: Dictionary = animations[name]
		var a := Animation.new()
		a.length = float(e.length)
		a.loop_mode = Animation.LOOP_LINEAR if e.loop else Animation.LOOP_NONE
		for bone in data.bones:
			var values: Array = []
			for pose in e.poses:values.append(deg_to_rad(float(pose.rotations[bone])))
			track(a,"VisualRoot/Skeleton2D/"+str(data.bones[bone].path)+":rotation",e.times,values)
		for bone in ["arm_near_upper","arm_far_upper"]:
			var positions: Array=[]
			for pose in e.poses:
				positions.append(vec(data.bones[bone].local_position)+vec(pose.get("bone_offsets",{}).get(bone,[0.0,0.0])))
			track(a,"VisualRoot/Skeleton2D/"+str(data.bones[bone].path)+":position",e.times,positions)
		var pelvis: Array = []
		var offsets: Array = []
		var rotations: Array = []
		var distances: Array = []
		for pose in e.poses:
			pelvis.append(vec(data.bones.pelvis.local_position)+vec(pose.pelvis_offset))
			offsets.append(vec(pose.visual_offset))
			rotations.append(deg_to_rad(float(pose.visual_rotation)))
			distances.append(float(pose.root_distance))
		track(a,"VisualRoot/Skeleton2D/pelvis:position",e.times,pelvis)
		track(a,"VisualRoot:position",e.times,offsets)
		track(a,"VisualRoot:rotation",e.times,rotations)
		track(a,".:root_distance",e.times,distances)
		if e.has("method_events"):
			var index := a.add_track(Animation.TYPE_METHOD)
			a.track_set_path(index,NodePath("RigEventRelay"))
			for event in e.method_events:a.track_insert_key(index,float(event.time),{"method":event.method,"args":[]})
		library.add_animation(name,a)
	player.add_animation_library("",library)
	own(unit,unit)
	var packed := PackedScene.new()
	assert(packed.pack(unit)==OK)
	assert(ResourceSaver.save(packed,"res://work/minotaur_breaker/candidates/minotaur_breaker_candidate.tscn")==OK)
	print("MINOTAUR CANDIDATE BUILT: 25 bones, 19 core sprites + 2 knee supports, 6 animations. NOT FORMALLY APPROVED.")
	unit.free()
	quit()
