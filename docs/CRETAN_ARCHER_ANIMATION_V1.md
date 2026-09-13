# Cretan Archer 原生动画 V1 制作计划

状态：PLANNED_NOT_RUN。当前没有本单位 Godot 场景或动画，本文记录用户要求及复用设计，不是验收报告。Godot 已核对为 4.7.2.stable.official.ed1daf0bf；实际路径 `D:/Wanjie/tools/Godot/4.7.2/Godot_v4.7.2-stable_win64_console.exe`。当前未对不存在的弓箭手场景运行解析或 smoke 测试。

复用 Skeleton2D / Bone2D / AnimationPlayer 的 HUMAN_MEDIUM_RIG_V1 拓扑。仅做 idle、walk、attack_01、hit、death，不引入第三方插件或战斗系统。

## Walk：动作参考的边界

WALK_REFERENCE 只决定“怎样走”，不决定脸、服装、弓或箭袋，不提取任何正式角色像素，也不把八幅人物作为 Sprite 动画。`reports/cretan_archer/walk_reference_pose_review.png` 是带上下文的参考裁片；画面相邻人物可能重叠，不能拿裁片当独立精确运动数据。

参考可见脚跟接触、后脚抬起等线索，但不清楚覆盖完整的 passing 及另一腿支撑循环。下表是需要在真实 Rig 中制作的完整循环，时间和阶段是基于步行动作逻辑的初始设计，不声称从参考图逐帧测得：

| 姿态 | 周期位置 | 目标 |
|---|---:|---|
| contact_near | 0.00 | 近脚接地，远脚前掌结束支撑 |
| down_near | 0.10 | 近腿承重，骨盆轻降 |
| passing_near | 0.27 | 近腿支撑，远腿离地经过 |
| up_near | 0.40 | 近脚跟抬起，远腿准备落脚 |
| contact_far | 0.50 | 远脚接地，进入反相半周期 |
| down_far | 0.60 | 远腿承重 |
| passing_far | 0.77 | 远腿支撑，近腿离地经过 |
| up_far | 0.90 | 远脚跟抬起，衔接近脚接地 |

初始周期约 1 秒，步幅约角色高度 0.30，比已批准 Roman Guard 的 0.2697 略大；骨盆起伏约高度 0.0065，比其 0.00488 稍明显。这些是调动画的起点，不是已通过数值。始终保持交替支撑和双支撑过渡，不出现跑步腾空。

必须联动 thigh、shin、foot，不能只转脚掌而小腿不跟随。真实前进位移与腿部关键帧一起设计，在支撑段记录脚跟/前掌等实际接触材料点的 world position。脚掌滚动阶段不能用踝节点不动伪装脚底锁定；要记录接触点切换。256/192px 无肉眼滑步优先于参考姿态近似。

torso 轻微反向补偿，head 稳定，bow hand 受控，空手仅小幅摆动，quiver/cloak 很轻滞后。不要复制盾兵重装碎步感。

## Attack 与其他动画

attack_01 计划约 0.9 秒：0.10 抬弓，0.22 准备搭箭，0.35 拉弓，0.48 满弓，约 0.52 释放，0.56 弦恢复，0.70 收势，结束回 ready。实际 AnimationPlayer method track 恰好发出一次 attack_release；禁止 timer。bow_socket 位于持弓手，arrow_socket 位于拉弦手，释放前箭可见、之后隐藏。不能套用近战刺击。

idle 稳定轻微呼吸；hit 短促小后仰；death 失衡倒地、不循环、不做 ragdoll。持弓与披布不得明显穿插。

## 待生成的实际证据

- 本单位 Rig 与 Lab 场景，资源路径检查及 headless parse。
- 五动画 256px/192px 原生渲染与独立审查，存于 `reports/cretan_archer/animations/`，保留 Roman Guard 现有报告。
- `reports/cretan_archer_walk_reference_comparison.png`：左参考姿态线索，右 Godot 实际对应姿态；对推导阶段明确注明，无像素相似度门禁。
- 支撑脚 world position 轨迹、接触阶段、战斗尺寸滑步审查。
- attack_release 一次播放计数恰好 1，弓/弦/箭连接正确。
- 20 单位实际 smoke，记录桌面引擎结果，不虚报手机性能。

上述全部当前 NOT_RUN。只有实际证据通过，才报告 HUMAN_MEDIUM_RIG_V1_REUSE_SUPPORTED；目前复用计划不是复用验证。
