extends SceneTree
const DATA := "res://resources/roman_centurion_rig_v1.json"
const ANIMS := "res://resources/roman_centurion_animations_v1.json"
const OUT := "res://scenes/units/odyssey/roman_centurion/roman_centurion_rig.tscn"
func _initialize() -> void: call_deferred("build")
func read_json(path: String) -> Dictionary: return JSON.parse_string(FileAccess.get_file_as_string(path))
func vec(a: Array) -> Vector2: return Vector2(float(a[0]),float(a[1]))
func own(node: Node, unit: Node) -> void:
	for c in node.get_children():
		c.owner = unit
		own(c,unit)
func track(a: Animation, path: String, times: Array, values: Array) -> void:
	var i := a.add_track(Animation.TYPE_VALUE)
	a.track_set_path(i,NodePath(path))
	for k in times.size(): a.track_insert_key(i,float(times[k]),values[k])
func build() -> void:
	var manifest := read_json("res://tools/roman_centurion_parts_manifest.json")
	assert(manifest.status == "PASS")
	var data := read_json(DATA)
	var animations := read_json(ANIMS)
	var unit := Node2D.new()
	unit.name = "RomanCenturion"
	unit.set_script(load("res://scripts/rig/roman_centurion_rig.gd"))
	var visual := Node2D.new()
	visual.name = "VisualRoot"
	unit.add_child(visual)
	var skeleton := load("res://scenes/rigs/human_medium_rig_v1.tscn").instantiate() as Skeleton2D
	skeleton.scene_file_path = ""
	skeleton.position = -vec(data.origin)
	visual.add_child(skeleton)
	for n in data.bones:
		var rec: Dictionary = data.bones[n]
		var bone := skeleton.get_node(NodePath(rec.path)) as Bone2D
		bone.position = vec(rec.local_position)
		bone.rest = Transform2D(0.0,bone.position)
		bone.rotation = 0.0
		bone.set_autocalculate_length_and_angle(false)
		bone.length = float(rec.length)
		bone.bone_angle = float(rec.bone_angle)
	for e in manifest.parts:
		var path: String = "res://" + str(e.file)
		assert(e.status == "PASS" and FileAccess.get_sha256(path) == e.sha256)
		var attach: String = data.attachments[e.name]
		var bone := skeleton.get_node(NodePath(data.bones[attach].path)) as Bone2D
		var sprite := Sprite2D.new()
		sprite.name = "Art_" + str(e.name)
		sprite.texture = load(path)
		assert(sprite.texture != null)
		sprite.centered = false
		sprite.position = -vec(data.bones[attach].pivot)
		sprite.z_as_relative = false
		sprite.z_index = data.draw_order.find(e.name)*2
		bone.add_child(sprite)
	var skin: Dictionary = read_json("res://resources/roman_centurion_local_skinning.json")
	assert(skin.rig_sha256==FileAccess.get_sha256(DATA))
	for rec in skin.meshes:
		var mesh := Polygon2D.new()
		mesh.name = "Art_"+str(rec.part)+"_skinned"
		mesh.position = -vec(data.origin)
		var vertices := PackedVector2Array()
		for point in rec.vertices: vertices.append(vec(point))
		mesh.polygon = vertices
		mesh.uv = vertices
		var triangles: Array = []
		for triangle in rec.triangles: triangles.append(PackedInt32Array(triangle))
		mesh.polygons = triangles
		var path: String = "res://assets/units/odyssey/roman_centurion/parts/"+str(rec.part)+".png"
		assert(FileAccess.get_sha256(path)==rec.texture_sha256)
		mesh.texture = load(path)
		mesh.skeleton = NodePath("../Skeleton2D")
		mesh.add_bone(NodePath(data.bones[rec.stationary_bone].path),PackedFloat32Array(rec.stationary_weights))
		mesh.add_bone(NodePath(data.bones[rec.moving_bone].path),PackedFloat32Array(rec.moving_weights))
		mesh.z_as_relative = false
		mesh.z_index = data.draw_order.find(rec.part)*2
		visual.add_child(mesh)
		unit.find_child("Art_"+str(rec.part),true,false).visible = false
	var relay := Node.new()
	relay.name = "RigEventRelay"
	relay.set_script(load("res://scripts/rig/centurion_event_relay.gd"))
	unit.add_child(relay)
	var player := AnimationPlayer.new()
	player.name = "AnimationPlayer"
	unit.add_child(player)
	var library := AnimationLibrary.new()
	for name in animations:
		var entry: Dictionary = animations[name]
		var anim := Animation.new()
		anim.length = float(entry.length)
		anim.loop_mode = Animation.LOOP_LINEAR if entry.loop else Animation.LOOP_NONE
		for n in data.bones:
			var rotations: Array = []
			var positions: Array = []
			var scales: Array = []
			for pose in entry.poses:
				rotations.append(deg_to_rad(float(pose.rotations[n])))
				var pos := vec(data.bones[n].local_position)
				if n == "pelvis": pos += vec(pose.pelvis_offset)
				if n == "leg_near_thigh": pos += vec(pose.hip_offsets.near)
				if n == "leg_far_thigh": pos += vec(pose.hip_offsets.far)
				positions.append(pos)
				scales.append(vec(pose.get("bone_scales",{}).get(n,[1.0,1.0])))
			track(anim,"VisualRoot/Skeleton2D/"+data.bones[n].path+":rotation",entry.times,rotations)
			track(anim,"VisualRoot/Skeleton2D/"+data.bones[n].path+":position",entry.times,positions)
			track(anim,"VisualRoot/Skeleton2D/"+data.bones[n].path+":scale",entry.times,scales)
		var offsets: Array = []
		var rolls: Array = []
		for pose in entry.poses:
			offsets.append(vec(pose.visual_offset))
			rolls.append(deg_to_rad(float(pose.visual_rotation)))
		track(anim,"VisualRoot:position",entry.times,offsets)
		track(anim,"VisualRoot:rotation",entry.times,rolls)
		if entry.has("method_events"):
			var index := anim.add_track(Animation.TYPE_METHOD)
			anim.track_set_path(index,NodePath("RigEventRelay"))
			for event in entry.method_events: anim.track_insert_key(index,float(event.time),{"method":event.method,"args":[]})
		library.add_animation(name,anim)
	player.add_animation_library("",library)
	own(unit,unit)
	var packed := PackedScene.new()
	assert(packed.pack(unit)==OK)
	assert(ResourceSaver.save(packed,OUT)==OK)
	print("CENTURION_NATIVE_BUILT bones=",data.bones.size()," sprites=",manifest.parts.size()," animations=",animations.size())
	unit.free()
	quit()
