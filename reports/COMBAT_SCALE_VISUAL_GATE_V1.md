# Combat / Rig 验收与拆件结果

当前 Complete Body：**PASS_WITH_NON_BLOCKING_HIRES_EDGE_ARTIFACTS**。整体流水线：**BLOCKED**，阻塞位于部件关节和隐藏区域。Godot Handoff：**NOT_READY**。

## 两种审查标准

| 审查 | 结果 |
|---|---|
| HIRES_PIXEL_REVIEW | 五处历史问题保留，NON_BLOCKING_COMBAT_ARTIFACT |
| COMBAT_SCALE_VISUAL_REVIEW | PASS，256 / 192 / 128 px，100% 显示 |

查看 [实际尺寸审查](combat_scale_visual_review.png)。角色高度由 Alpha 包围盒计算，保持纵横比，采用预乘 Alpha 缩小，无二次放大。白底和50%灰底均未见明显 halo、孤立黑点、悬浮鞋底黑块或超过约一个最终像素的背景噪声。仓库及 pictures 目录没有可用战场背景，未将原画充作战场素材。

当前源 `work/05_complete_body_candidate_v2_rgba_clean.png`，1024×1536 RGBA，SHA256：`df706ed02285e40b2532085d76e9936bba073eec0180e40bf63e94b35de26dfd`。未修改该图片、RGB原件、初始Alpha或Rig Master，未调用AI、重跑001–005或继续五处Alpha修补。历史 [Body Gate V3](complete_body_gate_v3.json) 保持原始高分辨率证据；当前生效的是 [Combat Body Gate](complete_body_gate_combat_v1.json)。

## 部件与重组

19/19个真实像素候选齐全：16个人体部件来自当前底版，盾、剑、披风沿用Rig Master提取候选。均为1024×1536 RGBA，格式和源像素提取验证通过。manifest指向人体 `_v3.png` masks/candidates；v3是拆件边界版本，不是重新生成身体。

正式美术批准仍为0/19。查看 [候选验证](parts_candidate_validation_v2.json)、[候选审查图](parts_candidate_review_v2.png)、[精确部件问题及bbox](part_art_review_v2.json)。遮挡区没有用邻近皮肤或甲片冒充补全，失败候选未发布到正式parts目录。

身体部件静态重组与当前底版的Alpha、所有可见RGB逐像素一致。Alpha=0位置RGB归零不计为可见改动。四个肘膝静止时沿骨骼轴的真实像素重叠约26%，满足20%–30%的数值范围，但不能替代隐藏关节表面。

[重组对照](recomposition_combat_review_v2.png) 的身份和装备布局可辨认且一致。现有几何门禁未通过：silhouette IoU 97.3917%（要求≥98.5%），质心偏差5.9205px（≤5），3px轮廓召回94.6657%（≥99%）。未修改阈值伪造PASS。见 [指标](recomposition_metrics_v2.json)、[差异图](recomposition_diff_v2.png)。这不撤销已通过的Combat Alpha验收。

## 运动测试

已执行18个真实候选案例：近/远肘、近/远膝各-20°/0°/+20°，盾三种小范围运动，剑0°/20°/30°。查看 [256px运动图](joint_rotation_test_v2.png)、[关节细节](joint_rotation_detail_v2.png)。肘膝预览没有盾或披风遮盖。

- 肘：转动后出现直切皮肤、外翻皮肤片和前臂过渡接缝。
- 膝：近侧开缝；远侧+20°的水平缺口在256px角色图中仍可见，属于运动暴露的缺失表面。
- 盾：可独立运动；+7°/(8,-5)的固定画布预览裁掉约0.897% Alpha质量。单独记录为预览边界问题，以后Godot Sprite2D视口不应按源画布截断运动。
- 剑：20°/30°已执行，无画布裁切；原手掌遮挡的握柄仍缺失，尚不是完整装备。
- 披风：可见布料提取仍有身体遮挡造成的缺失区域，后侧布面未完成。

## 续跑

保持当前底版与Combat Gate，只处理相应part边界、隐蔽关节、剑柄和披风局部。不要重启人体补全或Alpha修补。此前未验证出可靠局部inpaint接口，不能用整图生成绕过隐藏区门禁。

`tools/review_part_candidates.py` 复现候选格式、重组和运动审查，报告明确为CANDIDATES_ONLY_NOT_FORMAL。`tools/run_validation.py --test-tools`执行正式门禁，当前预期阻塞。12项原安全测试和6项新Combat Gate测试通过，保证源图/审查图变化会撤销审批，Combat例外不放宽单个part审批。

正式19 Parts、Recomposition、Joint Tests全部通过以后，才可进入Godot 4.7.2 Stable / Skeleton2D / Bone2D。未创建正式Rig、动画或第二兵种。
