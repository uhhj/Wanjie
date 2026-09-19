# 高斯步枪兵生产计划 V1

目标：中型远程步兵"高斯步枪兵"（OD_UNIT_05_GAUSS_RIFLEMAN）的完整单体资产与六个原生动画，不扩展其他系统。冻结来源依次为设计三视图、战斗外观、Rig 母图、收藏原画；收藏原画禁止提取战斗像素。

## 冻结源与角色

| 角色 | 文件 | 用途 |
|---|---|---|
| DESIGN_V1 | OD_UNIT_05_GAUSS_RIFLEMAN_DESIGN_V1.png (1448×1086 RGB) | 设计基准：三视图、头盔细节、武器细节、姿态参考 |
| COMBAT_LOOK_V1 | OD_UNIT_05_GAUSS_RIFLEMAN_COMBAT_LOOK_V1.png (1024×1536 RGBA) | 战斗外观参考 |
| RIG_MASTER_V1 | OD_UNIT_05_GAUSS_RIFLEMAN_RIG_MASTER_V1.png (1024×1536 RGBA) | Rig 母图：侧视、朝右、持枪站姿 |
| CODEX_V1 | OD_UNIT_05_GAUSS_RIFLEMAN_CODEX_V1.png (1122×1402 RGB) | 收藏原画（禁止用于战斗纹理） |

两张 1024×1536 母图 alpha 上限 254（非 255），为源图自身状态，如实记录；alpha 门禁在拆件阶段处理。源图只读，禁止修改。

## Rig 家族与部件

采用 HUMAN_MEDIUM_RIG_V1（与罗马盾兵同族中型人体），按本角色实际比例定长，不套用他人数值。画布 1024×1536，全部正式部件同画布 RGBA。核心部件清单（16 件）：helmet、head、torso、pelvis、arm_near_upper/fore、hand_near、arm_far_upper/fore、hand_far、leg_near_thigh/shin、foot_near、leg_far_thigh/shin、foot_far、rifle。与盾兵的差异：无盾牌/披风，新增 rifle（双手握持：主握把+前握把，攻击时换第二握点需检查可达性，参见牛头破阵者双手斧经验）。

腰袋/挂具/膝甲归入所属部件美术，不单独拆件。

## 动画与事件

六动画：idle 2 秒循环、walk 1.4 秒循环、attack_01（步枪射击，含后坐与收枪回位）、skill_01（穿甲射击类技能，具体设计待定）、hit 0.4 秒、death 1.7 秒。attack_hit 与 skill_hit 由 AnimationPlayer 方法轨道各发一次；伤害/弹药/蓝条归外部战斗层，骨架只提供时机。

## 流程与门禁

源图 SHA 冻结 → 遮挡补全候选（AI 或人工 Image 2.5，未编辑像素保护）→ RGBA/战斗尺寸门禁 → 像素优先拆件与关节重叠 → 原生装配（HUMAN_MEDIUM_RIG_V1 + 步枪双手约束）→ 六动画 → Rig Lab → 桌面压力审查。正式部件未通过前不得把候选报告写成 PASS。

## 当前状态与停止规则

本环境未验证到可用的图像生成/修补接口，按停止规则输出 PASS_WITH_IMAGE_EDIT_MANUAL_STEP_REQUIRED：遮挡补全的 mask 草案、提示词、job 记录与导入工具已就绪（见 GAUSS_RIFLEMAN_IMAGE_EDIT_HANDOFF_V1.md），补全结果返回后流水线从同一位置继续，不重启。
