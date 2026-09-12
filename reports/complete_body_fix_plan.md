# FIX_COMPLETE_BODY_GATE_V1 — 局部修复计划

结论：当前底版仍未通过。只观察到需要本轮处理的两类明确缺陷：裙甲斜向拼接和未经批准的高领甲。尚未执行 job 004 / 005。

## 基线与审查证据

- 实际仓库：`D:\Wanjie\documents\Wanjie`；此前已获用户确认从 `uhhj` 改名。分支：`feature/roman-guard-ai-rig-assets-v1`。本轮开始时工作区 clean，HEAD 为 `5b7fca9`；四个指定历史提交均保留。
- 唯一继续编辑的候选：`work/03_complete_body_base.png`，1024×1536 RGBA，SHA256 `492adab57065964962b6a7ef635cbb8990a4e774bdb5ec2ee30989049624c5bf`。
- 冻结源图：`D:\Wanjie\documents\pictures\OD_UNIT_01_ROMAN_GUARD_RIG_MASTER_V1.png`，SHA256 `98642eef9516a371af2e23aea63fbb7156ba506281bc6b245b60c159b7bfc563`；仓库副本与其一致，只读。
- 已逐张查看 `complete_body_review.png`、`complete_body_detail_review.png`、`001_hand_matte_review.png`、`equipment_extraction_review.png`、`occlusion_mask_review.png`、`helmet_edge_review.png`，均位于 `reports/`；已读取 `docs/IMAGE_EDIT_MANUAL_HANDOFF.md`。
- 补充实图放大证据：`work/fix_skirt_inspection.png`（原坐标裁片 300,880–620,1080，放大 3 倍）、`work/fix_collar_inspection.png`（423,335–595,456，放大 4 倍）。这些是诊断裁片，不是修改后的底版。

## 明确可见的缺陷

| 缺陷 | 可见证据 | 允许修复范围 |
|---|---|---|
| A：skirt armor seam | 原短剑经过的裙甲下摆及上大腿附近出现斜向贴片边界；暗红布褶、色值与锯齿形下摆不连续，局部呈三角形拼接；细斜线延伸到腿间透明区和上大腿。 | 约 x323–608、y936–1065 内的两条窄局部路径，沿实际接缝描绘；只包含接缝及少量上下文，不以此矩形整体编辑。 |
| B：unapproved high collar armor | 下颌后方出现竖起的铁灰金属领圈和金边，约 x443–562、y352–428。该新增款式在本轮查看的冻结设计可见区域中没有依据。 | 只包含新增领圈与数像素过渡；头盔、脸、现有肩甲主体与胸甲主体均保护。 |

未从这些图中确认第三项独立的结构缺陷，不补写推测性问题。当前候选可见双手、双腿、双脚，未见盾、剑、披风残留主体；这些观察不能抵消 A/B，也不能代替 v2 验收。头盔后缘已有修复证据，不重做。装备候选缺失的被遮挡部分属于后续独立部件任务，本轮不处理。

## 参考顺序与设计锁

依次查看 `D:\Wanjie\documents\pictures\` 下的 `OD_UNIT_01_ROMAN_GUARD_DESIGN_V1.png`、`OD_UNIT_01_ROMAN_GUARD_RIG_MASTER_V1.png`、`OD_UNIT_01_ROMAN_GUARD_COMBAT_LOOK_V1.png`。这些参考的颈肩有红布遮挡：只能继承已经可见的结构，不能把隐藏区域当成已获批准的颈甲设计。没有读取或使用 CODEX 原画决定隐藏结构。

保持脸、头盔、红冠、胸甲主体、原肩甲主体、人体比例、站姿、腿长、裙甲总体结构及配色。禁止增加颈甲、肩甲或其他装备，禁止全图重绘。去盾阶段 001 和当前 002/003 历史输出均保持原文件，不归档重跑。

## 顺序与门禁

1. job 004 从当前 `03_complete_body_base.png` 继续；局部 mask 为 `work/masks/fix_skirt_seam_v2.png`。仅在真实局部编辑成功后产生 `work/04_skirt_fixed.png`。
2. job 005 依赖真实的 004 输出；局部 mask 为 `work/masks/remove_unapproved_collar_v2.png`。004 若影响颈肩，则停止审查，不能静默沿用此 mask。通过后才产生 `work/05_complete_body_candidate_v2.png`。
3. 两张 mask 是可审查的准备草案，8-bit L、1024×1536，白色允许编辑、黑色保护。它们不是已执行 AI 的证明，也不表示已获美术通过。
4. 当前仅发现 `image_gen.imagegen` 的参考图编辑接口，没有独立 mask 参数；既有 Python 脚本仅准备/导入/合成，不提供模型端局部 inpainting。环境检查未验证到其他可调用局部接口。
5. 按本轮明确停止规则：`BLOCKED_LOCAL_INPAINT_UNAVAILABLE`。不调用整图编辑后再用 mask 合成绕过规则。仅保存计划、mask/提示词草案、能力审计和 NOT_RUN 记录。
6. 未产生 05 时，v2 美术门禁不得标 PASS，不创建伪 v2 复核图；19 个正式部件、重组、关节测试和 Godot 均不继续。

## 恢复条件

先验证真实编辑接口能够接受并遵守局部 mask，记录实际工具/模型标识及 mask 语义，再顺序执行 004、005。返回图必须同画布真实 RGBA；检查 mask 外像素、脸/头盔/胸甲/腿部比例保护，以及 A/B 是否确实消除。对真实 05 生成两张 v2 审查图并逐项审查人体完整性、装备移除、四肢、裙甲、颈肩、未经批准装备和身份一致性；全部通过后才解锁原流水线。
