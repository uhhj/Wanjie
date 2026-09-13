# Cretan Archer 输入身份冲突审查

基于本轮五张实际图片目视审查。冻结路径及哈希见 `art_source/odyssey/cretan_archer/source_manifest.json`；对照图见 `reports/cretan_archer/source_role_review.png`。

| 可见内容 | 观察 | 生产决定 |
|---|---|---|
| DESIGN / COMBAT_LOOK / RIG_MASTER 头部 | 棕色卷发、胡须、暗红头巾，未戴头盔 | 保持头巾轻装弓箭手身份 |
| 三张主要参考的服装 | 棕色皮甲、象牙白红边短袖/下摆、橄榄绿色披布、皮护腕与护胫 | 按 Rig Master 现有结构局部补全，不升级装甲 |
| CODEX 头部 | 可见头盔及冠饰，明显不同于前三图 | 仅收藏图，不进入 Rig 或人体补全 |
| CODEX 装备 | 更重的甲片外观、红色颈部布料及不同的护腿/肩部表现 | 保留冲突记录，不融合设计、不据此补颈甲 |
| 腰部短剑 | DESIGN/COMBAT_LOOK 有可见剑柄/鞘，Rig Master 当前腰侧没有同样可见的独立短剑 | 不从其他图增加短剑，不额外创建武器部件 |
| 姿态与视角 | DESIGN 多视图，COMBAT_LOOK 更展开，Rig Master 为较收拢的向右站姿 | 绑定坐标以 Rig Master 为准，不套用其他图比例 |
| WALK_REFERENCE | 展示落脚、后脚抬起等线索，多幅腿部前后关系相似 | 仅运动参考；不作为完整严格八相位证据，不提取正式像素 |

身份优先级：DESIGN > COMBAT_LOOK > RIG_MASTER >>> CODEX。生产几何优先级：RIG_MASTER > COMBAT_LOOK > DESIGN。两者并不授权把参考图的像素贴入角色。所有正式人物像素只来自 Rig Master 及其审查通过的局部补全链。

Rig Master 与 Combat Look 均有真实 Alpha，但最大值为 254，脚底可见投影。保留源图原样，后续派生 matte 单独处理透明度及背景投影。当前没有 Complete Body，不能给其结构或透明度盖 PASS。
