# 外部 Complete Body V2 验收

**Verdict：BLOCKED。十项视觉检查 PASS；Complete Body 生产门禁 FAIL（缺少 RGBA 透明通道）。Godot handoff：NOT_READY。**

本轮只读接收用户在外部完成的修复候选。没有调用 AI，没有重跑 001–005，没有改动候选图片。外部工具/模型和中间 04 未提供，不能据此补写虚构的 AI 调用记录；此前 004/005 的 NOT_RUN 是本地调用历史，本轮保留。

## 文件证据

- 候选：`D:\Wanjie\documents\Wanjie\work\05_complete_body_candidate_v2.png`
- SHA256：`042a00a27dac704b23ac0337ecdb27892edf7d490744ec9426ea4f3b44b647da`，读取前后相同。
- PNG，1024×1536，与冻结母图画布一致；实际模式为 **RGB**，只有 R/G/B 三个通道，没有 Alpha。
- 图中黑底是实际 RGB 像素，不是透明预览。左上角 RGB=(0,0,0)，左下角=(1,2,1)，不能将黑色阈值去除当成已经存在的真实透明边界。
- 已实际调用现有 `tools/rg_common.py` 的 `rgba()` 读取检查，结果为 `must be RGBA; conversion alone cannot establish transparency`。
- 原任务阶段 C 要求透明背景，现有流水线也要求底版同画布 RGBA。仅把 RGB 模式转换为 RGBA 会保留不透明黑底，不满足要求。本轮遵守“不要修改该图片”，没有转换、抠图或覆盖原件。

## 十项视觉检查

查看候选全图、同坐标局部对照，并按 DESIGN_V1 → RIG_MASTER_V1 → COMBAT_LOOK_V1 复核可见设计；未使用 CODEX 原画。

| 检查 | 结果 | 实际观察 |
|---|---|---|
| 1. 无盾牌 | PASS | 原持盾侧手臂与拳头可见，无盾牌主体或残留边框 |
| 2. 无短剑 | PASS | 持剑手下方无剑刃、护手或柄尾 |
| 3. 无披风 | PASS | 后摆、颈肩红色围布和披风扣已移除 |
| 4. 双手完整 | PASS | 两侧拳头、手腕及前臂连续，无明显缺失或断开 |
| 5. 双腿完整 | PASS | 双侧大腿、护胫、踝部与双脚可见，站姿完整 |
| 6. 裙甲连续 | PASS | 原 03 的斜向三角形拼接已消除；暗红布褶、下摆及上大腿过渡连续 |
| 7. 颈肩/胸甲一致 | PASS | 裸露颈部过渡到低胸甲上缘，保留原肩甲与胸甲的可见主体结构；未见独立新增领圈 |
| 8. 无此前高领甲 | PASS | 原 03 围绕颈部竖起的金边铁灰领甲已消失 |
| 9. 无新装备幻觉 | PASS | 未观察到新的武器、独立肩甲、颈甲或其他新增装备类别 |
| 10. 身份与比例一致 | PASS | 朝向、面部身份、头盔轮廓、红冠、胸甲主体、站姿和腿长未见明显漂移 |

视觉 PASS 表示没有观察到上述结构/身份缺陷，不表示隐藏设计被逐像素证实。颈肩在冻结参考中受布料遮挡，检查依据是与可见结构的合理衔接，没有把被遮挡的细节虚构为确定的原设计。

候选在脸、头盔、手和护胫等修复范围之外也有 RGB 像素差异，局部细节观感较柔和。数值记录见 `reports/external_complete_body_v2_intake.json`。这不等于证明换脸、全图重绘或某种外部处理方式；本轮未因像素不完全一致而伪报身份漂移。RGB 黑底也无法提供可靠的 Alpha 外轮廓对比。

## 门禁与下游

`reports/complete_body_gate_v2.json` 将美术和文件条件分开记录：`visual_checks_status=PASS`，四项美术 pass=true；`technical_requirements_pass=false`，总 `status=FAIL`。唯一确认的当前生产阻塞是缺少真实透明 RGBA。

正式 parts：required 19 / passed 0 / missing 19。既有 3 件装备提取候选不计正式通过。本轮未创建 19 件 mask、未提取正式部件、未变更人体生产来源/正式 manifest/pivot、未执行重组或关节测试，也未创建 Godot Rig 或动画。

## 审查图片与恢复点

- `D:\Wanjie\documents\Wanjie\reports\complete_body_review_v2.png`：冻结母图与外部 V2，同画布、同显示比例。
- `D:\Wanjie\documents\Wanjie\reports\complete_body_detail_review_v2.png`：冻结母图、旧 03、外部 V2 的同坐标头部、颈肩、裙甲和腿部对照。

保留本次 RGB 原件。从外部修复工程导出同尺寸、同构图、真实透明 RGBA 的独立文件后，再以新文件进行验收。不要只加一个全不透明 Alpha 通道，不需要重绘角色或重跑 001–005。通过透明背景/边缘与当前十项视觉复核后，才能切换正式人体来源并继续原有 19 部件流水线。

冻结源图及 001–003 的 SHA256 均未变。候选与审查图的哈希、只读完整性证据见 `reports/external_complete_body_v2_intake.json`。本轮提交并 push 当前分支，具体 Commit SHA 和最终 Working Tree 状态见任务回复。
