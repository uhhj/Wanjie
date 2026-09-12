# 当前交接：ALPHA_MATTE_CLEANUP_V2

**Verdict：BLOCKED_LOCAL_ALPHA_TOUCHUP_ONLY。Body Gate V3：FAIL；Godot Handoff：NOT_READY。**

当前候选：`D:\Wanjie\documents\Wanjie\work\05_complete_body_candidate_v2_rgba_clean.png`

SHA256：`df706ed02285e40b2532085d76e9936bba073eec0180e40bf63e94b35de26dfd`

本轮已按用户授权，仅在 trimap unknown band 的半透明像素中做黑底 RGB 去污染；所有最终 opaque RGB、sure foreground RGB，以及 unknown band 外的 Alpha/RGB 完全保持。旧 RGB 和初始 RGBA 不变。未调用 AI、未重跑 001–005。

当前全局算法和候选已冻结，不再修改全局阈值、羽化范围或侵蚀强度。只剩 region_001–region_005：红冠顶部、肩甲上缘、远侧护胫外缘、近侧鞋底、远侧鞋底。每处 bbox、问题、建议见 [局部目标 JSON](../reports/alpha_manual_touchup_targets_v2.json)，图见 [局部修补目标](../reports/alpha_manual_touchup_targets_v2.png)。

这些框是审查范围，不能当作整体编辑 mask。修补仅限已有 unknown band；保留真实黑色描边和 opaque RGB。若需要改变锁定 sure foreground，先明确标记冲突，不自动修改。当前并未执行局部修补。

查看 [本轮报告](../reports/ALPHA_MATTE_CLEANUP_V2.md)、[四背景](../reports/rgba_background_review_v2.png)、[4x 局部](../reports/rgba_edge_review_v2.png)、[trimap](../reports/alpha_trimap_review_v2.png)、[Body Gate V3](../reports/complete_body_gate_v3.json)。逐区域 4x 文件在 `reports/alpha_edge_details_v2/`，避免只看缩小总览。

数值检测：疑似 halo 3345→651，下降约80.54%，只是 debug，不能据此直接 PASS。7 项测试通过和 opaque RGB=0 也不能替代局部美术审查。

全部16项 Body Gate V3 通过之后才能开始 19 parts。当前正式人体来源、manifest、pivot 未切换；重组、关节测试、Godot Rig 与动画均未开始，不创建第二兵种。
