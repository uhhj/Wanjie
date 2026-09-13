# Roman Guard 原生动画 V1

动画源：`resources/roman_guard_animations_v1.json`。正式 AnimationLibrary：同目录 `.tres`，由 Godot builder 写入单位场景。所有动作明确 key 全部骨骼，防止切换后残留上一动作的角度。美术 PNG、Complete Body 和 near knee 权重保持冻结。

| 动画 | 长度 | 循环 | 行为 |
|---|---:|---|---|
| idle | 1.6s | 是 | 1.5 源像素呼吸、很小的盾剑/头盔/披风摆动 |
| walk | 1.0s | 是 | 真实向右前进，双腿相差半周期，持剑臂前后摆动，躯干轻微反向补偿，盾手稳定 |
| attack_01 | 0.8s | 否 | 先举盾，再抬高持剑手大幅前刺，恢复防御后回 idle |
| hit | 0.32s | 否 | 小幅后仰和盾牌震动，结束回 idle |
| death | 1.1s | 否 | 后仰、屈膝失衡、折倒、落地回弹、保持终姿；少量血滴 |

## Walk（用户批准：小腿与脚掌联动 V2）

用户确认：“确定为这版，将不合格的删除”。当前 Walk 正式冻结，旧候选和不合格预览已移除；完整批准哈希见 `reports/walk_chain_v2/approved_baseline.json`。

1秒循环、49个关键姿态，每周期真实向右前进387源像素。两腿错开半周期，近侧支撑[0,0.5)，远侧[0.5,1)。承重后段提前屈膝，随后抬跟、蹬地、收腿与前摆连续衔接。脚掌世界角范围约-12°至+18°，近侧蹬地时小腿后倾约12.6°，踝部局部角约18.1°。两鞋使用现有前向视图，其他动画保持各自原有鞋图。

骨盆上下0–7源像素、前后±1.5源像素；躯干轻微反向补偿，头部抵消85%的躯干运动。持剑上臂约±11.8°，盾臂仅有约0.3°惯性。Rig结构、膝甲pivot/蒙皮、正式部件和其余动画全部冻结。

AnimationPlayer 驱动现有关键帧，运行时按动画播放位置消费前进位移，不用timer猜步速。脚底检测分接触区间验证鞋底材料点世界坐标，支撑点最大漂移约0.038px（256px），约0.029px（192px）；暂停与循环位移验证通过。

[256px GIF](../reports/walk_chain_v2/walk_reference_follow_256.gif) / [192px GIF](../reports/walk_chain_v2/walk_reference_follow_192.gif)，均为16帧/1秒实际Godot GPU渲染。跟随视角由Camera2D跟进，地面刻度后移；角色真实前进位移保留。前进视角、逐帧审查和原生测试也在该目录。

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
