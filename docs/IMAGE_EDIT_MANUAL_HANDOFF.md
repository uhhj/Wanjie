# 当前交接：FIX_COMPLETE_BODY_GATE_V1

**BLOCKED_LOCAL_INPAINT_UNAVAILABLE。以下 004 → 005 是当前唯一续跑顺序。**

实际仓库仍为 `D:\Wanjie\documents\Wanjie`，分支 `feature/roman-guard-ai-rig-assets-v1`。本轮不重跑去盾，也不从 01 重做 B/C。继续使用现有 `work/03_complete_body_base.png`，SHA256 `492adab57065964962b6a7ef635cbb8990a4e774bdb5ec2ee30989049624c5bf`。先阅读 [修复计划](../reports/complete_body_fix_plan.md) 和 [本轮结果](../reports/FIX_COMPLETE_BODY_GATE_V1.md)。

当前已验证的工具没有可靠的局部 mask/inpainting 接口。`image_gen.imagegen` 不提供独立 mask 参数；历史 Python 导入/合成脚本也不是局部 inpainting 客户端。不能用整图编辑后合成保护区绕过本轮 STOP 规则。不要把下表当成已经调用成功的结果。

在实际支持局部 mask 的 Image 2.5 或其他编辑接口可用且能力已验证后，依次交付以下材料（路径相对仓库根目录）：

| Job | Input | Mask 草案 | Prompt | 真实结果目标 |
|---|---|---|---|---|
| 004 | `work/03_complete_body_base.png` | `work/masks/fix_skirt_seam_v2.png` | `work/prompts/004_fix_skirt_seam.txt` | `work/04_skirt_fixed.png` |
| 005 | **实际完成且裙甲修复通过审查的** `work/04_skirt_fixed.png` | `work/masks/remove_unapproved_collar_v2.png` | `work/prompts/005_remove_unapproved_collar.txt` | `work/05_complete_body_candidate_v2.png` |

005 的参考顺序为 `D:\Wanjie\documents\pictures\` 内的 DESIGN_V1、RIG_MASTER_V1、COMBAT_LOOK_V1；完整文件名和 SHA 见 `reports/complete_body_fix_references_v2.json`。不使用 CODEX 原画补人体或决定隐藏颈甲。

两张 mask 均为 1024×1536 的 8-bit L，白色允许编辑、黑色保护。应先查看 `reports/complete_body_fix_masks_review.png`；005 mask 在当前 03 上准备，必须核对实际 04 的颈肩坐标仍一致。按照真实编辑接口的 mask 约定转换，不猜测 API / endpoint / alpha 语义。记录每次实际输入、mask、提示词、真实工具/模型标识、输出哈希与调用时间，保留未执行记录的 Git 历史。密钥仅从环境变量读取。

真实输出须保持 1024×1536、原坐标、透明 RGBA；不能带背景棋盘格。核验 mask 外原像素及脸、头盔、冠饰、胸甲、腿部比例没有变化；若编辑器未遵守局部范围，保留失败证据并停止。不得用原图保护区后期覆盖来掩盖接口不支持局部编辑的事实。

只有真实 05 存在，才生成 `reports/complete_body_review_v2.png`、`reports/complete_body_detail_review_v2.png` 并完成 v2 十项人工/视觉审查。当前 `reports/complete_body_gate_v2.json` 为 BLOCKED、四项 pass 为 null；不运行旧 PASS 示例解锁部件。全部验收后才更新流水线人体来源及哈希绑定，继续原 19 部件流程；当前未进行这一切换。

`tools/prepare_complete_body_fix_v2.py` 只制作准备材料，不调用 AI；它在旧基线发生改变或已有 04/05 时拒绝运行，避免覆盖后续真实进度。

<details>
<summary>历史 A/B/C 交接记录（保留背景，本轮禁止执行其中的重跑和导入命令）</summary>

## 上一轮交接记录

仓库根目录：`D:\Wanjie\documents\Wanjie`。远端为 `https://github.com/uhhj/Wanjie`。不需要重新创建工程，也不需要重新生成母图。

已真实调用工具 `image_gen.imagegen` 三次。后端模型名未公开，不能宣称它是 Image 2.5；没有独立 mask 参数。结果都是带棋盘格的 RGB。没有发现配置好的图像 API key，也没有虚构 endpoint。Python 管理脚本不会调用不存在的本地图像 API。

如在你可用的 Image 2.5 或具有实际 mask/inpainting 的编辑器中继续，请按下表提供 **input + mask + prompt**。这些都是已经存在的文件。mask 是 8-bit L：**白色允许编辑、黑色保护**。如果目标 API 用 alpha=0 表示编辑，应按照该接口真实文档转换，不可猜测；不要直接把 L mask 当透明 mask 发送。

| 次序 | Input | Mask | Prompt | 保存返回结果 |
|---|---|---|---|---|
| A（只在手部边缘需要重做时） | `art_source/odyssey/roman_guard/OD_UNIT_01_ROMAN_GUARD_RIG_MASTER_V1.png` | `work/masks/remove_shield.png` | `work/prompts/001_remove_shield.txt` | `work/imports/001.png` |
| B（必须修正） | `work/01_no_shield.png` | `work/masks/remove_sword.png` | `work/prompts/002_remove_sword.txt`，附加下述 B 修正要求 | `work/imports/002.png` |
| C（B 通过后必须修正） | **经修正并通过的** `work/02_no_shield_no_sword.png` | `work/masks/remove_cape.png` | `work/prompts/003_remove_cape.txt`，附加下述 C 修正要求 | `work/imports/003.png` |

B 附加要求：仅在剑遮挡区补全真实的裙甲、红色布料、大腿和膝甲；布褶方向、色值、轮廓必须连续接上 mask 四周原像素，不留下斜向贴片接缝。保留手和全部未遮挡部位。不得通过重绘整个裙甲规避接缝。

C 附加要求：移除披风及围领，沿已露出的胸肩甲保守补全上缘；不要新增本轮候选中的竖起高领甲或其他未获批准的款式。只补全被披风遮挡的结构。保留裙甲红内衬、肩甲红衬及现有肌肤。透明区不能含棋盘格。

要求每张返回图为真实透明 RGBA、1024×1536、原坐标、未裁切。不要先把 RGB 改成 RGBA 冒充透明。若返回 RGB，导入脚本会拒绝；需要独立可审查的 alpha matte，不能沿用本轮 matte 去适配结构不同的新结果。

若实际使用的提示词包含附加修正或其他调整，先把完整实际文本保存到对应 `work/prompts/*.txt`，再导入。外部返回结果以 `EXTERNAL_RESULT_IMPORT` 记录，不会伪称由本地脚本调用成功。

下面命令在仓库根目录执行，`python` 需要 Pillow 与 NumPy（见 `requirements.txt`）。本机已验证运行环境：`C:\Users\Lenovo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`。

```powershell
python tools/validate_source_asset.py
python tools/ai_inpaint_roman_guard.py prepare 002_remove_sword
# 获得真实的 B 返回图后，先归档 B 以及依赖它的 C 当前输出与记录：
python tools/ai_inpaint_roman_guard.py archive 002_remove_sword
python tools/ai_inpaint_roman_guard.py import-result 002_remove_sword --result work/imports/002.png --tool-identifier "manual:Image 2.5 (user-declared)"
```

导入后查看生成的 `reports/002_remove_sword_review.png`。**只有确实审查通过**，才执行记录；用真实审查者与具体结论替换下面的示例文字：

```powershell
python tools/record_art_review.py 002_remove_sword --file work/02_no_shield_no_sword.png --status PASS --reviewer "实际审查者" --notes "具体说明裙甲/布褶/大腿接缝已消除且原设计保持，记录实际检查结果。"
python tools/ai_inpaint_roman_guard.py prepare 003_remove_cape
# 把修正后的 B + C mask + C prompt 交给编辑器，再导入 C：
python tools/ai_inpaint_roman_guard.py import-result 003_remove_cape --result work/imports/003.png --tool-identifier "manual:Image 2.5 (user-declared)"
```

重新审查 C 与完整底版后，分别对 `003_remove_cape`、`complete_body` 记录真实结论。失败就记录 FAIL，不要机械执行 PASS 命令。审查与文件 SHA256 绑定；改图后旧 PASS 自动失效。

随后处理 `docs/TODO_PART_MASK_REVIEW.md` 中 16 件身体 mask；先补隐藏区、检查关节重叠，逐件提取与审查。工具不会自动猜测身体切线。装备也必须补全缺失并审查。全部通过后运行 `python tools/run_validation.py`，检查重组和旋转图，记录对应的 `recomposition`、`joint_rotation` 审查并重跑。`check_godot_handoff.py` 只有在全部当前验证与审查通过时才输出 READY。

不需要给脚本提供 API secret。未来若接入真实 API，key 只能读取环境变量，不能写入提示词、JSON、日志或 Git。

</details>
