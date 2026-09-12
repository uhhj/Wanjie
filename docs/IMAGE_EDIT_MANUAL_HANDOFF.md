# 当前交接：RGBA_BACKGROUND_CONVERSION_V1

**Verdict：BLOCKED_ALPHA_MATTE_REVIEW。格式 PASS，Alpha 边缘视觉 FAIL。**

已在用户授权下，仅用确定性四邻域边界连通背景分离生成：

`D:\Wanjie\documents\Wanjie\work\05_complete_body_candidate_v2_rgba.png`

输出为同画布 1024×1536 RGBA，真实 Alpha 0/255，原人物 RGB 逐像素不变。只读 RGB 源仍为 `work/05_complete_body_candidate_v2.png`，其十项视觉 PASS 保留。

当前问题已经不是缺少 Alpha 通道。阈值 2 的白底/灰底审查显示，冠饰、肩甲外缘和鞋底仍有不规则黑色残留和散点；提高阈值又会穿入与背景相连的暗色描边。本轮已按用户 STOP 规则结束进一步修改；不得把格式 PASS 当作 Alpha 美术 PASS。

下一步只审查/修正 Alpha 边缘分类。继续保留当前 RGB、现有 RGBA 失败证据和角色设计，不能重新生成角色、重跑 001–005、覆盖原图或盲目提高阈值。完整十五项 Body Gate 必须等待 Alpha 审查通过；当前 19 parts、重组、关节测试和 Godot 均未解锁。

查看：

- [本轮完整报告](../reports/RGBA_BACKGROUND_CONVERSION_V1.md)
- [白/灰/棋盘对照](../reports/rgba_background_review.png)
- [边缘审查](../reports/rgba_edge_review.png)
- [头盔与鞋底细节](../reports/rgba_critical_edge_detail.png)
- [容差风险对照](../reports/alpha_tolerance_review.png)
- [格式验证](../reports/rgba_candidate_validation.json)
- [Alpha 视觉判定](../reports/rgba_visual_review.json)

本轮不使用生成式 AI。外部 RGB 原件、冻结源图和历史 AI 记录不变。转换脚本拒绝覆盖像素不同的已有输出；需要任何后续修正时，应先明确新的独立候选路径并保留失败证据。
