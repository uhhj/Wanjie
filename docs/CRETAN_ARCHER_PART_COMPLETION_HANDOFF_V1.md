# 获批 Body 后的局部部件补全交接

用户已明确“接受”候选 003。**Complete Body PASS，保持冻结，不再修脸、服装或整个人。** 新身体记录在 `reports/cretan_archer/approved_body_baseline.json`，原 Rig Master 仍用于装备可见像素。

本轮已提取 15 个身体候选、4 个可见装备候选，共 19 个同画布 RGBA 候选。文件在 `work/cretan_archer/candidates/parts/`；正式目录仍未批准。不能将“19 个文件存在”混同于 20 个完整可动画部件通过。

## 已实际暴露的局部缺失

| job id | 输入部件 | 原因 |
|---|---|---|
| pelvis_under_near_hand | pelvis | 近手移开时原手形区域成为裙布透明洞，256/192px 都可见 |
| leg_near_thigh_hidden_hip | leg_near_thigh | 当前可见大腿起于裙摆，缺少通向髋点的隐藏上段 |
| leg_far_thigh_hidden_hip | leg_far_thigh | 同上；不能复制裙布条带假装腿部重叠 |
| torso_under_near_arm | torso | 肩/躯干被上臂与短袖遮住，拆开后尚无完整可旋转的连接 |

每项 mask、prompt 位于 `work/cretan_archer/part_completion/<job id>_mask.png` / `_prompt.txt`。精确输入、哈希、参照身体、输出路径见 `reports/cretan_archer/parts_v1/local_completion_jobs.json`。总览图 `reports/cretan_archer/parts_v1/local_completion_review.png`。

这些是**独立部件**局部补全，不回写 Complete Body。以相应透明部件为 input，批准身体只作结构与肤色/材质对位参考，白色 mask 内补齐隐藏像素。头、手、膝、脚及可见设计不能重画。mask 为待局部边界审查的草稿；不存在已调用成功的模型作业。

外部结果到达后可导入，例如：

```powershell
Set-Location D:/Wanjie/documents/Wanjie
$archerPython = 'C:/Users/Lenovo/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
& $archerPython tools/import_cretan_archer_part_completion.py --job pelvis_under_near_hand --result D:/Wanjie/documents/Wanjie/work/cretan_archer/raw/pelvis_fixed.png --tool-id '实际工具及模型'
```

导入器拒绝 mask 外像素变化、过期 source/mask/body SHA、错误 canvas/mode 和覆盖已有结果；不会自动标记正式通过。复查局部旋转后才替换对应候选，不重做已通过 Body。不要运行候选生成器去覆盖外部补全结果，导入结果另存于 part_completion。

## 装备仍缺什么

`reports/cretan_archer/parts_v1/equipment_visible_pixel_review.png` 是实际可见像素提取，非完整装备验收。当前弓的握柄处被持弓手遮挡，弦被手臂遮挡的区段缺失；箭袋被头发与肩披布遮挡；披布候选仅包含当前可见部分，其与原衣服的边界也仍需独立审查。

下一步只处理独立装备，不生成整个人：

- **FULL_BOW_V1**：原 Rig Master 木弓、金属箍、弓尖和弓身像素优先保留，只补手挡住的握柄；不带手，不改弓形。弓弦另件，绑定点待实际校准。
- **BOW_STRING_V1**：独立可控弦，恢复被前臂遮挡区段，确保上下连接点与原弓一致；不能把弦焊进弓身。
- **FULL_QUIVER_V1**：保留原箭袋及箭羽可见设计，只补被身体/披布遮挡的背面轮廓，不带头发、头巾或人物。
- **FULL_CLOAK_V1**：只补独立披肩的隐藏连接和边缘，延续橄榄绿、暗红磨损边和原扣饰；不能夹带袖口、皮肤。
- **ARROW_SINGLE_V1**：当前 Master 只露出箭袋中箭羽和部分箭杆，缺一支完整箭。需同设计单支完整箭尖、箭杆、箭羽，RGBA、不含手/人物/箭袋。DESIGN 只作设计参考，不提取其人物像素；长度与弓的搭箭位置必须再验证，不能凭现有羽毛伪造已恢复完整箭。

所有候选 1024×1536、RGBA、透明，不 tight crop。对于尚未可确定的完整装备边界和箭长，不生成空 mask 或假 PNG。先完成装备局部参考/边界审查，再记录实际外部补全输入输出；当前没有这些完整装备的模型结果。

## 本轮实际验收范围

15 件身体零度重组在 256px 基本恢复批准 Body；近肘动作仍暴露裙布洞。远肘、双膝 ±20° 的 256/192px 预览未见明显断裂，仅为小范围静态测试，不代表肩髋或 Walk 已通过。预览保留真实缺口，不用遮盖片伪造 PASS。

没有原生弓箭手 Rig、完整装备重组通过、射箭动画、attack_release 或 smoke 结果。Godot handoff=NOT_READY，暂不启动正式 Rig。原有 Roman Guard 不变。
