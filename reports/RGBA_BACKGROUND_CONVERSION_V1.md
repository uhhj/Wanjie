# ROMAN_GUARD_RGBA_BACKGROUND_CONVERSION_V1

**Verdict：BLOCKED_ALPHA_MATTE_REVIEW。格式验证 PASS，透明边缘视觉审查 FAIL。Complete Body Gate：FAIL；Godot handoff：NOT_READY。**

本轮完成确定性 Alpha 转换，并保存同画布真实 RGBA 候选。没有调用生成式 AI，没有执行 001–005，没有修改 RGB 原件或任何人物 RGB 像素，没有开始 19 parts。按用户规定，发现明显边缘问题后停止，没有以格式通过替代美术通过。

## 输入与输出

| 属性 | 只读视觉源文件 | RGBA 候选 |
|---|---|---|
| 路径 | `D:\Wanjie\documents\Wanjie\work\05_complete_body_candidate_v2.png` | `D:\Wanjie\documents\Wanjie\work\05_complete_body_candidate_v2_rgba.png` |
| SHA256 | `042a00a27dac704b23ac0337ecdb27892edf7d490744ec9426ea4f3b44b647da` | `5939747ad6f41a2b372f8f4bcf912d76875a8d2548226d54738f1513d00f6a11` |
| 模式 | PNG / RGB | PNG / RGBA |
| 画布 | 1024×1536 | 1024×1536，未缩放或移动 |
| Alpha min / max | 无 Alpha | 0 / 255 |
| 全透明像素 | 无 | 1,142,490 |
| 全不透明像素 | 无 Alpha | 430,374 |
| 部分透明像素 | 无 | 0，未羽化 |

人物 RGB 改动像素数为 **0**，包括透明区域内存储的 RGB 也逐像素保留。非透明包围盒为 `[258, 29, 848, 1465]`（右下坐标不包含），不触碰画布边缘。

## 确定性方法

从四个 32×32 角块和整圈画布边缘采样。四角 RGB 中位数均为 (0,0,0)，整圈边缘单通道最大值为 2，确认属于同一黑色背景分布。

最终使用最保守、能覆盖实测边缘颜色的阈值：`max(R,G,B) <= 2`（每通道 0–255）。仅将该候选集合中能从任一画布边缘像素通过上下左右四邻域到达的区域设为 Alpha=0；其余 Alpha=255。采用 scanline flood fill，没有把所有黑色像素透明化，没有清除不连通的暗色区域，没有修色、形态学切除或整体模糊。

**10,521 个**不与背景连通的近黑像素保持完全不透明。该保证仅适用于“不连通”的像素，不能证明与背景相连的每一处暗色描边都已正确分类。

## 视觉结果

已查看白底、50% 灰底、棋盘背景，以及冠饰、头盔、肩甲、双手、裙甲、双腿和鞋底放大对照。

- **FAIL — 黑色残留/halo**：红冠上缘、肩甲外缘及鞋底附近可见不规则黑色边缘、散点和凸出小块；白底/灰底上明显。鞋底放大图尤其清楚，不能直接标记为正式干净边缘。
- **描边保留尚未批准**：最终阈值 2 保留了头盔后缘和鞋底的主体暗部，未见较高阈值造成的那种大面积镂空；但边界处原有描边和背景残留尚不能仅靠颜色连通性可靠区分。
- **内部暗色区域**：最终候选中可见手指、甲片缝隙和裙甲内部阴影仍存在；所有不连通近黑像素的 Alpha=255 已数值验证。这不是对整个 Alpha matte 的通过判定。

诊断容差 6 / 10 / 14 / 18 的对照保存在 `reports/alpha_tolerance_review.png`。提高阈值确实能去除部分边缘残留，但也会沿相连的暗色描边进入头盔、盔甲或鞋部；14/18 出现明显透明裂线，6/10 的头盔后缘也受损。因此没有提高最终阈值来隐藏黑边问题，也没有用更宽的模糊修饰结果。最终输出固定为阈值 2 的未批准候选。

## 验证和门禁

`tools/validate_rgba_candidate.py` 已实际运行并 PASS：文件存在、PNG、RGBA、同画布、Alpha 0/255、透明/不透明像素各超过画布 1%、包围盒非空且不触边、RGB 未改、Alpha 与边缘连通背景一致；拒绝全 255 假 RGBA。

`tools/test_rgba_candidate.py` 的 10 项测试 PASS，覆盖独立 BFS 对照、四邻域不穿越对角、内部黑区保留，以及全不透明、全透明、内部阴影误删、RGB 修改、画布变化和边缘前景等失败情况。测试结果不代表人物边缘通过。

依用户“只有 RGBA 转换审查通过后才重新运行完整 Body Gate”的顺序，本轮未运行完整十五项 Body 复验；当前 `reports/complete_body_gate_v2.json` 记录前置 Alpha 审查失败，总门禁保持 FAIL。原 RGB 的十项视觉 PASS 作为带 SHA 的源图审查保留，不被改写为失败，也不冒充新 Alpha 的通过证据。

19 Parts：NOT_STARTED，正式 0/19；Recomposition：NOT_RUN；Joint Tests：NOT_RUN；Godot Handoff：NOT_READY。人体生产来源、正式部件、manifest、pivot 和既有 AI 调用记录均未改动。

## 审查文件

- `D:\Wanjie\documents\Wanjie\reports\rgba_background_review.png`
- `D:\Wanjie\documents\Wanjie\reports\rgba_edge_review.png`
- `D:\Wanjie\documents\Wanjie\reports\rgba_critical_edge_detail.png`
- `D:\Wanjie\documents\Wanjie\reports\alpha_tolerance_review.png`

转换记录：`reports/rgba_conversion.json`；格式验证：`reports/rgba_candidate_validation.json`；视觉判定：`reports/rgba_visual_review.json`。下一步需要审查并修正 Alpha 边缘分类，继续保留 RGB 和角色设计；本轮依 STOP 规则不继续尝试、拆件或接入 Godot。

Git：继续 `feature/roman-guard-ai-rig-assets-v1`，新增真实转换与失败审查证据提交并正常 push；不改写历史。准确提交 SHA 与最终 Working Tree 状态见任务最终回复。
