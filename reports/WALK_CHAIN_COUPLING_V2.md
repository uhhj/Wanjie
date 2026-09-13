# Walk 小腿与脚掌联动 V2

修复对象：用户指出的“脚掌变角度，小腿没有跟上”。技术及战斗尺寸连接检查完成；动作自然度仍待用户观看新版确认。

## 修复

上一版近侧脚在蹬地时相对小腿折了 42.19°，小腿轴近乎竖直。其屈膝曲线在离地瞬间返回低值，随后才开始收腿，使脚掌先独立转动。

本次提前在承重后半段屈膝，并连续带入离地收腿；随后平滑伸展。近侧足部轨迹向后修正 30 源像素，使膝和小腿能够跟进。所有调整均写入既有 Walk 关键帧，不改 rest pivot、骨长或资产。

| 近侧蹬地时（0.50s） | 前版 | 本版 |
|---|---:|---:|
| 小腿轴相对竖直，正值向后倾 | -1.5° | +12.6° |
| 脚掌世界角 | +28.0° | +18.0° |
| 踝部局部角 | +42.19° | +18.10° |

上身、骨盆、剑手、盾手、头部和独立膝甲的 Walk 键值保持一致。19 个部件、knee_near 附件、蒙皮、Rig 结构及其余四个动画均通过冻结校验。近膝形变范围没有扩大，步频、左右错相及每周期 387 源像素前进位移不变。

## 审查材料

- [256px 16帧跟随视角 GIF](walk_chain_v2/walk_reference_follow_256.gif)
- [192px 16帧跟随视角 GIF](walk_chain_v2/walk_reference_follow_192.gif)
- [蹬地/收腿前后对照，256px](walk_chain_v2/lower_leg_before_after_256.png)
- [256px 全16帧](walk_chain_v2/walk_reference_256_review.png) / [192px 全16帧](walk_chain_v2/walk_reference_192_review.png)
- [关键帧角度记录](walk_chain_v2/leg_chain_key_audit.json)

图片均来自实际 Godot GPU 渲染。对照图上排为上一版，下排为本版；标注的小腿角度是骨骼轴相对竖直，脚掌角度相对水平，数值来自动画键与 rest 轴几何。跟随视角地面向后移动，世界前进位移依然存在。前进视角原始帧和 GIF 也保留在同目录。

## 验证

- Godot 4.7.2 Stable headless 解析与原生测试 PASS，无脚本错误。
- 两个周期实际前进 774 源像素，暂停不移动，attack_hit 仍恰好 1 次。
- 支撑点最大漂移约 0.038px（256px），约 0.029px（192px）；支撑高度波动低于 0.05px（256px）。
- 助手检查两种尺寸及前后对照，小腿在抬跟时已跟进，未观察到新增明显关节缺口。此观察不代替用户的动作质量认可。
- [原生测试](walk_chain_v2/headless_tests.json)、[冻结校验与输出哈希](walk_chain_v2/walk_reference_metrics.json)、[脚底轨迹](walk_chain_v2/walk_foot_contact_debug.png)。

本次未重测旧桌面 FPS，未改其他动作、正式美术或 HIRES Alpha。

复现时依次运行数据生成器、`update_walk_keys.gd -- --walk-chain-v2`、`install_walk_key_resource.py reports/walk_chain_v2`；使用 `capture_native_animations.gd -- --walk-chain-v2` 与 `--walk-chain-v2-follow` 渲染。审查脚本接受 `reports/walk_chain_v2` 参数，另运行 `review_walk_chain_v2.py` 生成前后对照。
