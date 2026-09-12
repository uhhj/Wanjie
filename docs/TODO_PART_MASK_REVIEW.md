# 部件审查：本轮已关闭

19/19正式RGBA同画布部件结构审批通过，Godot Handoff READY。当前有效清单为 `tools/roman_guard_parts_manifest.json`。

| 部位 | 当前结果 |
|---|---|
| near elbow | 27px连续重叠，32.14%，256/192px PASS |
| far elbow | 27.23px连续重叠，33.21%，256/192px PASS |
| near knee | 36.19px连续重叠，32.90%，256/192px PASS |
| far knee | 36.84px连续重叠，32.89%，256/192px PASS；+20°透明缺口消失 |
| sword | COMPLETE；独立握柄补全、真实RGBA、原保留金属件像素不变 |
| shield | PASS；纹理未修改，扩展预览视口解决裁切 |
| 其他部件 | 纹理未重做，按已测试Combat范围结构审批通过 |

原问题和修复证据见 [ARTICULATED_PART_FIX_V1](../reports/ARTICULATED_PART_FIX_V1.md)。高分辨率接缝与五处Alpha边缘继续非阻塞，不为当前范围追求像素完美。

头盔作为头部附件共同运动；现有披风前/后绘制在已测试范围内接受。未来扩大动作范围时审查新暴露部位，不重新生成角色。
