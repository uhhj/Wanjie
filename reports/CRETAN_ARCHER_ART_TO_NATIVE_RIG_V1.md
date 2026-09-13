# Cretan Archer 本轮交付状态

**Verdict：PASS_WITH_IMAGE_EDIT_MANUAL_STEP_REQUIRED**。已完成源图冻结及可恢复的局部编辑交接；完整资产与 Native Rig 任务尚未通过。

| 项目 | 实际状态 |
|---|---|
| 输入冻结 | DESIGN、COMBAT_LOOK、RIG_MASTER、CODEX、WALK_REFERENCE 共 5 张，原始字节/SHA 留存 |
| 身份冲突 | 已记录 CODEX 头盔/重甲与头巾轻装设计的冲突，不融合 |
| 图像编辑能力 | 有参考图编辑工具；没有验证到可靠局部 mask API/CLI；本单位模型调用 0 次 |
| 编辑准备 | 3 张局部 mask 草稿、3 份 prompt、3 份待执行 job，均可审查 |
| Complete Body | NOT_RUN，未生成，不声称视觉或 Alpha PASS |
| 正式部件 | 0/20，manifest 明确 MISSING；pivot 是待审查建议 |
| Recomposition / Joint tests | NOT_RUN |
| idle / walk / attack_01 / hit / death | NOT_RUN |
| attack_release 恰好一次 | NOT_RUN |
| 20 单位 smoke / 本单位 headless | NOT_RUN |
| HUMAN_MEDIUM_RIG_V1 复用 | 已核对基线并制定适配计划；PLANNED_NOT_PROVEN |
| Godot handoff | NOT_READY |

Rig Master：`D:/Wanjie/documents/Wanjie/art_source/odyssey/cretan_archer/OD_UNIT_02_CRETAN_ARCHER_RIG_MASTER_V1.png`。SHA256：`9fcc93f8dabcfc08003932444cfa6801bb808c3cb7f69693672d38a5862f6618`。1024×1536、RGBA、Alpha 0–254，已有真实透明背景，脚下另有可见投影。不得覆盖原图或再次用黑色阈值分离。

## 接下来准确交给外部工具的内容

先处理 001：Rig Master + `work/cretan_archer/masks/001_remove_bow.png` + `work/cretan_archer/prompts/001_remove_bow.txt`。仅移除弓和弦，保护可见手指、手腕、服装。结果放 `work/cretan_archer/raw/001_external.png`，通过导入和视觉审查后才做 002、003。

完整三阶段表、命令、Alpha 格式派生及恢复门禁，见 `docs/CRETAN_ARCHER_IMAGE_EDIT_HANDOFF_V1.md`。无需重启或重新复制源图。当前没有本地 mask 能力，因此按用户指定回退交接；没有把全图编辑当作局部补全，也没有造正式 PNG 满足清单。

## 本轮可审查图片

- `D:/Wanjie/documents/Wanjie/reports/cretan_archer/source_role_review.png`：五张输入职责。
- `D:/Wanjie/documents/Wanjie/reports/cretan_archer/occlusion_mask_review.png`：三个草稿 mask；重点看持弓手指、头巾与箭袋、白袖与披肩交界。
- `D:/Wanjie/documents/Wanjie/reports/cretan_archer/walk_reference_pose_review.png`：运动参考裁片，保留脚部上下文；不是正式 Sprite 或 Godot 帧。

Walk 已整理 contact/down/passing/up 的近/远两半周期。参考没有明确展示的 passing/反相动作标为需要制作，不能声称提取到了完整循环。最终对比图必须等待真实 Godot Rig 姿态，当前未生成占位对比图。

## 验证与范围

导入门禁 9 项测试通过，覆盖 mask 外改动、RGB 伪输入、越过前阶段审查、来源缺失、prompt 变化、覆写、matte 新增前景、RGB 保留及缺图不能 PASS。测试使用临时 8px 合成样本，放在被忽略的 `work/test_runs/`，不进入正式资产。

五张源图及 49 项 Roman Guard 冻结文件哈希验证通过。未修改已批准 Roman Guard、共享骨架、其他动画或原有报告。Godot 版本已确认 4.7.2.stable.official.ed1daf0bf，路径见动画计划；这不等同于本单位解析通过。

分支：`feature/cretan-archer-native-rig-v1`，基于 `aa81611`。本轮只提交新增 Cretan Archer 准备包。当前不能回答“已经证明复用成功”或“比首兵种成本更低”；需在真实部件、动画和 smoke 全部通过后评估。
