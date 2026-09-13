# Cretan Archer 资产流水线 V1

当前已完成 20 个正式部件，RGBA 同画布、重组及局部关节战斗尺寸审查通过。完整人体仍是用户说“接受”的外部候选 003；本次没有重新生成或修改这张 Body。原生动画、事件、脚底接触和性能有独立门禁，见 reports/cretan_archer/native/，不得用资产 PASS 代替动画 PASS。

## 冻结与身份

art_source/odyssey/cretan_archer/source_manifest.json 保存五张参考的 SHA 和职责。DESIGN/COMBAT_LOOK/RIG_MASTER 定义轻装头巾弓箭手。CODEX 的头盔重甲冲突保留在审查文档，不参与正式像素生产。WALK_REFERENCE 只提供运动阶段、腿脚联动及节奏；未提取其人物作为动画 Sprite。

批准 Body：work/cretan_archer/04_complete_body_rgba.png，SHA256 f8451c19b04a8d754fb2ebfeb4441324990a5b5d9de6dcc6ccec518550536bc8。原外部候选 RGB 全部保留，仅对 Alpha 254→255 做已记录的规范化。此替代来源有独立批准记录，没有伪造 001–003 成功记录。

运行 tools/cretan_archer_pipeline.py verify-frozen 会核对五张源图和 49 项 Roman Guard 冻结文件。共享 HUMAN_MEDIUM_RIG_V1 原件保持不变，Archer 只适配实例副本。

## 本次实际修复

内置 image_gen.imagegen 实际完成八次独立部件编辑：裙装缺口、近侧隐藏大腿、远侧隐藏大腿、隐藏躯干、弓握柄、完整单箭、箭袋和披肩。没有把整个人物作为编辑目标。工具未暴露原生 mask 参数及具体模型版本，原始输出带 RGB 棋盘底；这些事实在 job 中如实保存。

生成结果仅提供缺失材料。确定性合成在明确区域加入补片，锁定全部已归属的原可见 RGBA 像素；不能将整张生成图直接当成正式部件。两处残留棋盘边缘随后只在新补片内修正 RGB，并保存 donor 坐标及改动 mask。批准 Body、原参考、已批准罗马兵均未变化。

源像素归属也完成纠正：裙摆和中央红布归 pelvis，袖片归上臂，远侧膝盖按真实边缘补回源像素重叠。整体源覆盖没有丢失或增加。原有低 Alpha 零散像素及隐藏接边差异按实际 256/192px 观感记录，不追求高倍像素完美。

## 可复现工具

1. tools/fix_cretan_archer_mask_ownership.py：从既有拆件候选纠正源像素归属。
2. tools/compose_cretan_archer_hidden_repairs.py：从已保存的真实 raw 生成结果合成四个身体补片，验证源像素不变。
3. 两个装备目录内的 process_assets.py / process_equipment.py：装备 raw→透明独立部件。它们处理已有输出，不再调用模型。
4. tools/review_cretan_archer_repaired_parts.py：完整 20 件、可控弓弦、默认重组、肘膝/肩髋及装备小幅运动审查。
5. tools/record_cretan_archer_self_repair.py：记录真实输入、参考、指导 mask、prompt、raw/derived SHA 和工具信息。
6. tools/approve_cretan_archer_parts.py --review-file reports/cretan_archer/self_repair/assembled/visual_gate.json：只有当前候选 SHA 与实际审查吻合才能正式发布。

再次处理 raw 会产生待审查候选，不得直接复用旧 SHA 的通过记录。完整追溯目录为 reports/cretan_archer/self_repair/ 和 work/cretan_archer/self_repair/。

## 正式资产与门禁

assets/units/odyssey/cretan_archer/parts/ 包含 15 件身体和 bow、bow_string、quiver、cloak、arrow_single，共 20 件 1024×1536 RGBA PNG。tools/cretan_archer_parts_manifest.json 保存 SHA、source、局部补全记录、draw order、pivot 及默认可见状态。单箭默认隐藏；弓弦 PNG 同时提供原生 Line2D 的位置依据。

reports/cretan_archer/parts_gate.json 是格式与来源检查；reports/cretan_archer/self_repair/assembled/visual_gate.json 是 256/192px 实际视觉审查。重组重点是批准身份、轮廓、关节锚点、装备位置及比例。AI 隐藏区域、正常关节重叠和不可见的高分辨率接边不作为像素差值阻塞条件。

源像素及 Complete Body 不再重做。若大角度动画出现连接问题，首先修改关键帧或原生局部蒙皮，只有明确证明素材不足才处理对应独立部件。
