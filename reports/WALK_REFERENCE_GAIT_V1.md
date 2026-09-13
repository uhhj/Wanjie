# Walk 参考步态 V1

技术与战斗尺寸连接检查通过；新版动作自然度尚待用户观看确认。

输入为用户提供的姿态参考条。本次提取的是后脚抬跟、前脚承重、后腿收回的动作关系，沿用当前三分之四视角的冻结美术。参考条主要是同侧腿的相近姿态，因此补齐另一条腿相差半周期的完整循环。

## 本次变化

- 足部增加后足接地、放平承重、抬跟与前脚掌蹬地；世界足部角度约 -12° 至 +28°。
- 摆动腿在身后先屈膝收回，再通过身体下方、向前放脚。屈膝峰值提前，未增大已批准近膝形变上限。
- 骨盆 0–7 源像素起伏改为落脚后承重下沉、通过后抬升，保留轻微重心变化及上身补偿。
- 维持 1 秒步频、387 源像素每周期位移、49 个关键姿态与左右脚半周期错相。持剑臂、盾牌和头部保持上一版的小幅动作。

仅更新 Walk 既有轨道的键值。Rig 节点、near_knee pivot/权重、正式部件、Complete Body 和其余四个动画均验证未变；`.tscn` 与 `.tres` 中 Walk 子资源以外的文本一致。没有生成式图像调用。

## 实际渲染

每份 GIF 为 **16 帧、1000ms**，使用 Godot 4.7.2 Stable / GTX 1650 实际 GPU 渲染。

| 尺寸 | 跟随视角，适合连续观察 | 前进视角 | 16帧审查图 |
|---|---|---|---|
| 256px | [GIF](walk_reference_v1/walk_reference_follow_256.gif) | [GIF](walk_reference_v1/walk_reference_256.gif) | [PNG](walk_reference_v1/walk_reference_256_review.png) |
| 192px | [GIF](walk_reference_v1/walk_reference_follow_192.gif) | [GIF](walk_reference_v1/walk_reference_192.gif) | [PNG](walk_reference_v1/walk_reference_192_review.png) |

跟随视角使用 Camera2D；地面刻度相对角色向后移动，前进位移仍然存在。前进视角 GIF 在一个周期结束后返回屏幕起点，此显示重置不参与步态滑步检测。

## 验证

- Headless 场景解析与原生测试 PASS；attack_hit 仍恰好 1 次。
- 实际运行两周期前进 774 源像素；暂停无额外位移。
- 鞋底轮廓以冻结前向鞋的五个校准点近似。检测每个实际接地材料点的世界位置，足部滚动时切换接触点，并独立检查支撑高度。
- 256px 最大接触点漂移 **0.0882px**；192px **0.0662px**。支撑高度变化约 **0.09px**（256px）。两侧各覆盖四段接触点区间。
- 助手检查了两种尺寸的实际帧，未观察到新增明显肢体断裂，抬跟、收腿与交替支撑可辨。此结论不代替用户对动作自然度的判断。
- [脚底轨迹](walk_reference_v1/walk_foot_contact_debug.png)、[原始测试](walk_reference_v1/headless_tests.json)、[冻结验证与输出哈希](walk_reference_v1/walk_reference_metrics.json)。

本次没有重新运行桌面压力测试。历史 FPS 保留为旧基线。旧“将就了吧”的质量保留意见继续保留，不能当作用户已经认可本次参考步态。五处 HIRES 美术瑕疵保持非阻塞。

## 复现

1. `python tools/build_native_rig_data.py`
2. Godot `--headless --path . --script res://scripts/build/update_walk_keys.gd -- --walk-reference`
3. `python tools/install_walk_key_resource.py`（只替换 Walk 子资源）
4. Godot `--headless --path . --script res://scripts/tests/test_native_rig.gd`
5. Godot `--path . --script res://scripts/tests/capture_native_animations.gd -- --walk-reference`，另以 `--walk-reference-follow` 导出跟随视角。
6. `python tools/review_walk_reference_v1.py`；生成技术验证和审查材料，视觉审批须另行记录。

原始参考、改动前动画、冻结文件 SHA256、原生逐帧截图均保留在 `walk_reference_v1/`。
