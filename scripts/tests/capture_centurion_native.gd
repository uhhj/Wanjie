extends SceneTree
const SCENE := "res://scenes/units/odyssey/roman_centurion/roman_centurion_rig.tscn"
const FOLDER := "res://reports/roman_centurion/native/frames"
func _initialize() -> void: call_deferred("capture")
func capture() -> void:
	assert(DisplayServer.get_name()!="headless","Actual GPU rendering required")
	var records: Array = []
	for height in [256,192]:
		var viewport := SubViewport.new()
		viewport.size = Vector2i(700,520)
		viewport.transparent_bg = true
		viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		root.add_child(viewport)
		var unit = load(SCENE).instantiate()
		unit.autoplay = false
		unit.root_motion_enabled = false
		unit.scale = Vector2.ONE*height/1425.0
		unit.position = Vector2(270,420)
		viewport.add_child(unit)
		unit.set_process(false)
		unit.animation_player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
		for name in ["idle","walk","attack_01","hit","death","skill_command"]:
			var length: float = unit.animation_player.get_animation(name).length
			for frame in 16:
				var t: float = length*frame/(16.0 if name in ["idle","walk"] else 15.0)
				unit.play_animation(name)
				unit.animation_player.seek(t,true)
				unit.position = Vector2(270,420)
				if name=="walk": unit.position.x += 280.0*t/length*unit.scale.x
				await process_frame
				await RenderingServer.frame_post_draw
				var im := viewport.get_texture().get_image()
				var path := "%s/%s_%d_%02d.png" % [FOLDER,name,height,frame]
				assert(im.save_png(path)==OK)
				var bounds := im.get_used_rect()
				records.append({"file":path,"sha256":FileAccess.get_sha256(path),"animation":name,"height":height,"time":t,"frame":frame,"bounds":[bounds.position.x,bounds.position.y,bounds.size.x,bounds.size.y],"clipped":bounds.position.x<2 or bounds.position.y<2 or bounds.end.x>698 or bounds.end.y>518})
			print("CENTURION_CAPTURE ",name," ",height)
		viewport.free()
	var file := FileAccess.open("res://reports/roman_centurion/native/capture_manifest.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"source":"Actual Godot GPU SubViewport rendering","engine":Engine.get_version_info(),"renderer":RenderingServer.get_video_adapter_name(),"scene_sha256":FileAccess.get_sha256(SCENE),"frames":records},"\t"))
	quit()
