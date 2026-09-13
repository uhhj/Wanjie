# 箭袋与披肩：实际补全结果

已分别执行两次 `image_gen__imagegen`，输入只有 Rig Master 的局部装备裁片。未生成整个人物；未修改批准 Body、原 Master、Roman Guard 或正式 parts manifest。DESIGN 只用于人工理解箭袋结构，CODEX/WALK 未参与像素生产。

可交给整体资产审查的结果：

- `work/cretan_archer/self_repair/equipment_quiver_cloak/quiver_completed_same_canvas.png`
- `work/cretan_archer/self_repair/equipment_quiver_cloak/cloak_completed_same_canvas.png`

两张都是 1024×1536 RGBA，Alpha 最小 0、最大 255，保持原 Master 画布位置。箭袋建议旋转点 `(325,333)`；披肩建议旋转点 `(500,360)`。此处没有改写正式 pivots。

## 来源与处理

工具真实返回 RGB、烘焙棋盘背景，不能将其声称为原生透明结果。`ai_jobs.json` 保存真实工具、完整提示词、输入/输出路径与 SHA；没有虚构模型版本或 native mask 参数。

先仅在生成装备图上分离边界连通的亮中性棋盘背景（RGB 最大最小差 ≤24、最小通道 ≥145），再按原裁片尺寸对位。原图装备可见像素通过独立 ownership mask 逐像素复制；只有隐藏部位使用实际生成结果。没有通过全图背景替换来修改 Body。

箭袋保留原箭羽、铜箍、回纹、牛头和已见皮革；补齐被披肩/身体遮住的下段及底部。源像素归属数 23,772，归属内 RGBA 变化 0。隐藏补全 15,583 像素。

披肩剔除了旧候选夹带的箭袋、皮肤、袖子与斜皮带；保留原橄榄绿褶皱、暗红边、扣饰。源像素归属数 23,664，归属内 RGBA 变化 0。隐藏补全 3,113 像素。原箭袋后方上缘需要局部生成纹理对位：只在保存的 border alignment mask 内，取相邻生成披布纹理延续。此处原图低 Alpha 背景残影不作为可见披布保留；没有修改主体不透明原像素。

最终 mask、raw、生成 Alpha、对位图和 `process_equipment.py` 均位于上述 work 目录，可重做确定性合成；脚本不调用模型。运行重合成后 review_status 会回到待审查，不能自动继承旧人工审查。

## 实际审查

- `equipment_combat_scale_review.png`：批准 Body 可见高度按 Alpha≥128 得到 1,344 源像素，实际展示 256/192px。白、灰、蓝底及独立装备已检查，没有明显棋盘残留、人物像素夹带或装备断裂。
- `equipment_small_motion_review.png`：固定 Body 下箭袋/披肩各自 -5°/0°/+5°，256/192px，未见明显结构断裂。只是装备小范围运动探查，不能代替正式 Native Rig 动画验收。
- `quiver_completed_detail_review.png`、`cloak_completed_detail_review.png`：保留高分辨率证据。

高分辨率仍有箭袋隐藏左边接合的少量轮廓偏差、披肩隐藏上缘局部纹理过渡；当前组合的 256/192px 未见显著问题，记作 NON_BLOCKING_COMBAT_ARTIFACT。没有声称像素级完美。

当前结论是两张候选可继续整体重组与关节审查；本子任务未正式 promotion，也未声称 20 Parts、Godot Handoff 或动画通过。
