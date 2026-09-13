extends SceneTree

func _initialize() -> void:
	call_deferred("capture")

func capture() -> void:
	var viewport = SubViewport.new()
	viewport.size = Vector2i(1024,1536)
	viewport.transparent_bg = true
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var unit = load("res://scenes/units/odyssey/roman_guard/roman_guard_rig.tscn").instantiate()
	unit.autoplay = false
	unit.position = Vector2(530,1460)
	viewport.add_child(unit)
	unit.rest_pose()
	await process_frame
	await RenderingServer.frame_post_draw
	viewport.get_texture().get_image().save_png("res://reports/native_rig_v2/rest_pose_native.png")
	viewport.free()
	var lab = load("res://scenes/tests/roman_guard_rig_lab.tscn").instantiate()
	root.add_child(lab)
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("res://reports/native_rig_v2/rig_lab_screenshot.png")
	lab.free()
	quit()
