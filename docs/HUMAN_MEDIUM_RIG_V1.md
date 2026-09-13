# HUMAN_MEDIUM_RIG_V1

Godot 4.7.2 Stable Standard，原生 Skeleton2D、23 个 Bone2D、AnimationPlayer，GDScript，无第三方骨骼插件。通用骨骼场景为 `scenes/rigs/human_medium_rig_v1.tscn`，Roman Guard 实例为 `scenes/units/odyssey/roman_guard/roman_guard_rig.tscn`。

## 骨骼与坐标

```text
Skeleton2D
└─ pelvis
   ├─ torso
   │  ├─ neck ─ head
   │  ├─ arm_near_upper ─ arm_near_fore ─ hand_near ─ sword_socket
   │  ├─ arm_far_upper ─ arm_far_fore ─ hand_far ─ shield_socket
   │  └─ cape_root ─ cape_mid ─ cape_tip
   ├─ leg_near_thigh ─ knee_near ─ leg_near_shin ─ foot_near
   └─ leg_far_thigh ─ knee_far ─ leg_far_shin ─ foot_far
```

所有 pivot 坐标以 1024×1536 源画布左上角为原点，x 向右、y 向下。`resources/human_medium_rig_v1.json` 保存每根骨骼的父节点、NodePath、局部位置、长度和显示方向；长度取首个非重合子关节距离，末端/同点控制骨使用 25px 显示长度，不拉伸纹理。Skeleton 在角色原点的偏移为 (-530,-1460)。

| 关节 | 源画布坐标 |
|---|---|
| pelvis / torso | (530,701) / (533,695) |
| neck / head | (526,395) / (537,290) |
| near shoulder / elbow / wrist | (375,555) / (332,671) / (329,835) |
| far shoulder / elbow / wrist | (641,601) / (680,695) / (740,782) |
| near hip / knee / ankle | (430,900) / **(388,1083)** / (332,1331) |
| far hip / knee / ankle | (592,910) / (640,1083) / (658,1334) |
| sword / shield grip | (328,867) / (744,821) |
| cape root / mid / tip | (508,415) / (250,760) / (150,1040) |

原拆片建议的 near hip=(421,995)、far hip=(619,1003) 接近可见大腿切片上缘。实际行走暴露出旋转轴过低，因此动画 Rig 将髋轴移入裙甲遮挡下的髋部。此修改只调整骨骼与反向 Sprite 偏移，0°重组、纹理和膝甲中心保持不变。Walk 采用双膝朝前屈的解，不能再沿用旧近腿反向弯曲。Death 用等效变换补偿保留用户认可的姿态。

## Rest 与正式像素

19 个核心件加独立 `knee_near`，共 20 张正式纹理，全部同画布 RGBA。每个 Sprite2D `centered=false`，局部位置为负 attachment pivot，使 0°时同源像素回到相同画布位置。Rest 是 `rest_pose()`，不是第六个动画；AnimationPlayer 只有用户指定的五个动画。

场景有 20 个 Sprite2D 节点和 4 个 Polygon2D，按动作切换后始终为 21 次正式美术绘制：cape PNG 以原有互斥 masks 分成前领/后摆两次绘制；近胫始终使用 Polygon2D。两个肩部在 Walk/Attack 使用局部蒙皮，远脚在 Walk 使用局部蒙皮，对应原 Sprite 同时隐藏；其他动作沿用原 Sprite，不能重复叠画。

大幅举盾/刺击暴露了原肩部刚性绑定的真实空洞。`resources/arm_near_upper_local_skinning.json` 和 `arm_far_upper_local_skinning.json` 让肩甲/胸甲上缘跟随 torso，下方大臂逐渐转为 upper-arm 权重，使用原 PNG 的真实像素。近肩轴从切片提示 (457,510) 调整为肌肉关节位置 (375,555)。此处是经实际动作证明的局部结构修复，没有新增甲胄或重画人物。远脚的 `foot_far_local_skinning.json` 让鞋筒上端跟随 shin，鞋底跟随 foot，消除独立平脚旋转造成的踝部折断感。原 PNG 和已批准 near knee 权重均未覆盖。

近侧膝甲绑定 `knee_near`；近胫采用冻结的 `near_knee_skinning_v1.json`，分别绑定 `knee_near` 和 `leg_near_shin`。膝甲边缘使用 stationary socket 权重，离开膝甲后平滑过渡至 shin 权重。膝甲不随 shin 大幅旋转。本轮没有扩大约 32.9% 的 thigh/shin overlap。

Walk 的右鞋需要朝前的视图，原 far shoe 站姿纹理朝外，不能靠一个平面旋转修成另一个视角。因此仅在 Walk 中复用已批准的 `foot_near.png` 像素作为 far shoe 的朝前变体，UV 保持原像素，几何平移到 far ankle 后绑定 shin/foot。两脚保持同一朝向；Rest、Idle、Hit、Attack、Death 仍使用原 far shoe。没有重画鞋子、镜像纹理或修改冻结 `foot_far.png`。运行时存在姿态变体，不能把动画中的 far shoe 审查误写成原 far PNG 已改动。

`knee_far` 是关节控制骨，当前 far knee 没有独立 PNG，不为结构对称重新拆件。cape_mid、cape_tip 为复用预留控制骨；当前冻结披风以 cape_root 刚性运动，未虚构多段布料蒙皮。冠饰没有独立 PNG，Idle 只有极小 helmet 整体转动。

## 绘制顺序与 sockets

唯一 z 顺序入口：`scripts/rig/roman_guard_draw_order.gd`。后披风和远肢在后；躯干中层；近膝甲盖在近胫上；helmet 盖 head；剑和近手置于盾牌前，以保证刺击可读，0°不改变已批准重组。DeathBlood 为独立效果层。

Sword Sprite 是 sword_socket 子节点，socket 位于 hand_near 下；Shield 对应 hand_far/shield_socket。武器运动来自骨骼链，禁止每帧独立猜测武器位置。自动测试直接测量剑柄与握持点的全程距离。

## 生成和复用

`tools/build_native_rig_data.py` 生成通用骨骼和五动画源数据；`scripts/build/build_native_scenes.gd` 用 Godot 将通用骨骼的一份 owned copy 烘焙进正式单位场景，再绑定纹理和 AnimationLibrary。单位场景不是实时继承链接：修改通用骨骼后必须重新 Build，并重新验证。

复用时保留通用骨名、事件协议和 socket 语义，按新单位的批准素材提供 pivot/attachment/绘制顺序；不保证不同体型无需重新校准。本轮没有创建第二兵种。
