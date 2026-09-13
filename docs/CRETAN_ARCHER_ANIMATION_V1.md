# Cretan Archer 原生动画 V1

本单位使用 Godot 4.7.2 Stable Standard、GDScript、Skeleton2D、Bone2D、AnimationPlayer 和局部 Polygon2D 蒙皮。没有第三方骨骼插件。正式场景为 `scenes/units/odyssey/cretan_archer/cretan_archer_rig.tscn`，实验场景为 `scenes/tests/cretan_archer_rig_lab.tscn`。

## 骨架复用

从 `scenes/rigs/human_medium_rig_v1.tscn` 实例化原有 23 骨骼，适配副本的源坐标、rest、骨长与旋转方向。额外三个骨骼为 hand_far 下的 bow_socket、bow_socket 下的 arrow_socket，以及 torso 下的 quiver_socket，总计 26 骨骼。原 sword_socket/shield_socket 保留为空节点，不把弓挂到盾牌插槽。披肩使用现有 cape 分支。

共享场景与 Roman Guard 的艺术、动画、测试输出都不覆盖。单位数据位于 `resources/cretan_archer_rig_v1.json`；draw order 集中在同一文件。19 个 Sprite2D 负责纹理引用，其中八个由同纹理局部 Polygon2D 替代绘制，另有一个可控 Line2D 弓弦。正式资产仍为 20 个 PNG。

源画布是 1024×1536，地面原点 `(524,1460)`，战斗缩放采用可见身体高度 1340 源像素。PNG 保持全画布，Sprite 使用负源 pivot。单箭例外：它以纹理 nock `(282,725)` 对齐 arrow_socket；默认隐藏，不要求箭源画布和人物画布在 rest 中重叠。

## 连接区蒙皮

单纯转动硬切图片在大角度抬臂、弯膝时会暴露不连续。因此肩袖、护腕上缘、两侧护胫顶端和脚踝使用已有骨骼之间的连续权重，共八处。近侧上臂为 torso/upper/fore 三骨权重，其余七处为双骨。网格由源 Alpha 覆盖区生成，UV 与源坐标相同，不改部件 RGB、Alpha 或设计。连接区跟随近端骨骼，远端逐渐跟随活动骨骼。近上臂肩袖 y455–505 渐变到 upper，下缘 y575–650 逐渐转交 fore 控制，保证脸部高度拉弦时护腕与裸臂连续；没有增加覆盖漏洞的假图片。

Archer 副本的 near shoulder 控制点为 `(440,448)`，near elbow deformation control 为 `(382,600)`，wrist 为 `(388,789)`。其中 elbow 是经大角度拉弓校准的变形控制点，不能当作母图肘关节的医学定位。rest 的负 pivot 和 UV 保持原画零姿态位置；共享骨骼和正式源 pivot hints 不变。

生成器：`tools/build_cretan_archer_local_skinning.py`，数据：`resources/cretan_archer_local_skinning.json`。每个网格绑定纹理 SHA。重建时必须读取已批准正式部件，不能将过期候选无审查接入。

## 五个动画

| 动画 | 时长 | 行为 |
|---|---:|---|
| idle | 1.60s，循环 | 小幅呼吸，头部补偿，弓稳定，箭袋/披肩轻微滞后 |
| walk | 1.05s，循环 | 420 源像素/循环的前进位移，左右脚交替，支撑/摆动阶段与膝踝联动 |
| attack_01 | 1.20s | 取箭准备、前送、0.44s 搭箭、面部锚点拉弦瞄准、0.82s 唯一释放、收势回 idle |
| hit | 0.30s | 短促受击反馈，结束回 idle |
| death | 1.55s | 捂胸失衡、屈膝跪地、短暂停顿、前倾倒地与收势；弓由关键帧放落，无物理模拟 |

关键帧数据由 `tools/build_cretan_archer_native_data.py` 调用 Walk/Attack/Death V2 模块离线生成。新的三张 motion references 独立归档在 `art_source/odyssey/cretan_archer/motion_reference/`，只提供姿态阶段与节奏，不能作为正式纹理来源。Godot 播放 AnimationPlayer 轨道，不运行 IK 求解器。每段动画显式键控所有有关旋转、位置、弦控制点及箭可见性，以免切换时继承上个动作的残留状态。

## Walk 与参考

参考只决定 contact/down/passing/up 的阶段逻辑与轻装感，不复制参考图帧。离线使用每只真实鞋的下缘材料轮廓生成足底接触点，支撑段保持材料点世界位置稳定；足跟落地后转平，蹬地阶段逐渐提踵，摆动腿随后抬离地面。

根位移和腿部关键帧共同设计。运行时依据 AnimationPlayer 当前进度消费位移，正确处理循环和暂停；不能用额外整体移动遮盖不匹配的支撑脚。`resources/cretan_archer_walk_contacts.json` 保存源坐标目标、接触材料点、支撑段 ID、预期世界坐标及实际测试所需数据。

`scripts/tests/test_cretan_archer_rig.gd` 测量 Bone2D 实际 world position，既测键之间子采样，也测两轮真实 advance/root-motion 和暂停。接触点改变时分组，但同一材料点支撑段不能不断重置锚点以伪造零滑动。256/192px 指标与真实渲染共同验收。

## 弓箭与事件

弓在待机/行走/攻击时与手通过 bow_socket 固定；死亡后段才由明确的 bow_offset 轨道放落。Line2D 两端对应原弓弦附着点，中央 draw_point 随拉弦改变。arrow_socket 与 draw_point 同步，单箭仅在搭箭后至释放前显示，释放后隐藏。取箭阶段是拉弦手伸向箭袋的准备动作；本版不另做手持单箭搬运附着。Rig 不生成战斗投射物、不计算伤害。

attack_01 只有一个 AnimationPlayer method key，调用 `RigEventRelay._event_attack_release()`，由 relay 和单位发出 `attack_release`。没有 timer 猜测时间。Lab 显示每次播放计数；自动测试分别播放两次并确认每次恰好新增一次事件。

## 重建与验证

1. 验证 `tools/cretan_archer_parts_manifest.json` 为 PASS，正式部件 SHA 和源冻结一致。
2. 运行 `tools/build_cretan_archer_native_data.py`；它生成 Archer 数据，并从当前副本控制点重建八处局部蒙皮。不要运行 Roman 专用生成器。
3. Godot 4.7.2 headless editor import 后，运行 `scripts/build/build_cretan_archer_scenes.gd`。
4. 运行 Archer headless tests；随后使用真正渲染模式执行 `capture_cretan_archer_animations.gd` 和 `cretan_archer_smoke.gd`。
5. `tools/review_cretan_archer_animations.py` 将原生 GPU 帧制作成 GIF、战斗尺寸接触图、参考比较与脚底调试图。

Native 结果存于 `reports/cretan_archer/native/`。离线诊断图明确标记为 offline，不能代替 Godot GPU 捕获或性能数据。20 单位测试只代表当前桌面、当前渲染模式的基线，不代表手机性能。当前最终通过状态以 `reports/cretan_archer/pipeline_status.json` 及对应 SHA 绑定审查为准。

## 参考采用与边界

Walk 保留真正的双腿交替与世界支撑点锁定，步幅420源像素、1.05秒一圈，脚尖蹬地18°、摆动抬脚62源像素；头部补偿、持弓手稳定。参考中的相似侧身姿态不能代替完整循环，passing/opposite-support由骨骼逻辑补足。

Attack 的手指材料点与弦中点在搭箭/瞄准时吻合；取箭和回收是独立关键阶段，不能把不存在的飞行箭动画标记为已完成。弓弦使用8源像素运行线宽以避免256/192px下出现断续虚线，正式PNG不变。

Death 先明确跪地再前倒；最终地面高度依据真实透明纹理材料及同一三角形蒙皮求出，并以Godot实渲确认。弓放落为同一bow_socket的位置/旋转关键帧，无第三方插件、物理系统或战斗逻辑。

## 复用结论与成本

直接复用23骨的人型层级、原生Skeleton2D/Bone2D、事件中继模式、Lab和实渲/脚底测试方法。Archer新增3个弓箭插槽、弓弦控制、取箭拉弓动作和八处本兵种连接区权重；共享源、Roman角色以及20张Archer正式PNG不随这些动作试做而变化。

本次工作主要集中在遮挡资产补全和弓箭攻击姿态，Walk风格与箭袋/披肩为较小部分。没有可比较的受控工时记录，因此不声称成本已量化显著下降。后续单位可复用基础设施，但仍需本单位动作与连接区审查。
