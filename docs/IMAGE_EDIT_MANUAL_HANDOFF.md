# 当前资产交接：READY

ROMAN_GUARD_ARTICULATED_PART_FIX_V1：**PASS**。19个正式部件已通过，Godot Handoff：**READY**。

当前完整人体继续冻结为 `work/05_complete_body_candidate_v2_rgba_clean.png`，SHA256为 `df706ed02285e40b2532085d76e9936bba073eec0180e40bf63e94b35de26dfd`。五处HIRES Alpha问题仍为NON_BLOCKING_COMBAT_ARTIFACT，不再修补。

四个肘膝已用真实底版像素建立约32%–33%连续重叠并校准pivot；256px和192px均通过±20°测试。高分辨率接缝为PASS_WITH_NON_BLOCKING_HIRES_JOINT_ARTIFACT。

完整短剑已发布到 `assets/units/odyssey/roman_guard/parts/sword.png`：仅握柄使用一次内置imagegen结果，原剑刃、剑格和剑首的保留像素不变；最终是真实透明RGBA。无需重新处理已通过部件。实际prompt与调用记录在 `work/prompts/FULL_SWORD_V1.txt`、`reports/ai_jobs/006_full_sword_v1.json`。

正式资产清单见 [parts manifest](../tools/roman_guard_parts_manifest.json)。结果见 [完整报告](../reports/ARTICULATED_PART_FIX_V1.md)、[战斗关节审查](../reports/joint_rotation_combat_scale_v3.png)、[新综合门禁](../reports/combat_rig_gate_v3.json)。旧的V2失败报告和Alpha审查完整保留为历史证据。

复验：`python tools/run_validation.py --test-tools` 与 `python tools/test_articulated_gate_v3.py`。源图、pivot、mask、正式part或审查证据改变后，哈希审批失效，需重验受影响项目。不要重跑001–005或从头拆19件。

交接目标：Godot 4.7.2 Stable、HUMAN_MEDIUM_RIG_V1、Skeleton2D/Bone2D。资产审批覆盖已测试动作范围；Godot场景与动画为后续阶段。
