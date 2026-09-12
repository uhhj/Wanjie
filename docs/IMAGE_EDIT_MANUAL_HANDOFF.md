# 局部图像编辑交接与续跑

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
