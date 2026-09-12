# ROMAN_GUARD_ARTICULATED_PART_FIX_V1

**Verdict：PASS。19/19正式部件通过；Godot Handoff：READY。**

当前Complete Body与Combat Scale Gate保持通过。身体候选SHA256仍为 `df706ed02285e40b2532085d76e9936bba073eec0180e40bf63e94b35de26dfd`，未修改源图、比例、甲胄或五处Alpha边缘。五处HIRES问题继续为 `NON_BLOCKING_COMBAT_ARTIFACT`。

## 关节与pivot

只重分了指定八个肘膝部件，其余十个候选纹理不变；短剑另作独立握柄补全。肘膝没有使用AI，也没有新增绘制像素。新mask替换整个局部相接区域，建立连续的近端/远端覆盖，避免旧版孤立重叠条带与原部件之间留下空隙。重复像素是正常的关节重叠。

| 关节 | 重叠跨度（源像素） | 重叠面积（像素） | 约占关节直径 | 校准pivot (x,y) | 256px / 192px |
|---|---:|---:|---:|---|---|
| near elbow | 27.00 | 2708 | 32.14% | (332,671) | PASS / PASS |
| far elbow | 27.23 | 2539 | 33.21% | (680,695) | PASS / PASS |
| near knee | 36.19 | 4271 | 32.90% | (389,1079) | PASS / PASS |
| far knee | 36.84 | 4693 | 32.89% | (640,1083) | PASS / PASS |

Pivot已做视觉校准和±20°验证，仍是进入Godot前的建议中心，允许引擎内调整；修改后必须重验。查看 [pivot/轮廓/重叠图](joint_pivot_review_v3.png)、[原分辨率局部](joint_rotation_test_v3.png)、[256px与192px关节图](joint_rotation_combat_scale_v3.png)。完整原尺寸帧保存在 `reports/joints_v3/`。

Full Resolution：`PASS_WITH_NON_BLOCKING_HIRES_JOINT_ARTIFACT`。高分辨率仍能观察到皮肤或甲片接缝，但两个战斗尺寸100%查看均没有可见透明断裂，远膝+20°此前的水平缺口已消失。带装备的同组测试见 [完整装备运动图](joint_equipped_combat_scale_v3.png)。本次结构审批覆盖这些测试范围；更大动作需要新审查，不需要为当前范围追求HIRES像素完美。

## 完整短剑与盾牌

Sword：**COMPLETE / PASS**。正式文件为 `assets/units/odyssey/roman_guard/parts/sword.png`，1024×1536 RGBA，SHA256：`ac8b63fb8097e0757fca0555c10ce22b17a5e8ca84953b443f38d95eb608d295`。

检查了DESIGN、RIG_MASTER、COMBAT_LOOK。Design独立剑图的握柄长度与当前武器不同，其他两图仍被手掌遮挡，因此没有拉伸参考像素冒充当前握柄。使用内置 `image_gen.imagegen` 执行一次独立短剑补全请求，未输入人体底版，也未重跑001–005。工具实际返回的是带棋盘格的RGB图，原件仅归档，未当作透明资产发布。

正式剑保留原提取中的剑刃、剑格和剑首，只提取生成结果中的握柄，并去除旧提取的皮肤/红布残留。所有保留的原像素改动为0；最终Alpha min/max为0/255，主体是一个连通组件，没有手、人物或棋盘背景。没有把AI返回的重绘剑刃覆盖原剑刃。20°/30°运动已复验。

查看 [完整短剑](full_sword_review_v1.png)、[握柄细节](full_sword_grip_review_v1.png)、[实际调用记录](ai_jobs/006_full_sword_v1.json)、[提示词](../work/prompts/FULL_SWORD_V1.txt)、[确定性装配与哈希记录](full_sword_assembly_v1.json)。

Shield：**PASS**，纹理和mask完全未改。此前裁切来自固定预览画布，现改用扩展视口，正式PNG画布仍保持1024×1536。±7°与小范围移动在256px和192px均无明显问题。见 [盾/剑运动图](equipment_combat_scale_v3.png)。

## Recomposition Gate V3

HIRES：已审查，允许已批准补全、关节重复像素和非阻塞Alpha差异。256px：**PASS**。192px：**PASS**。

十项检查均通过：角色身份、整体轮廓、头部锚点、肩部锚点、髋部锚点、膝部锚点、双脚地面线、盾牌默认位置、短剑默认位置、整体比例。旧IoU/逐像素等指标完整保留为diagnostic，`blocking=false`，不再阻塞Combat/Rig资产。

查看 [原分辨率重组](recomposition_full_resolution_v3.png)、[256px重组](recomposition_256px_v3.png)、[192px重组](recomposition_192px_v3.png)、[新门禁](combat_rig_gate_v3.json)。

## 正式发布与验证

19个正式PNG均为1024×1536 RGBA，路径在 `assets/units/odyssey/roman_guard/parts/`，全部绑定独立mask/part审批、来源和SHA。人体部件逐项验证为批准底版的真实像素提取；短剑额外验证为记录的原金属件+局部生成握柄装配。其余原候选均只读保留，未推倒重做。

结构审批按实测Combat范围执行：头盔随头部保持附件关系，现有前/后双绘制披风在测试范围内接受；不要求凭空补出不会暴露的隐藏区域。

`tools/run_validation.py --test-tools`：源图、19 Parts、Recomposition、Joint Tests、Godot Handoff全部通过。12项安全测试及7项V3回归测试通过，包括修改pivot、测试图、正式纹理、移除短剑审批都会撤销READY；即使重新填写哈希，私改剑刃仍不能通过装配来源验证。

**Godot Handoff = READY**，目标Godot 4.7.2 Stable / HUMAN_MEDIUM_RIG_V1 / Skeleton2D / Bone2D。这里是资产交接验收，本轮没有生成Godot场景或动画，没有第二兵种。
