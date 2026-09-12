# ROMAN_GUARD_AI_RIG_ASSET_PIPELINE_V1

**当前 Verdict：BLOCKED — STOP_ART_PIPELINE。Godot handoff：NOT_READY。**

冻结母图已导入，只读 SHA256 校验通过。已完成三次真实 AI 编辑、受 mask 约束的候选底版、三个原像素装备提取候选，以及可恢复执行的工程工具。底版存在裙甲拼接瑕疵和未经确认的颈甲结构，未被标记为正式素材。没有生成假的 19 件 PNG，也没有把失败素材接入 Godot。

项目位置：`D:\Wanjie\documents\Wanjie`。远端仓库：[uhhj/Wanjie](https://github.com/uhhj/Wanjie)。原始源文件：`D:\Wanjie\documents\pictures\OD_UNIT_01_ROMAN_GUARD_RIG_MASTER_V1.png`。所有后续工程文件与资产均在 D:\Wanjie\documents 内。

- [最终状态](reports/FINAL_VERDICT.md)
- [完整底版审查](reports/complete_body_review.md)
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
