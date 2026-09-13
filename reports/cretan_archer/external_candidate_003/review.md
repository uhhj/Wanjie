# Complete Body 候选 003 审查

**当前：PENDING_DESIGN_APPROVAL。透明背景问题已解决，尚未批准替换身体基线。**

原样归档 `work/cretan_archer/raw/external_complete_body_candidate_003.png`。SHA256：`a8257d52983c75656696a4342ca4d11f260ace24a5f3c24e3bf7d4a8baffcbfd`。1024×1536、RGBA、Alpha 0–254；不是 RGB 黑底，也没有上一版烘焙的棋盘格。候选、五张源图及 Roman Guard 均未修改；没有调用 AI。

## 已观察通过的部分

- 弓、箭袋、披肩已去除，双手双腿可见完整。
- 未出现第一版近侧腰部大短剑或 CODEX 的头盔、高领重甲。
- 头部位置和总体站姿比候选 001 更接近冻结 Rig Master。
- 白、50%灰、蓝底下 256/192/128px 静态背景审查通过，没有明显棋盘格、黑底残留或背景噪点。不因高倍边缘瑕疵恢复 Alpha 修图。

## 仍需设计确认

脸部笔触、胡须/皮肤明暗及皮甲、护胫材质仍有可见重绘痕迹。`structural_detail_review.png` 使用相同源图坐标裁片直接比较；不是以高倍微小 Alpha 瑕疵判失败。当前不把相近的护胫绑带排列夸大为新装备类型，也不声称角色变成了另一个兵种。

用户先前要求保留可见脸部与冻结设计，仅局部补全遮挡。本次只发送新图片，尚未明确授权接受这些可见重绘作为新基线。因此可以通过“静态背景显示”子项，但不能直接将整个 Complete Body 或正式资产链标记 PASS。

若用户明确接受本版身体美术，应保留原 Rig Master 不动，另记录用户批准的身体基线和真实外部来源，随后处理派生 Alpha 的 254→255、校准部件/pivot，并通过实际重组验证。不能补造 001–003 的局部编辑过程或模型调用记录。

## 文件

- `source_comparison.png`：同画布母图/候选。
- `combat_scale_review.png`：三背景、三尺寸静态审查；统一按母图身体约 1340px 高度缩放，保留候选与母图的相对锚点/比例差异。
- `structural_detail_review.png`：脸、胸部皮甲、远侧护胫同坐标裁片。
- `format_review.json`、`complete_body_gate.json`：格式实测和各项判定。

正式部件 0/20，重组、关节、动画、事件与 smoke 均未执行，Godot NOT_READY。
