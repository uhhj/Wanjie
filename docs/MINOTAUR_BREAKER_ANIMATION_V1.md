# 牛头破阵者原生动画 V1

> 当前普攻和技能已更新为 V2：详见 [MINOTAUR_BREAKER_HEAVY_ACTIONS_V2.md](MINOTAUR_BREAKER_HEAVY_ACTIONS_V2.md)。以下1.35秒攻击和1.8秒技能描述为历史V1；当前正式值为1.8秒过顶劈砍、4.2秒牛角冲锋。其他四动画不变。

六动画：idle 2秒循环；walk 1.4秒循环；attack_01 1.35秒；skill_01 1.8秒；hit 0.4秒；death 1.7秒。数据在 `resources/minotaur_breaker_animation_candidates.json`，原生AnimationPlayer由构建脚本生成。

Walk每周期前进180源像素。双腿相差半周期，支撑相62%、摆动相38%，支撑期间踝点相对身体向后移动，与根位移抵消。行走落脚点收拢到身体下方，避免沿母图宽站姿原地挪步。大腿、小腿通过固定骨长IK联动。头部保持稳定，空手与披风仅小幅滞后。测试记录源像素和两种战斗尺寸的世界脚底漂移。

Attack先接第二握点、蓄力举斧再下压挥击，结束回idle。Skill先降低重心，随后向前推进220源像素并换步，最后重击；它是移动破阵动作，不只是普通攻击加大伤害。两者分别在AnimationPlayer方法轨道发独立事件。Rig不包含任何伤害常量、蓝条容量或击退计算。

Death先失衡下沉、屈膝，再侧前倒下；末段校准头角、斧刃与地面的相对位置，不循环、不自动恢复。六动画均已检查360/288尺寸的16帧实机序列；`production_art_review.json`绑定被审查构建的SHA。早期穿地或关节断口诊断图仅保留问题溯源，不是当前正式效果。

正式动画数据为 `resources/minotaur_breaker_animations_v1.json`，正式场景内嵌AnimationPlayer动画库。提升脚本只改资源路径、场景名称和默认自动播放，`formal_scene_parity.json`验证动作/纹理未改变；`formal_motion_contract_test.json`在正式场景重测脚底轨迹及两种命中事件。

Lab提供六动画选择、Play/Pause/Restart、0.5/1/2倍速、360/288尺寸、骨骼/关节/挂点显示、攻击和技能计数。压力场景提供1/10/20/30/50单位及idle/walk/attack_loop/skill_loop/hit_loop/death_once。压力FPS是当前桌面环境基线，不推断手机表现；拥挤场景需要独立检查斧、角和披风遮挡。

`reports/minotaur_breaker/animations`中的PNG来自实际Godot GPU SubViewport。GIF和contact sheet仅组装这些帧，不把AI动作图或Python变换图冒充原生渲染。
