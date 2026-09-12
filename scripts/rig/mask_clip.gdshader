shader_type canvas_item;
uniform sampler2D clip_mask : filter_nearest, repeat_disable;
void fragment() {
	COLOR.a *= texture(clip_mask, UV).r;
}
