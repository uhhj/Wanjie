extends RefCounted
# Only this table assigns visual z order. Cape clips are separate draws of one PNG.
const LAYERS = ["cape_back", "leg_far_thigh", "leg_far_shin", "foot_far",
	"arm_far_upper", "arm_far_fore", "hand_far", "leg_near_thigh",
	"leg_near_shin", "foot_near", "knee_near", "pelvis", "torso", "cape_front",
	"head", "helmet", "arm_near_upper", "arm_near_fore", "shield", "sword", "hand_near"]

static func apply(root: Node) -> void:
	for i in range(LAYERS.size()):
		var item = root.find_child("Art_" + LAYERS[i], true, false) as CanvasItem
		assert(item != null, "Missing draw: " + LAYERS[i])
		item.z_as_relative = false
		item.z_index = i
		var skin = root.find_child("Art_"+LAYERS[i]+"_skinned",true,false) as CanvasItem
		if skin != null:
			skin.z_as_relative = false
			skin.z_index = i
	var blood = root.get_node("DeathBlood") as CanvasItem
	blood.z_as_relative = false
	blood.z_index = LAYERS.size()
