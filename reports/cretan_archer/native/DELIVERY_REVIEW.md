# Cretan Archer 原生骨骼交付审查

Verdict: **CRETAN_ARCHER_NATIVE_RIG_REUSE_SUPPORTED**

正式美术20/20已通过。此次动作调整没有改变Complete Body或任何正式PNG。最新三张参考图单独冻结，仅用于动作阶段与节奏，不提取人物帧或纹理。

| 验收 | 结果 |
|---|---|
| Godot | 4.7.2 Stable Standard / GDScript |
| 人型Rig复用 | 原有23 Bone2D + 3弓箭插槽 = 26 |
| 正式纹理 | 20张；19 Sprite2D引用、8处原生Polygon2D蒙皮替代绘制、1条动态Line2D弓弦 |
| Idle / Walk / Attack / Hit / Death | 256px与192px均PASS |
| attack_release | 每次播放恰好1次，两次独立播放合计2次 |
| Walk支撑漂移（256px） | near 0.00229px / far 0.00292px |
| 两轮Walk世界位移 | 840源像素，暂停保持 |
| Headless语法/资源/轨道 | PASS |
| 20单位桌面smoke | 1920×1080，角色192px，20.006秒，平均80.53FPS |
| GPU | GeForce GTX1650；Windows实际渲染，非headless性能数据 |

Walk：轻装交替步态，膝、踝、脚掌联动；取参考的阶段规律，重新确定整圈关键帧。Attack：取箭准备、搭箭、举弓、脸部锚点瞄准、释放与回收。Death：一腿先失衡、另一脚继续支撑，屈膝跪地后前倒，头/前臂落地，停止保持。

保留的非阻塞限制：近肩在搭箭/捂胸阶段仍有紧凑的圆弧纹理折叠，256/192px下无透明缺口或断臂；最终倒姿比参考略伸展；原有高分辨率边缘瑕疵保持。取箭目前是手部准备动作，不另实现手持单箭转移；飞行箭由未来Combat System处理，本轮没有实现战斗系统。

## 查看与复现

- `scenes/tests/cretan_archer_rig_lab.tscn`：五动画、播放/暂停/重启、速度、256/192px、骨骼/插槽/地面调试。
- `reports/cretan_archer/animations/`：五动画各16帧原生GIF与256/192审查图。
- `reports/cretan_archer_walk_reference_comparison.png`：Walk阶段对照。
- `reports/cretan_archer/native/attack_reference_comparison.png`、`death_reference_comparison.png`：攻击/死亡阶段对照。
- `reports/cretan_archer/native/delivery_gate.json`、`headless_tests.json`、`capture_manifest.json`、`smoke_20_walk.json`：按当前SHA绑定的验收证据。
- `docs/CRETAN_ARCHER_ANIMATION_V1.md`：骨骼、变形控制点、事件、重建与测试方式。

实际帧和脚底接触测试决定通过，不使用参考像素相似度。此前失败/旧参考批次保留在native下的baseline/attempt目录，不能当作最终证据。

复用成立：共享骨架、原生动画/事件模式与验证设施沿用；新增集中在弓弦、拉弓、连接区权重和遮挡资产。没有可比较的受控工时数据，因此不声称量化生产成本下降。建议后续继续复用基础设施，并保留每个单位的动作验收。本轮到此为止，不进入第三兵种。
