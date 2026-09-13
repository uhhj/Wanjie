# ROMAN_GUARD_AI_RIG_ASSET_PIPELINE_V1

## 当前 Native Rig V2

Walk 最新小幅关键帧调整：[256px 16帧GIF](reports/walk_polish_v1/walk_polish_256.gif) / [192px 16帧GIF](reports/walk_polish_v1/walk_polish_192.gif) / [变更与完整审查](reports/WALK_KEYFRAME_POLISH_V1.md)。Rig和素材保持冻结。

已建立 Godot 4.7.2 Stable Standard 原生 Skeleton2D/Bone2D/AnimationPlayer 工程、五动画、Rig Lab 和桌面压力测试。最新视觉状态与技术证据以 [Native Gate V2](reports/native_rig_v2/native_gate_v2.json) 为准；以下资产报告属于已通过的冻结输入，不代替动画验收。

本轮按用户“将就了吧”的反馈作为可用战斗原型收口，保留动作质感未达到精修成品的说明。SUPPORTED 是原生流水线可行性结论，不应解读为无保留的美术质量认可。

- [通用骨骼、坐标和局部蒙皮](docs/HUMAN_MEDIUM_RIG_V1.md)
- [动画、支撑脚、事件和运行方式](docs/ROMAN_GUARD_ANIMATION_V1.md)
- [最新 Walk：16帧关键帧微调](reports/walk_polish_v1/walk_polish_256.gif)
- [最新 Attack：举盾与肩部连接](reports/animations/attack_closed_shoulder_v4_256.gif)
- [Death](reports/animations/death_256.gif)

在仓库根目录运行 `./tools/run_godot_native.ps1 -Action Lab`。`Validate` 执行原生测试，`Stress` 打开压力实验室，`Benchmark` 运行 20/50 单位五模式实测。引擎位于 `D:/Wanjie/tools/Godot/4.7.2/`，已核对官方版本与发布包校验和。

19 核心件和独立 knee_near 的正式 PNG 没有修改。动作中暴露的两侧肩部与右脚踝用局部原生蒙皮处理；Walk 右鞋使用已批准左鞋像素的前向视图，其他动作保留原鞋。当前分支为 `feature/roman-guard-native-rig-v2`。

## 冻结资产阶段

**当前：近侧膝关节五档运动PASS。19个核心件+独立knee_near，共20件；资产交接READY。**

近侧膝甲固定在独立socket，小腿使用随附的局部双骨权重。thigh/shin重叠仍约32.9%，0°重组逐像素不变；其余关节和装备冻结。当前近膝结果以 [局部修复报告](reports/NEAR_KNEE_ARTICULATION_V1.md)、[256px五档](reports/near_knee_motion_256px_v1.png)、[192px五档](reports/near_knee_motion_192px_v1.png) 为准。旧V3近膝刚性旋转审批已被替代，不得复用于新布局。

本轮局部生产脚本为 `refine_near_knee_v1.py`，蒙皮数据为 `assets/units/odyssey/roman_guard/near_knee_skinning_v1.json`。接入时必须使用这些权重；不接受重新让膝甲随shin大幅旋转。复验使用 `run_validation.py` 与 `test_near_knee_v1.py`，无需重跑其他已通过资产的渲染。以下保留原19核心件流水线说明。

Complete Body保持PASS_WITH_NON_BLOCKING_HIRES_EDGE_ARTIFACTS，五处Alpha问题非阻塞。只重分了指定八个肘膝部件，建立约32%–33%真实像素重叠并校准四个pivot；256px和192px运动检查通过。

完整短剑已用独立握柄补全结果制作成真实RGBA，保留原剑刃及金属件像素；盾牌与其余纹理未重做。正式19件全部为1024×1536 RGBA，位于 `assets/units/odyssey/roman_guard/parts/`。

- [完整修复与验收报告](reports/ARTICULATED_PART_FIX_V1.md)
- [Pivot与重叠](reports/joint_pivot_review_v3.png)
- [256/192px关节审查](reports/joint_rotation_combat_scale_v3.png)
- [完整短剑](reports/full_sword_review_v1.png)
- [256px重组](reports/recomposition_256px_v3.png)
- [192px重组](reports/recomposition_192px_v3.png)
- [当前交接](docs/IMAGE_EDIT_MANUAL_HANDOFF.md)

项目为 `D:\Wanjie\documents\Wanjie`，远端：[uhhj/Wanjie](https://github.com/uhhj/Wanjie)。新COMBAT_RIG_V3门禁按战斗尺寸视觉、结构审批和哈希证据计算；历史像素级指标保留诊断，不再阻塞。旧失败报告保留历史，当前状态以 `reports/final_status.json` 为准。

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

当前源图、正式部件、重组、关节和Godot交接门禁均返回0。测试夹具隔离在 `work/test_runs/`，不属于正式资产且被 Git 忽略。

## 工具与真实行为

| 脚本 | 作用 |
|---|---|
| review_combat_scale.py | 只读生成256/192/128px角色高度的白/灰底审查，不再修补Alpha |
| build_body_part_candidates.py | 从已通过的身体生成可审查可见像素边界与真实关节重叠，拒绝覆盖候选 |
| review_part_candidates.py | 在正式审批之前运行真实候选的格式、重组和18种运动诊断，不授予正式PASS |
| test_combat_gate.py | 验证审批哈希失效、显示尺寸证据与Combat/Artwork范围隔离 |
| review_articulated_v3.py | 渲染原分辨率、256/192px肘膝、盾剑与重组证据；扩大预览视口而不改PNG画布 |
| sword_completion.py | 验证原金属件与局部生成握柄的精确装配来源，阻止改剑刃冒充补全 |
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
| validate_parts.py | 19核心件及显式新增膝甲、来源、hash、透明通道、画布和美术审查门禁 |
| recompose_roman_guard.py | V3模式核验正式部件与战斗尺寸重组证据；旧模式保留历史渲染路径 |
| generate_joint_rotation_test.py | V3模式核验已渲染的关节动作证据及当前pivot/part哈希；旧模式保留原测试路径 |
| record_art_review.py | 用当前文件 SHA256 记录实际 PASS/FAIL，防止旧审查被复用 |
| check_godot_handoff.py | 检查全部当下结果与绘制配置，再决定 READY/NOT_READY |

19个正式部件、masks与pivot均通过当前Combat范围审批；候选和历史版本仍独立保留。

一个 cape PNG 同时包含后摆与前领，重组使用两次互斥 mask 绘制同一核心纹理；它仍是 19 个核心部件之一。没有新增兵种或第三方骨骼插件。

## 工程来源

用户确认从零建立仓库，并将名称更正为 `Wanjie`（GitHub 所有者 `uhhj`）。原有 V1 工程不在本机；本次在资产 READY 后建立新的 Native Rig V2，未引用不存在的旧工程。

API key 不在工程内。`.env`、密钥文件和运行缓存被忽略。`origin` 为 `https://github.com/uhhj/Wanjie.git`；资产分支 `feature/roman-guard-ai-rig-assets-v1` 保留原历史。AI 调用记录中的旧本地路径保留为调用时的真实历史。本次 Native 动画修复没有生成式 AI 调用。
