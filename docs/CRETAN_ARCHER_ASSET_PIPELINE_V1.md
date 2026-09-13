# Cretan Archer 资产流水线 V1

当前状态：PASS_WITH_IMAGE_EDIT_MANUAL_STEP_REQUIRED（仅生产准备完成）。Complete Body、20 个正式部件及原生 Rig 均未完成，Godot handoff=NOT_READY。流程依据用户的完整任务说明和 WALK_REFERENCE 补充；附件原文归档在 `CRETAN_ARCHER_TASK_SPEC_V1.txt`，不把图内内容当作额外指令。

代码入口为 `tools/cretan_archer_pipeline.py`，仅依赖 Python、Pillow、NumPy，不包含虚构 API 或密钥。工作目录及报告使用 `work/cretan_archer/`、`reports/cretan_archer/`，避免覆盖已批准的 Roman Guard 报告和中间文件。

## 已完成

- 五张用户图片按职责冻结，原件字节保留，尺寸、mode、Alpha 范围及 SHA256 均有记录。
- 身份冲突审查；20 部件清单；可见解剖标志的初始 pivot hints。所有 pivot 仍需 Complete Body 后审查，不能直接当批准绑定数据。
- 三张真实、非空、同画布局部 mask 草稿及完整 prompts、待执行 job manifests、能力审计。
- 顺序导入、mask 外改动拒绝、来源及审查 SHA 绑定、独立 Alpha 导入、实际尺寸审查图生成、Body fail-closed 门禁。
- HUMAN_MEDIUM_RIG_V1 复用计划和轻装八相位 Walk 计划；没有伪造原生渲染或性能数据。

## 数据链

`Rig Master → 001 去弓 → 审查 → 002 去箭袋 → 审查 → 003 去披布 → 审查 → 004 独立 Alpha 派生 → Body/combat gate → 正式拆件 → 重组/关节门禁 → 原生 Rig/动画`。

精确输入、mask、prompt、输出和命令见 `CRETAN_ARCHER_IMAGE_EDIT_HANDOFF_V1.md`。前三次是局部美术补全，第四步仅应用已审查 Alpha，RGB 不变。源图不覆盖，已有阶段结果不覆盖，审查不能脱离文件 SHA。

## 正式拆件解锁后

`tools/cretan_archer_parts_manifest.json` 列出 20 个目标，目前均 MISSING，没有占位 PNG。15 个身体部件唯一来源为批准的 `04_complete_body_rgba.png`；装备优先提取原 Rig Master 的真实可见像素。隐藏弓握柄、箭袋背面、披布及完整箭杆需要真实遮挡检查，详见 `TODO_CRETAN_ARCHER_PART_REVIEW.md`。

肘膝保留合理重复像素重叠；pivot 放在解剖旋转中心。沿用 Roman Guard 已验证的“大腿—小腿—脚掌联动”经验，但不复制其重装步态。不得为对称性强行拆独立可见膝甲。正式 PNG 同源画布 RGBA；身份、轮廓、锚点和装备位置以 256/192px 重组验收，不能靠像素差值忽略实际失真，也不能因隐藏重复像素误判失败。

后续需要真实生成 `reports/cretan_archer_recomposition_review.png`、`reports/cretan_archer_joint_review.png`，目前未生成，不能将 source_role_review 当成这些测试。

## 复用范围与冻结

原有 `scenes/rigs/human_medium_rig_v1.tscn` 的 23 个骨骼节点及 SHA 已记录在 `reports/cretan_archer/rig_reuse_plan.json`。计划以该拓扑实例化本单位，适配本单位 rest pose / 骨长，增加 bow_socket、arrow_socket、quiver attachment，复用 cape 分支。弓不挂在 shield_socket；不修改 Roman Guard 场景、资源、动画或已批准共享基线。

`verify-frozen` 同时核对五张新源图和 49 项 Roman Guard 冻结文件。真实复用、成本比较、attack_release、20 单位测试均待正式资产通过后验证，当前不宣称复用成功或已降低生产成本。

## 状态判定

缺图为 NOT_RUN；格式、来源或视觉审查失败为 FAIL；只有全部通过才 Body PASS。后续 parts、recomposition、joints、五动画、单次释放事件及 20 单位 smoke 全部通过，才能输出 CRETAN_ARCHER_NATIVE_RIG_REUSE_SUPPORTED。准备阶段的手动编辑交接状态不是整项任务成功。
