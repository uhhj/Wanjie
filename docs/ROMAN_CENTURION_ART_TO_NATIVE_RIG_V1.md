# 百夫长资产与原生动画流水线

单位 OD_UNIT_03_ROMAN_CENTURION。图1 DESIGN、图2 COMBAT_LOOK、图3 RIG_MASTER、图4 CODEX。图3是唯一正式像素来源；图4不决定隐藏人体。源图只读；透明图原件 alpha max=254，派生副本仅将254提升为255，RGB不变。

流程：局部剑/披风遮挡补全 → 真实RGBA与256/192px人体审查 → 可见像素优先拆件 → 重组与关节测试 → HUMAN_MEDIUM_RIG_V1 / Skeleton2D / Bone2D / AnimationPlayer → 六动画实际GPU审查。失败不得标记PASS或接入正式Rig。

## 技能 skill_command

举剑高呼：稳住前后站姿、胸口吸气抬起、剑臂从身侧向头顶上方举起，剑尖向上并略朝前，非持剑手向友军方向展开；头略抬、胸腹发力，号令保持后自然落手。预计1.4–1.8秒，non-loop。与攻击斩击区别：主要轮廓是竖直举剑和稳定号令，不向前劈落。

在号令保持段使用 AnimationPlayer method track 触发一次 command_release 信号。Rig只发事件；附近友军短时强化由未来战斗系统消费，半径、时长和数值未给定，不擅自实现。若需要张嘴高呼的脸部替换，单独制作表情候选，不修改冻结头部；没有合格表情时不得谎称已完成嘴型。

六动画 idle、walk、attack_01、hit、death、skill_command。Walk采用髋膝踝联动和真实前进位移，支撑脚世界坐标验证。Death采用失衡、屈膝、落地序列。所有动作均在256/192px审查，不以高倍边缘瑕疵为阻塞理由。

工程命令：tools/roman_centurion_pipeline.py verify；compose --raw work/roman_centurion/raw/001_complete_body.png；review。导入的AI结果必须同画布真RGBA，遮罩外逐像素保留。不得把生成式工具描述成原生支持精确mask；mask约束由确定性合成保证，遮罩内仍需视觉检查。

当前停止点：BLOCKED_COMPLETE_BODY_ART_GATE。失败证据见 reports/roman_centurion/complete_body_gate.json 与 complete_body_fix_targets.png。遮罩也有遗漏，不能把问题全部归因于模型。后续从原件与已有mask继续局部修复；不重启源图阶段，不把失败结果标正式。
