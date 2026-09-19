# 牛头破阵者 V1 交付

> 普攻当前版本为 [ATTACK_V4](MINOTAUR_BREAKER_ATTACK_V4.md)：更高蓄力、斧刃触地重劈与程序化冲击特效，2.3 秒；技能当前版本为 [CHARGE_V3](MINOTAUR_BREAKER_CHARGE_V3.md)：柄尾拖斧与 56 度深俯身牛角冲锋，4.2 秒。新预览在 `reports/minotaur_breaker/actions_v4/`；本文件中的V1帧图和压力数据作为历史记录保留。

角色单体资产、六动画和原生Rig已完成；高密度桌面性能与阵列遮挡保留限制，不能把50单位测试完成解释为50单位流畅运行。

## 打开

在本仓库执行 `powershell -File tools/run_minotaur_lab.ps1` 打开Rig Lab，加 `-Stress` 打开压力场景。使用已验证的Godot 4.7.2 Stable Standard。正式单位场景：`scenes/units/odyssey/minotaur_breaker/minotaur_breaker_rig.tscn`。

Lab支持六动画、暂停/重播、播放倍率、360/288显示尺寸、骨骼/关节/挂点显示和事件计数。独立蓝条示范采用“4次普通攻击触发一次技能”的实验值，仅存在Lab，不是兵种平衡数值。正式Rig只发attack_hit和skill_hit，不实现伤害、蓝条或敌方击退系统。

## 资产与动画

四份参考原件SHA未变。19核心部件加2隐藏膝后支撑层均为1024×1536 RGBA；25根Bone2D，13个原生Polygon2D蒙皮，其余使用Sprite2D。模型输出仅用于局部遮挡补全，万界录原画未用作战斗纹理。

六动画：idle、walk、attack_01、skill_01、hit、death。`reports/minotaur_breaker/animations`提供360/288两种尺寸的16帧GIF及原生GPU PNG。正式与候选场景的动作和纹理等价关系由formal_scene_parity.json验证。GIF标题保留CANDIDATE以对应采集时的场景名称，当前通过版本由approved_candidate_capture.json的SHA明确锁定。

普通攻击为双手短促举斧挥压；技能包含换步向前破阵及重击，位移与普通攻击不同。死亡保留握斧并以屈膝失衡后倒地，没有装备物理掉落。

## 验证与限制

- 冻结源、RGBA、局部编辑范围、网格UV/权重：PASS。
- 360/288实机逐帧审查及重组：PASS，审查为Codex技术/视觉检查，不冒称用户签字。
- 原生支撑脚漂移：近侧约0.0013px、远侧约0.0041px（360px尺寸）。
- attack_hit、skill_hit每次对应动画各发一次，互不串发；Lab蓝条演示及死亡保持通过。
- 1920×1080、GTX1650当前桌面：20单位walk约31.57 FPS；50单位walk约12.49 FPS；20单位skill_loop约24.36 FPS。8秒测量、2秒预热，无手机性能结论。
- 20单位阵列仍有纵向头角/脚部重叠；50单位紧密阵列有明显披风、角、战斧和邻单位遮挡，密度可读性不通过。单体Rig可用，不应直接照搬压力场景的阵列间距用于正式战斗。
- 保留源图非阻塞高分辨率边缘瑕疵。隐藏膝部皮毛共用一份局部补全并分别配准；仅验证当前侧向六动画，不保证任意新极限姿态。

失败迭代和诊断图保留在work/reports，用于溯源。当前有效结论看delivery_report.json、production_art_review.json、formal_motion_contract_test.json和formal_scene_parity.json；不要把旧diagnostic截图当成当前动画。

## 复现门禁

构建候选 → 格式/结构/运动测试 → 实际GPU采集两种尺寸 → 逐帧美术审查 → promote_minotaur_assets.py → formal_scene_parity与正式运动测试 → Lab及真实桌面压力测试。修改动画或纹理后，旧SHA审查失效，不能直接复用PASS。

本角色在独立工作树Wanjie-minotaur-breaker及feature/minotaur-breaker-native-rig-v1分支开发，原工作树里其他角色的未提交修改未被动过。
