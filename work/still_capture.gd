extends SceneTree
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var view := SubViewport.new()
	view.size = Vector2i(1440,560)
	view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(view)
	var bg := ColorRect.new(); bg.size=Vector2(1440,560); bg.color=Color(.85,.86,.87); view.add_child(bg)
	var ground := Line2D.new(); ground.points=PackedVector2Array([Vector2(20,475),Vector2(1420,475)]); ground.width=1; ground.default_color=Color(.5,.5,.5); view.add_child(ground)
	var packed: PackedScene = load("res://work/minotaur_breaker/candidates/minotaur_breaker_candidate.tscn")
	var unit = packed.instantiate(); unit.autoplay=false; unit.root_motion_enabled=false
	unit.scale = Vector2.ONE*360.0/1435.0; unit.position=Vector2(500,475)
	view.add_child(unit); unit.set_process(false)
	unit.animation_player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	unit.play_animation("skill_01")
	unit.animation_player.seek(2.0,true)
	await process_frame
	await RenderingServer.frame_post_draw
	view.get_texture().get_image().save_png("work/carry_still.png")
	quit()
