# 19部件审查待办

Complete Body的Combat Gate已通过。人体16个masks已生成，装备3个masks沿用真实像素提取。有效路径、SHA和pivot见 `tools/roman_guard_parts_manifest.json`。19个候选格式通过，正式审批未完成。

| 部位 | 当前问题 / 待验证项 |
|---|---|
| near upper / fore arm | 旋转后直切皮肤及外翻片；需局部肘面和边界处理 |
| far upper / fore arm | 护具上缘开放楔形接缝 |
| near thigh / shin | 膝盖上方开缝，±20°洞增长检查失败 |
| far thigh / shin | +20°水平透明缺口在256px仍可见 |
| sword | 剑首与刃/护手之间缺少原手掌遮挡的握柄 |
| cape | 可见布料保留身体/手臂遮挡形状，后侧未完整 |
| head / helmet | 脸部开口、耳部、颊护片所有权需审批；未测相对转动 |
| torso / pelvis | 肩、腰、髋边界与运动隐藏重叠需审批 |
| hands / feet | 腕、踝接缝及活动范围需审批 |
| shield | 独立运动已执行；+7°固定画布预览裁切需处理，区别于纹理缺陷 |

查看 [局部问题](../reports/part_art_review_v2.json)、[候选图](../reports/parts_candidate_review_v2.png)、[运动图](../reports/joint_rotation_test_v2.png)。四个肘膝静止轴向重叠约26%，不能据此宣称隐藏关节完整。

只处理相应part，不重画角色。五处静态Alpha高分辨率问题已非阻塞，不在本待办范围。源图与当前Complete Body只读。
