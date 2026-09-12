# ROMAN_GUARD_AI_RIG_ASSET_PIPELINE_V1

**Combat Body Gate：PASS_WITH_NON_BLOCKING_HIRES_EDGE_ARTIFACTS。整体Verdict：BLOCKED（部件关节与隐藏区域）。Godot Handoff：NOT_READY。**

已按256/192/128px实际角色高度通过白底和50%灰底验收。五处高分辨率Alpha问题保留并标为NON_BLOCKING_COMBAT_ARTIFACT，停止局部Alpha修补。当前身体候选与冻结源文件均未修改。

已继续生成19个真实像素部件候选和masks，完成重组与18种运动预览。全部候选为同画布RGBA，但膝肘隐藏面和握柄等尚未通过美术/旋转门禁，正式批准仍为0/19。详细结果与续跑边界见以下材料。

- [当前完整报告](reports/COMBAT_SCALE_VISUAL_GATE_V1.md)
- [100%实际尺寸审查](reports/combat_scale_visual_review.png)
- [重组对照](reports/recomposition_combat_review_v2.png)
- [真实候选运动测试](reports/joint_rotation_test_v2.png)
- [部件局部问题](reports/part_art_review_v2.json)
- [当前交接](docs/IMAGE_EDIT_MANUAL_HANDOFF.md)
- [历史高分辨率Alpha报告](reports/ALPHA_MATTE_CLEANUP_V2.md)

项目：`D:\Wanjie\documents\Wanjie`。远端：[uhhj/Wanjie](https://github.com/uhhj/Wanjie)。当前完整人体来源由 `tools/pipeline_config.json` 的 `complete_body_source` 指定。001–005历史保持不变，不能用历史失败底版覆盖当前通过候选。

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
| review_combat_scale.py | 只读生成256/192/128px角色高度的白/灰底审查，不再修补Alpha |
| build_body_part_candidates.py | 从已通过的身体生成可审查可见像素边界与真实关节重叠，拒绝覆盖候选 |
| review_part_candidates.py | 在正式审批之前运行真实候选的格式、重组和18种运动诊断，不授予正式PASS |
| test_combat_gate.py | 验证审批哈希失效、显示尺寸证据与Combat/Artwork范围隔离 |
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

19个真实像素候选、masks与pivot已建立；关节旋转暴露的局部缺口尚未通过。未创建空白部件填数，候选与正式发布保持分离。

一个 cape PNG 同时包含后摆与前领，重组使用两次互斥 mask 绘制同一核心纹理；它仍是 19 个核心部件之一。这个 draw order 提案也必须在实际重组时审查。没有新增兵种、第三方骨骼插件或自动安装 Godot。

## Godot 后续

用户已确认从零建立仓库，并将仓库名称更正为 `Wanjie`（GitHub 所有者为 `uhhj`）；原有 `ROMAN_GUARD_NATIVE_RIG_VERTICAL_SLICE_V1` 和 `HUMAN_MEDIUM_RIG_V1` 工程文件不在本机任务中。只有素材 READY 后，才创建 Godot 4.7.2 Stable 原生 Skeleton2D/Bone2D 场景和 idle、walk、attack_01、hit、death。当前没有创建占位骨骼、动画或伪称已经接入。

API key 不在工程内。`.env`、密钥文件和运行缓存被忽略。`origin` 为 `https://github.com/uhhj/Wanjie.git`，工作分支为 `feature/roman-guard-ai-rig-assets-v1`。AI 调用记录中的旧本地路径保留为调用时的真实历史，不因仓库改名而改写。
