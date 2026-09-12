extends Node2D
var show_bones := true
var show_pivots := true
var show_ground := true
var show_sockets := true

func _process(_delta: float) -> void:
	if visible:
		queue_redraw()

func _draw() -> void:
	var unit = get_parent()
	var skeleton = unit.get_node("VisualRoot/Skeleton2D") as Skeleton2D
	if show_ground:
		draw_line(Vector2(-600,0),Vector2(600,0),Color(0.1,0.9,0.5),3)
	for bone in skeleton.find_children("*","Bone2D",true,false):
		var point = to_local(bone.global_position)
		if show_bones and bone.get_parent() is Bone2D:
			draw_line(to_local(bone.get_parent().global_position),point,Color(0.3,0.9,1),3)
		if show_pivots:
			draw_circle(point,5,Color.YELLOW)
		if show_sockets and "socket" in str(bone.name):
			draw_circle(point,12,Color.MAGENTA,false,3)
