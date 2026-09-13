extends SceneTree

func _initialize() -> void:
	call_deferred("capture")

func capture() -> void:
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://resources/human_medium_rig_v1.json"))
	var viewports: Array = []
	var units: Array = []
	var cameras: Array = []
	var chain := "--walk-chain-v2" in OS.get_cmdline_user_args() or "--walk-chain-v2-follow" in OS.get_cmdline_user_args()
	var follow := "--walk-chain-v2-follow" in OS.get_cmdline_user_args()
	var heights = [256,192]
	for height in heights:
		var viewport = SubViewport.new()
		viewport.size = Vector2i(512,420)
		viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		root.add_child(viewport)
		var background = ColorRect.new()
		background.color = Color(0.86,0.87,0.88)
		background.size = Vector2(512,420)
		viewport.add_child(background)
		var unit = load("res://scenes/units/odyssey/roman_guard/roman_guard_rig.tscn").instantiate()
		unit.autoplay = false
		unit.root_motion_enabled = false
		unit.position = Vector2(300,306)
		unit.scale = Vector2.ONE * height / float(data.body_height)
		viewport.add_child(unit)
		if follow:
			var ground = Line2D.new()
			ground.points = PackedVector2Array([Vector2(-512,306),Vector2(1536,306)])
			ground.width = 1.0
			ground.default_color = Color(.66,.68,.70)
			viewport.add_child(ground)
			var spacing: float = unit.walk_stride*unit.scale.x/2.0
			for tick in range(-20,45):
				var marker = Line2D.new()
				marker.points = PackedVector2Array([Vector2(tick*spacing,307),Vector2(tick*spacing,311)])
				marker.width = 1.0
				marker.default_color = Color(.72,.74,.76)
				viewport.add_child(marker)
			var camera = Camera2D.new()
			camera.position = Vector2(256,210)
			viewport.add_child(camera)
			cameras.append(camera)
			background.position.x = -512
			background.size.x = 2048
		unit.animation_player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
		viewports.append(viewport)
		units.append(unit)
	await process_frame
	await RenderingServer.frame_post_draw
	if "--cape-trial" in OS.get_cmdline_user_args():
		for angle in [-10,-20,-30,-40,-50]:
			for unit in units:
				unit.play_animation("attack_01")
				unit.animation_player.seek(.5,true)
				unit.get_node("VisualRoot/Skeleton2D/"+data.bones.cape_root.path).rotation = deg_to_rad(angle)
			await process_frame
			await RenderingServer.frame_post_draw
			viewports[0].get_texture().get_image().save_png("res://reports/native_rig_v2/cape_trial_%d.png" % angle)
		for viewport in viewports:
			viewport.free()
		quit()
		return
	var records: Array = []
	var walk_folder := "reports/walk_chain_v2"
	if follow:
		walk_folder += "/follow"
	var walk_only := chain
	var names: Array = ["walk"] if walk_only else ["rest_pose","idle","walk","attack_01","hit","death"]
	for name in names:
		var length = 0.0 if name=="rest_pose" else units[0].animation_player.get_animation(name).length
		var frame_count = 16 if walk_only else (1 if name=="rest_pose" else int(ceil(length*15))+1)
		for frame in range(frame_count):
			var time = length*frame/(frame_count if walk_only else max(1,frame_count-1))
			for unit in units:
				unit.position.x = (320.0 if name=="death" else 240.0) + (unit.walk_stride*time*unit.scale.x if name=="walk" else 0.0)
				if name=="rest_pose":
					unit.rest_pose()
				else:
					unit.play_animation(name)
					unit.animation_player.seek(time,true)
			if follow:
				for index in range(cameras.size()):
					cameras[index].position.x = 256+units[index].walk_stride*time*units[index].scale.x
			await process_frame
			await RenderingServer.frame_post_draw
			for index in range(heights.size()):
				var folder = walk_folder if walk_only else "reports/animations"
				var path = "res://%s/%s_%d_%03d.png" % [folder,name,heights[index],frame]
				var result = viewports[index].get_texture().get_image().save_png(path)
				assert(result==OK)
				records.append({"animation":name,"height":heights[index],"time":time,"frame":frame,"path":path})
		print("CAPTURED ",name," ",frame_count," frames at each scale")
	var file = FileAccess.open("res://"+walk_folder+"/capture_manifest.json" if walk_only else "res://reports/native_rig_v2/capture_manifest.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"engine":Engine.get_version_info(),"renderer":RenderingServer.get_video_adapter_name(),"source":"Actual Godot SubViewport GPU renders, no Python reconstruction","body_height_source":data.body_height,"frames":records},"\t"))
	for viewport in viewports:
		viewport.free()
	quit()
