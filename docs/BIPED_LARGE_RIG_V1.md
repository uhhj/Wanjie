# BIPED_LARGE_RIG_V1

牛头破阵者使用 Godot 4.7.2 Stable Standard、Skeleton2D、Bone2D、AnimationPlayer 和原生 Polygon2D 骨骼权重。没有第三方骨骼运行时。正式场景为 `scenes/units/odyssey/minotaur_breaker/minotaur_breaker_rig.tscn`；候选及原始失败证据保留在work/reports，不用于正式引用。

## 比例与坐标

原画布1024×1536；原点(486,1485)；初始战斗显示高度360/288px。25个骨骼的源坐标、父节点、长度和静止Transform由 `resources/minotaur_breaker_rig_v1.json` 记录。牛头和双角由同一head部件保持刚性，不独立摇角。

髋关节藏在裙甲下：近侧(367,870)、远侧(566,875)。不能把首次可见大腿像素的y963当作髋中心。膝分别(375,1085)、(618,1103)，踝分别(296,1360)、(614,1365)。大型宽躯干和蹄足以本角色为准，不把中型人体统一放大。

## 层级

pelvis控制torso及双腿；torso连接neck/head、双侧shoulder、upper/fore/hand和cape_root/mid/tip。每腿为thigh/knee/shin/foot。far hand下的axe_socket为主握柄，near hand下的axe_support_socket为辅助握柄。骨骼名不绑定兵种名称。

主握柄源点(821,862)，辅助握柄源点(803,1012)。静止姿势沿母图单手持斧；重击和技能中近手移向辅助握柄。动画预计算两段骨骼IK并烘焙为角度关键帧，禁止伸缩骨长解决超伸。`candidate_ik_reach.json`记录不可达帧；其PASS不替代可视审查。

## 绘制与局部蒙皮

绘制顺序只由rig JSON的draw_order管理。背后披风/远侧肢体先画，躯干与裙甲居中，近侧臂与肩甲在前，斧与远侧握手保持源图遮挡。PNG全部保留完整源画布；运行时Sprite2D.region只减少透明区域绘制，不改变源PNG画布。

19个核心部件加2个隐藏膝后皮毛支撑层，合计21张同画布RGBA。13个原生Polygon2D部件处理肩、肘、膝、踝与披风连续性，其余部件使用Sprite2D。24源像素网格在360px尺寸约6显示像素，UV保持源坐标；PNG本身不变。相邻部件的重叠区域使用一致关节权重，避免两份膝甲在转动时分开。不可用蒙皮掩盖缺失设计；远侧上臂、披风、斧柄及膝后补全分别有AI记录。两个膝后支撑层来自同一局部皮毛补全，分别配准，位于原有甲片和披风后方。

## 复现

先运行Python资产候选构建和补全导入，再运行动画候选/蒙皮生成，最后以Godot执行 `scripts/build/build_minotaur_candidate_scene.gd`。候选场景位于work目录，压缩纹理资源可重建。不要直接把候选状态改为PASS。

验证包括冻结源SHA、同画布RGBA、原位重组、原生支撑蹄轨迹、独立事件、360/288实帧以及桌面压力。方法轨道为attack_hit和skill_hit各一次；外部战斗系统负责蓝条积累、技能请求、伤害和击退，骨架只提供时机。
