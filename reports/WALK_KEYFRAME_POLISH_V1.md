# Walk 关键帧微调 V1

PASS：只优化现有 Walk 关键值。其他四个动画数据完全相同；单位场景剔除 Walk subresource 后逐字节相同；67项冻结资源/文件哈希保持一致，包含原 Rig、全部部件和 near knee 数据。

| 调整 | 原版 → 本版 |
|---|---|
| 周期 / 关键姿态 | 1秒 / 49个，保持不变 |
| 骨盆上下范围 | 0–4 → 0–7 源像素，增加3源像素 |
| 骨盆前后重心 | 0 → ±1.5源像素 |
| 躯干与头 | 躯干轻微反向补偿，头部抵消85%躯干角度 |
| 周期前进距离 | 360 → 387 源像素，增加7.5% |
| passing抬脚 | 30 → 34源像素 |
| 持剑上臂摆幅 | ±11° → ±11.8° |
| 盾牌 | 保持防御方向，盾臂仅增加±0.3°惯性 |

保留原支撑阶段、步态解法、鞋朝向变体、全部权重与骨骼结构。near_knee 独立控制键未变化，没有调整pivot或扩大overlap。没有把动作改成跑步，没有修改其他动画。

## 输出

- [256px GIF](walk_polish_v1/walk_polish_256.gif) / [256px 全16帧审查](walk_polish_v1/walk_polish_256_review.png)
- [192px GIF](walk_polish_v1/walk_polish_192.gif) / [192px 全16帧审查](walk_polish_v1/walk_polish_192_review.png)

两份GIF均为16帧、正好1000ms。取样时刻为0至0.9375秒，不重复周期端点；PNG均为实际Godot 4.7.2 GPU画面，角色维持256/192px真实显示尺寸。GIF循环时展示单位回到屏幕起点；Rig Lab仍连续向前移动。

## 验证

原生解析、轨道路径、攻击事件恰好一次和支撑脚锁定测试通过。实际runtime连续两周期测试，支撑脚最大漂移约0.0037px（256px），约0.0028px（192px）。两种尺寸审查未发现新增关节断裂或夸张头盾运动。

[精确指标与SHA](walk_polish_v1/walk_polish_metrics.json) / [Godot测试](walk_polish_v1/headless_tests.json) / [冻结文件基线](walk_polish_v1/before_hashes.json)。

本轮仅验证关键帧微调；保留此前“可用原型、尚非精修成品”的整体质量说明。此前20/50单位FPS是原版桌面基线，本轮未重测，不把旧数值说成新关键帧的实测。
