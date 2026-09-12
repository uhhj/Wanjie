# 当前验收：ROMAN_GUARD_AI_RIG_ASSET_PIPELINE_V1

**Verdict：BLOCKED_LOCAL_ALPHA_TOUCHUP_ONLY。**

当前 RGBA 清理已完成窄带 Alpha 估计和黑底 RGB 去污染，但五处局部轮廓残留未通过；不再调整全局算法。

| 项目 | 结果 |
|---|---|
| Opaque RGB changed | 0；最大差值0 |
| Edge RGB changed | 5892 |
| Fractional alpha | 5964 |
| Halo debug | 3345→651，下降80.54% |
| Plume / shoulder / boots | 仍需局部修补 |
| Helmet / hands / skirt | 视觉 PASS |
| Legs | 近侧保持；远侧护胫外缘需局部修补 |
| Complete Body Gate V3 | FAIL |
| 19 Parts | NOT_STARTED，正式0/19 |
| Recomposition / Joint Tests | NOT_RUN / NOT_RUN |
| Godot Handoff | NOT_READY |

输出：`work/05_complete_body_candidate_v2_rgba_clean.png`，PNG RGBA 1024×1536。

SHA256：`df706ed02285e40b2532085d76e9936bba073eec0180e40bf63e94b35de26dfd`

[完整报告](ALPHA_MATTE_CLEANUP_V2.md) · [五处修补目标](alpha_manual_touchup_targets_v2.png) · [Body Gate V3](complete_body_gate_v3.json)

原 RGB、初始 RGBA、冻结源图和历史阶段未改。未调用生成式 AI，未执行001–005。继续当前分支正常提交并push；准确 Commit SHA 与最终 Working Tree 状态见任务回复或 Git。
