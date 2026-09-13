extends Node2D
## Small deterministic death accent; frozen character textures remain unchanged.
@export var phase := -1.0:
	set(value):
		phase = value
		queue_redraw()

func _draw() -> void:
	if phase <= 0.0 or phase >= 1.0:
		return
	var fade := minf(1.0, (1.0-phase)*3.0)
	for i in range(7):
		var velocity := Vector2(-300.0-i*35.0, -150.0+(i%3)*110.0)
		var p := Vector2(-350,-900) + velocity*phase + Vector2(0,180*phase*phase)
		var color := Color(0.40+(i%2)*0.09,0.025,0.035,fade)
		draw_line(p,p+velocity.normalized()*(7.0+i%3*3.0),color,3.0+i%2,true)
		draw_circle(p,2.2+i%3*0.7,color,true,-1,true)
