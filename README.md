# ROMAN_GUARD_AI_RIG_ASSET_PIPELINE_V1

**当前 Verdict：BLOCKED_LOCAL_ALPHA_TOUCHUP_ONLY。Body Gate V3：FAIL；Godot handoff：NOT_READY。**

当前独立候选为 `work/05_complete_body_candidate_v2_rgba_clean.png`。trimap 窄带内完成局部 Alpha 估计和黑底 RGB 去污染：opaque RGB 改动为 0，边缘 RGB 改动 5,892 个像素，fractional alpha 5,964 个；同一规则检测的疑似 halo 从 3,345 降至 651。但红冠顶部、肩甲、远侧护胫和两侧鞋底仍有五处局部问题，已停止全局调整并标出修补目标。详见 [本轮清理报告](reports/ALPHA_MATTE_CLEANUP_V2.md) 和 [Body Gate V3](reports/complete_body_gate_v3.json)。

冻结母图与历史 001–003 保持原哈希。此前三次 AI 编辑和三个装备提取候选保留为历史产物；外部 V2 有独立的输入哈希和只读接收记录。正式 parts 仍为 0/19。旧版局部修复的阻塞原因与计划仅供历史追溯，不应再次执行。

项目位置：`D:\Wanjie\documents\Wanjie`。远端仓库：[uhhj/Wanjie](https://github.com/uhhj/Wanjie)。原始源文件：`D:\Wanjie\documents\pictures\OD_UNIT_01_ROMAN_GUARD_RIG_MASTER_V1.png`。所有后续工程文件与资产均在 D:\Wanjie\documents 内。

- [当前状态](reports/FINAL_VERDICT.md)
- [本轮四背景对照](reports/rgba_background_review_v2.png)
- [本轮 4x 边缘对照](reports/rgba_edge_review_v2.png)
- [五处局部修补目标](reports/alpha_manual_touchup_targets_v2.png)
- [RGB 源图视觉审查（已通过，历史）](reports/complete_body_review_v2.md)
- [上一轮修复门禁（历史）](reports/FIX_COMPLETE_BODY_GATE_V1.md)
- [局部编辑交接与续跑](docs/IMAGE_EDIT_MANUAL_HANDOFF.md)
- [16 件人体 mask 与装备隐藏区待办](docs/TODO_PART_MASK_REVIEW.md)

## 运行

依赖为 Python、Pillow、NumPy；参见 `requirements.txt`。在仓库根目录运行：

```powershell
python tools/run_validation.py
# 仅验证脚本行为的隔离测试：
python tools/test_pipeline_safety.py
```

本机普通 `python` 没有 Pillow。本轮已使用 Codex 自带 Python 验证：

```powershell
& 'C:\Users\Lenovo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' tools/run_validation.py
```

当前源图验证返回 0；素材/重组/关节/Godot 门禁返回 2，表示预期的美术阻断，不是工具崩溃。测试夹具隔离在 `work/test_runs/`，不属于正式资产且被 Git 忽略。

## 工具与真实行为

| 脚本 | 作用 |
|---|---|
| cleanup_roman_guard_alpha_v2.py | trimap、保守组件清理、局部距离/颜色 Alpha 估计和半透明 RGB 去污染；拒绝覆盖本轮候选 |
| review_alpha_cleanup_v2.py | 四背景、trimap、11 个精确 4x 局部条带和 halo debug |
| mark_alpha_touchup_targets_v2.py | 标注已观察到的五处局部问题，不修图 |
| test_alpha_cleanup_v2.py | 距离/组件、固定内部、细羽毛保护和实际输出复现检查 |
| convert_roman_guard_rgba.py | 从全部边缘做四邻域近黑连通分离，仅写独立输出 Alpha，RGB 不变 |
| validate_rgba_candidate.py | 检查 PNG/RGBA、画布、有效透明/不透明像素、边界、RGB 与连通性；不代替视觉审查 |
| generate_rgba_review.py | 生成黑/白/灰/棋盘效果和关键边缘放大图 |
| test_rgba_candidate.py | 对照独立 BFS，验证假 RGBA、内部误删、RGB 改动等被拒绝 |
| review_external_complete_body_v2.py | 只读生成外部候选全身/局部审查图和格式证据；不执行 AI 或自动授予美术 PASS |
| validate_source_asset.py | 检查源图存在性、SHA256、RGBA 与画布；不覆盖源图 |
| generate_or_manage_masks.py | 从真实 polygon 或导入 mask 管理拆件边界；底版失败时拒绝人体拆件 |
| ai_inpaint_roman_guard.py | 准备真实工具输入、导入真实返回图、保护 mask 外像素、归档阶段和恢复流水线；不是虚构的图像 API |
| normalize_part_canvas.py | 以明确 offset 补齐同画布 RGBA，禁止自动拉伸和猜测位置 |
| extract_roman_guard_parts.py | 优先提取真实源像素，分别管理候选和正式发布 |
| validate_parts.py | 19 件、来源、hash、透明通道、画布和美术审查门禁 |
| recompose_roman_guard.py | 实际 draw passes 重组、轮廓/位置/RGB 对比、diff 图；缺件时 NOT_RUN |
| generate_joint_rotation_test.py | 肘膝 ±20° 与 0°；前臂连带手和武器旋转；膝连带小腿与脚；盾 socket、剑 20°/30°；启发式连续性检查加视觉审查 |
| record_art_review.py | 用当前文件 SHA256 记录实际 PASS/FAIL，防止旧审查被复用 |
| check_godot_handoff.py | 检查全部当下结果与绘制配置，再决定 READY/NOT_READY |

19 个 core part 和初始 pivot 已登记，但人体边界尚不可靠。未创建任何空白部件 mask 去填数。完整底版必须通过之后才能沿正确来源拆分。

一个 cape PNG 同时包含后摆与前领，重组使用两次互斥 mask 绘制同一核心纹理；它仍是 19 个核心部件之一。这个 draw order 提案也必须在实际重组时审查。没有新增兵种、第三方骨骼插件或自动安装 Godot。

## Godot 后续

用户已确认从零建立仓库，并将仓库名称更正为 `Wanjie`（GitHub 所有者为 `uhhj`）；原有 `ROMAN_GUARD_NATIVE_RIG_VERTICAL_SLICE_V1` 和 `HUMAN_MEDIUM_RIG_V1` 工程文件不在本机任务中。只有素材 READY 后，才创建 Godot 4.7.2 Stable 原生 Skeleton2D/Bone2D 场景和 idle、walk、attack_01、hit、death。当前没有创建占位骨骼、动画或伪称已经接入。

API key 不在工程内。`.env`、密钥文件和运行缓存被忽略。`origin` 为 `https://github.com/uhhj/Wanjie.git`，工作分支为 `feature/roman-guard-ai-rig-assets-v1`。AI 调用记录中的旧本地路径保留为调用时的真实历史，不因仓库改名而改写。
