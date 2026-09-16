# 百夫长原生 Rig 与六动作候选

百夫长使用已批准 Complete Body V2 和21件同画布 RGBA 部件。原盾兵、弓箭手和共享 HUMAN_MEDIUM_RIG_V1 文件不变。Godot 为4.7.2 Stable Standard，原生 Skeleton2D / Bone2D / AnimationPlayer；10处 Polygon2D 局部权重用于肩、肘、腿根、膝和踝，没有第三方插件。

## 素材与骨架

正式像素目录为 `assets/units/odyssey/roman_centurion/parts/`。16个人体基础部件、2个独立狮面膝甲、完整剑、披风后摆、胸前搭片，共21件。后摆在人体后方，搭片在胸甲/肩甲上方。draw order只定义在 `resources/roman_centurion_rig_v1.json`。

共享23骨结构不变，百夫长场景持有独立重定向副本。所有人体骨名仍使用 pelvis、torso、arm_near_upper 等通用名。近膝(489,1109)、远膝(728,1112)为源画布坐标；膝甲随膝中心和大腿，独立小腿旋转不带动整块膝甲。全部 pivot、骨长、父子路径记录在 Rig JSON。

局部 AI 只用于被遮挡的剑柄、上段大腿、膝甲下方底层、近肩胸甲和披风隐藏部分。原剑刃与其他可见源像素由遮罩恢复。005/006/008为内置 image_gen 原始结果；007保留了错误剑首，整图被拒绝。全部 prompt、输入/输出 SHA 和局部合成配方在 reports/roman_centurion/ai_jobs 与 parts_v1/hidden_completion_recipes.json。原始模型输出不能直接作为正式 PNG。

## 动作

| 动作 | 时长 | 循环 | 内容 |
|---|---:|---|---|
| idle | 1.6s | 是 | 轻微呼吸、稳站 |
| walk | 1.05s | 是 | 左右腿交替，源空间每周期前进280px，剑手轻摆 |
| attack_01 | 1.05s | 否 | 蓄势举剑、全身配合下劈、回收 |
| hit | 0.32s | 否 | 短促受击反馈 |
| death | 1.3s | 否 | 失衡、屈腿、侧向倒下和停留 |
| skill_command | 1.7s | 否 | 举剑向上、空手示意、号令保持和回收 |

attack_01、hit、skill_command结束自动回idle，death不自动恢复。Rig Lab允许六动作切换、Play/Pause/Restart、0.5x/1x/2x、256/192px、骨骼/轴心/socket/地线显示。

`attack_hit`在攻击method track中发出一次；`command_release`在号令保持段发出一次。没有Timer猜时。Rig不计算范围增益，附近友军强化的半径、时长与数值由未来Combat System消费事件。技能目前使用冻结头像，没有新增张嘴表情或配音，不能宣称口型已完成。

## 验证与使用

在项目根运行 `tools/run_centurion_native.ps1 -Action Lab` 可打开实验场。其他Action：Build、Validate、Capture、Stress、Benchmark。

构建顺序：`build_centurion_native_data.py` → `build_centurion_skinning.py` → `settle_centurion_death.py` → Godot `build_centurion_scenes.gd`。骨架场景文件为 `scenes/units/odyssey/roman_centurion/roman_centurion_rig.tscn`。这些脚本仅更新百夫长资源。

Capture使用真实GPU SubViewport，Python只组装GIF和审查图，不能合成替代Godot运动。每个动作各16帧，256px与192px独立渲染。Walk包含真实根位移及固定地面刻度；257个插值时刻检查支撑脚上的固定材质点世界坐标，不能用每帧重新选锚点隐藏滑步。

20/50单位压力测试在1920×1080桌面环境、192px角色尺寸、随机动画相位进行，记录idle/walk/attack/skill四模式。FPS是当前桌面基线，不是手机性能，也不是60FPS保证。

Complete Body与静态部件门禁已通过。六动作是第一版可审查候选；技术测试通过不等于用户已接受动作观感。动画的最终视觉状态、非阻塞项与尚需调整项以 `reports/roman_centurion/native/animation_visual_gate.json` 为准。

## 动作反馈修订 V2

按用户反馈保留死亡动作。Walk改为固定髋部轨迹下的双骨求解，左右脚保留透视间距，缩短跨步以减少交叉，摆动期提高离地高度；步幅与真实根位移同步调整为每周期280源像素。攻击扩大蓄势、躯干跟进与伸臂下劈。号令采用持剑手从画面左侧外展抬剑的独立路径，肘部保持同一弯曲分支，抬起与回收均不做角度取模跳转。冻结部件与其他兵种保持不变；三项修订等待用户观感验收。
