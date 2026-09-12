# ROMAN_GUARD_ALPHA_MATTE_CLEANUP_V2

**Verdict：BLOCKED_LOCAL_ALPHA_TOUCHUP_ONLY。Complete Body Gate V3：FAIL。Godot Handoff：NOT_READY。**

本轮完成确定性 trimap、保守散点清理、局部距离/颜色 Alpha 估计及黑底 edge RGB 去污染。没有调用生成式 AI，没有修改主体设计、画布、内部不透明 RGB，没有执行 001–005。全局处理后的候选已经冻结；只剩五处已标注的局部边缘问题，没有再更改全局算法或开始 19 parts。

## 文件与完整性

- 只读 RGB：`D:\Wanjie\documents\Wanjie\work\05_complete_body_candidate_v2.png`
  SHA256：`042a00a27dac704b23ac0337ecdb27892edf7d490744ec9426ea4f3b44b647da`
- 初始 Alpha：`D:\Wanjie\documents\Wanjie\work\05_complete_body_candidate_v2_rgba.png`
  SHA256：`5939747ad6f41a2b372f8f4bcf912d76875a8d2548226d54738f1513d00f6a11`
- 本轮独立输出：`D:\Wanjie\documents\Wanjie\work\05_complete_body_candidate_v2_rgba_clean.png`
  SHA256：`df706ed02285e40b2532085d76e9936bba073eec0180e40bf63e94b35de26dfd`

| 指标 | 实测 |
|---|---:|
| 画布 / 格式 | 1024×1536 / PNG RGBA |
| Alpha=0 | 1,143,284 |
| Alpha=255 | 423,616 |
| Fractional Alpha | 5,964 |
| RGB 总改动像素 | 5,892 |
| Opaque RGB 改动像素 | **0** |
| Opaque RGB 最大差值 | **0** |
| Edge RGB 改动像素 | 5,892 |
| Edge RGB 最大差值 | 212（仅半透明窄带内；低 Alpha 去黑底后的直通颜色） |
| Sure foreground RGB 改动 | **0** |
| Unknown band 外 RGB / Alpha 改动 | **0 / 0** |

源 RGB、初始 RGBA、冻结 Rig Master 和历史阶段文件均保持不变。输入人物内的脸、甲胄、裙甲、手指及腿部颜色没有作为整体重绘或重新着色。

## 方法

从初始 `M=alpha>0` 构建 Euclidean disk 腐蚀 2px 的 sure foreground，膨胀 3px 外为 sure background。unknown band 为二者之间区域，共 31,182 像素；sure foreground 为 418,001 像素。保存 `work/masks/alpha_trimap_v2.png`，值 255/128/0 对应 SF/unknown/BG。

用 8 邻域组件分析保留斜向连接的细羽毛。仅直接删除距主组件超过 2px、面积不超过 16px、颜色仍很暗且不包含 sure foreground 的组件：**5 个组件、14 像素**。**33 个**靠近主体的组件没有被直接删点，而是留在 unknown band 判断。彩色细羽毛或固定前景受额外保护。

unknown Alpha 同时使用原几何、已确认边界连通背景、精确局部 Euclidean 最近前景距离和局部颜色投影。约 1px 的几何覆盖过渡产生半透明边缘；内侧邻接 sure foreground 的真实暗色边保留不透明。没有提高全局黑色阈值或使用整图/宽高斯模糊。若找不到近邻前景参考，保留原覆盖供审查，不凭空补色或删除彩色细羽毛。

仅在 unknown 且 `0<alpha<255` 的像素执行 RGB 去污染：以最近 sure foreground 为参考，对 `C/alpha` 做局部增益上限、RGB clamp 和参考颜色混合，权重为 alpha²；Alpha 越低越依赖参考。所有最终 opaque RGB 和 sure foreground RGB 均保持原值。

## Halo 对照与视觉判断

同一固定原轮廓 ring（向内 3px、向外 1px）、同一暗色/邻域亮度规则检测前后版本：疑似 halo **3,345 → 651**，下降约 **80.54%**。这是 debug 指标，真正黑色描边也可能被标记，不据此自动修图或认定 PASS。

已查看白、50% 灰、中蓝及棋盘四背景，以及 11 个精确 4x 局部条带。未见明显新增白边/亮边或人物身份漂移。

| 区域 | 视觉结果 |
|---|---|
| Plume | 尾部细羽毛保留；顶部仍有局部黑色凸点，需修补 |
| Helmet | PASS：后缘深色结构保持，未见明显误挖或亮边 |
| Shoulder | 上弧边缘有局部黑色凸点，需修补 |
| Hands | PASS：手指暗部、拳头与手腕连续，未见明显内部误透明 |
| Skirt | PASS：此前接缝修复保持，裙甲设计与红布边缘连续 |
| Legs | 近侧绑带保留；远侧护胫外缘有少量不规则黑色阶梯，需局部审查 |
| Boots | 两侧鞋底下方仍有小块/短段残留，需修补 |

## 五个局部目标

坐标为原画布 `[x0,y0,x1,y1]`，右下不包含。矩形仅用于定位，**不是允许整体修改的 mask**。

| ID | Bounding box | 问题与建议 |
|---|---|---|
| region_001 | [483,27,638,63] | 红冠顶部黑色凸点；逐点核对真实羽毛，处理其外侧残留，保留细羽毛 |
| region_002 | [326,381,445,415] | 肩甲上缘黑色凸点；沿原金属弧线清理外侧，保留暗描边 |
| region_003 | [682,1169,709,1282] | 远侧护胫黑色阶梯；逐段区分原甲边与外侧残留，不削薄腿形 |
| region_004 | [330,1448,442,1468] | 近侧鞋底扁块状残留；保持真实鞋底厚度与阴影，只修外侧短段 |
| region_005 | [686,1434,838,1459] | 远侧鞋底点状残留；不统一侵蚀鞋底，不提高全局阈值 |

局部修补仍须核对 trimap。若某处需要改动当前锁定的 sure foreground，应先单独标记该冲突，不能直接改动。此轮没有执行这些局部修补，也没有为获得通过而放宽锁定区域。

## 证据与后续门禁

- `reports/rgba_background_review_v2.png`
- `reports/rgba_edge_review_v2.png`：全部局部均为 4x；逐区域文件在 `reports/alpha_edge_details_v2/`
- `reports/alpha_trimap_review_v2.png`
- `reports/suspected_halo_overlay_v2.png`：紫色仅用于 debug
- `reports/alpha_manual_touchup_targets_v2.png` 和同名 JSON
- `reports/alpha_cleanup_metrics_v2.json`、`reports/alpha_cleanup_integrity_v2.json`
- `reports/complete_body_gate_v3.json`：16 项逐项检查，未全部 PASS

7 项测试 PASS，包括独立连通性/距离对照、细羽毛和不透明内部保护、当前输出像素级可复现。测试与数值完整性通过不等于边缘视觉通过。

19 Parts：NOT_STARTED，正式 0/19。Recomposition、Joint Tests：NOT_RUN。Godot Handoff：NOT_READY。现有正式人体来源、manifest 和 pivot 未切换；未创建正式 Rig、动画、插件或第二兵种。

当前分支 `feature/roman-guard-ai-rig-assets-v1` 正常新增提交并 push，不改写历史。准确 Commit SHA 和最终 Working Tree 状态见任务最终回复。
