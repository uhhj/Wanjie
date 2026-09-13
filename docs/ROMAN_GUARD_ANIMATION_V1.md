# Roman Guard 原生动画 V1

动画源：`resources/roman_guard_animations_v1.json`。正式 AnimationLibrary：同目录 `.tres`，由 Godot builder 写入单位场景。所有动作明确 key 全部骨骼，防止切换后残留上一动作的角度。美术 PNG、Complete Body 和 near knee 权重保持冻结。

| 动画 | 长度 | 循环 | 行为 |
|---|---:|---|---|
| idle | 1.6s | 是 | 1.5 源像素呼吸、很小的盾剑/头盔/披风摆动 |
| walk | 1.0s | 是 | 真实向右前进，双腿相差半周期，持剑臂前后摆动，躯干轻微反向补偿，盾手稳定 |
| attack_01 | 0.8s | 否 | 先举盾，再抬高持剑手大幅前刺，恢复防御后回 idle |
| hit | 0.32s | 否 | 小幅后仰和盾牌震动，结束回 idle |
| death | 1.1s | 否 | 后仰、屈膝失衡、折倒、落地回弹、保持终姿；少量血滴 |

## Walk

用户选定真实向前行走。Walk 关键帧微调后每周期前进 387 个源画布像素（比原版增加7.5%），即角色高 256px 时约 69.04px/s，192px 时约 51.78px/s。`RomanGuard` 从 AnimationPlayer 的实际播放位置消费位移；倍率、暂停和循环边界一致，不使用另一个猜测步速的 timer。

站姿右鞋原本朝外；Walk 的右鞋改用左鞋的批准像素作为前向显示变体，绑定到右脚关节。两脚行进朝向一致，而不是只把原来朝外的鞋图上下转动。两脚在摆动中均略抬脚尖，支撑阶段落平。该变体只影响 Walk，其他动作的原鞋图保持不变。

近脚支撑区间 [0,0.5)，远脚 [0.5,1.0)。支撑阶段的局部脚位移与前进速度相反且相等，因此世界位置锁定。摆动阶段使用匹配起落速度的 Hermite 水平轨迹和 34 源像素抬脚高度（原为30）。两个脚有不同投影通道，保留三分之四视角深度。对齐的是各自地面投影，不强迫两个源图鞋底处于同一 y。

本次仅微调 Walk 现有关键帧：骨盆上下范围从0–4增为0–7源像素，前后变化±1.5源像素；躯干轻微反向补偿，头部抵消85%的躯干转动；持剑上臂幅度增加0.8°，盾臂加入0.3°的极轻微惯性并保持盾牌朝向。保持1秒周期、49个关键姿态、原支撑区间、Rig结构、near_knee、部件和其他四动画不变。最新[16帧审查](../reports/WALK_KEYFRAME_POLISH_V1.md)取代旧Walk GIF；此前桌面FPS仍为基线，本次未重跑压力测试。

离线解算 48 个区间的关键姿态，没有运行时 IK。髋轴位于裙甲内部；关键帧中小幅髋部升降配合重心与抬脚，骨骼长度不变，不增加接缝覆盖。双膝都向角色朝向前屈。持剑上臂约 ±11.8°，前臂配合；躯干约 ±1.2°，远上臂反向抵消躯干变化。远脚摆动时脚尖最多抬 10°，着地回到水平；踝部局部双骨权重连接鞋筒与小腿，不再让整张鞋图刚性反转出明显折角。

`reports/walk_foot_contact_debug.png` 和 `headless_tests.json` 记录真实 Godot 骨骼世界点，不把局部脚滑误算成无滑步。自动测试还通过实际 runtime 位移消费者跑两整周期，验证总位移和每个支撑区间；暂停不平移。

Rig Lab 在跑道边界重新放置展示单位；Stress 在固定展示范围循环排列。该展示边界重置不属于步态，也不参加支撑脚锁定测量。GIF 展示一个周期，循环播放时回到起始屏幕位置；真实 Lab 连续向前走。

## Attack 与事件

0–0.15s 举盾蓄力；约 0.28s 开始前送；0.36–0.50s 肩肘伸展并保持上胸前的盾；0.62s 收剑；0.80s 回防御。关键峰值上臂 -95°、前臂 -14°、手腕反向补偿，形成明确的横向刺击。双肩使用只改变绑定的局部蒙皮，保留原肩甲和胸甲边缘，防止整块护甲旋走露出白色背景。剑柄始终通过 hand_near/sword_socket 连接，盾牌通过 far 链上举。

唯一 method key 位于 0.40s，调用 `RigEventRelay._event_attack_hit()`，只发 `attack_hit`。每次 attack 播放 counter 必须等于 1。没有命中检测、伤害、timer 或兵种脚本猜时间。idle/walk/hit/death 没有 attack_hit key。

## Death

保持用户认可的 1.1s 分阶段倒地：受击后仰，双腿不对称失衡，躯干折倒，装备下沉，接触地面后轻微回弹并停止。装备仍跟随手，不做物理掉落或 ragdoll。最终 y 通过冻结部件 alpha 外轮廓计算地面接触，不以整个人换角度作为唯一动作。

`scripts/rig/death_blood.gd` 是独立原生绘制效果，7 个小型暗红血滴/短线，AnimationPlayer 的浮点 phase 驱动，约 0.12–0.65s 出现并消退，不修改角色纹理，也不添加新动画。

## 操作和证据

```powershell
# 仓库根目录
./tools/run_godot_native.ps1 -Action Lab
./tools/run_godot_native.ps1 -Action Validate
./tools/run_godot_native.ps1 -Action Stress
./tools/run_godot_native.ps1 -Action Benchmark
```

默认引擎在 `D:/Wanjie/tools/Godot/4.7.2/`。启动脚本拒绝非 4.7.2 Stable Standard。Lab 提供五动画选择、Play/Pause/Restart、0.5/1/2x、256/192/512px、骨骼/pivot/地线/socket 和 attack_hit counter。

`capture_native_animations.gd` 使用实际 GPU SubViewport，按原始角色高度 1435 源像素换算 256/192px，输出 PNG 帧序列；Python 只把这些真实帧排成 contact sheet/GIF，不合成替代骨骼运动。PNG 为规范证据，GIF 调色板只用于方便观看。

桌面压力测试：1920×1080，关闭 VSync，固定随机种子错开动画相位，每组合预热 1.5s、测量约 3s，记录真实绘制帧数/时间。death_once 的测量在倒地后进行，代表静止尸体，不代表活动倒地峰值。20/50 单位五种模式的原始数据见 `reports/native_rig_v2/stress_results.json`。

战斗验收只看真实 256/192px 下动作、连接、装备与滑步。五处已记录的 HIRES alpha 问题仍为 NON_BLOCKING_COMBAT_ARTIFACT，不因此重画素材。当前最终验收状态见 `reports/native_rig_v2/native_gate_v2.json`，不要用旧原型截图或历史失败报告代替当前结果。
