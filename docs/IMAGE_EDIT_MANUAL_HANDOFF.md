# 当前交接：Combat Gate 已通过，继续部件局部工作

Complete Body：**PASS_WITH_NON_BLOCKING_HIRES_EDGE_ARTIFACTS**。整体：**BLOCKED**；Godot：**NOT_READY**。

当前人体来源：`D:\Wanjie\documents\Wanjie\work\05_complete_body_candidate_v2_rgba_clean.png`。
SHA256：`df706ed02285e40b2532085d76e9936bba073eec0180e40bf63e94b35de26dfd`。

**停止 region_001–region_005 Alpha 修补。** 五处高分辨率问题已标为 NON_BLOCKING_COMBAT_ARTIFACT。256/192/128px 白底、灰底审查通过；本例外仅适用于 Combat/Rig。

已生成19个同画布真实像素候选、16个人体 masks、pivot hints，执行重组和18种运动预览。没有发布失败部件，没有新的AI调用或001–005。见 [当前报告](../reports/COMBAT_SCALE_VISUAL_GATE_V1.md)。

续跑从 [parts manifest](../tools/roman_guard_parts_manifest.json) 的当前候选开始。先看 [局部问题与bbox](../reports/part_art_review_v2.json) 和 [运动图](../reports/joint_rotation_test_v2.png)。修复对象为肘膝隐蔽表面与边界、缺失剑柄及披风背面。没有用大面积复制、遮盖或整图重绘掩盖缺失表面。

若在外部美术工具补全，只处理相关独立part的局部，保留来源、mask、输入/输出SHA。不得改变已通过底版或装备设计。无法可靠局部编辑时保持部件阻塞，不能退回整图生成。

候选复测：`python tools/review_part_candidates.py`。
正式门禁：`python tools/run_validation.py --test-tools`。
每个part与mask都需单独、绑定SHA的审批才可通过 `extract_roman_guard_parts.py --promote`；Combat Gate不会自动批准部件。人体候选当前后缀_v3代表mask迭代，人体源没有换版。

此前Alpha过程完整保留在 [历史报告](../reports/ALPHA_MATTE_CLEANUP_V2.md) 与 [历史Body Gate V3](../reports/complete_body_gate_v3.json)。历史FAIL仅供高分辨率追溯，不是当前Combat门禁。
