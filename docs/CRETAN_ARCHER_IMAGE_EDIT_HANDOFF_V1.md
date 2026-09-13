# Cretan Archer：局部编辑交接 V1

当前只完成生产准备，尚无 Complete Body。现有参考图编辑工具没有可核实的专用 mask 参数；本机未发现已配置的局部 inpaint API/CLI。因此按任务第 5 节回退，未调用生成式编辑，没有把整图重画冒充局部补全。

项目根目录：`D:/Wanjie/documents/Wanjie`。以下路径均相对该目录。所有编辑结果放在 `work/cretan_archer/raw/`，原始图片及 Roman Guard 保持只读。

## 三次顺序编辑

| 阶段 | input | mask（白色可编辑） | 完整 prompt | 导入后的 output |
|---|---|---|---|---|
| 001 去弓 | `art_source/odyssey/cretan_archer/OD_UNIT_02_CRETAN_ARCHER_RIG_MASTER_V1.png` | `work/cretan_archer/masks/001_remove_bow.png` | `work/cretan_archer/prompts/001_remove_bow.txt` | `work/cretan_archer/01_no_bow.png` |
| 002 去箭袋 | 上一步通过审查的 `01_no_bow.png` | `work/cretan_archer/masks/002_remove_quiver.png` | `work/cretan_archer/prompts/002_remove_quiver.txt` | `work/cretan_archer/02_no_bow_no_quiver.png` |
| 003 去披布 | 上一步通过审查的 `02_no_bow_no_quiver.png` | `work/cretan_archer/masks/003_remove_cloak.png` | `work/cretan_archer/prompts/003_remove_cloak.txt` | `work/cretan_archer/03_complete_body_base.png` |

将每行的 input + mask + prompt 交给实际支持局部蒙版编辑的工具，例如用户自己的 Image 2.5 工作流。此处没有声称已发现或调用某个 Image 2.5 API。必须记录实际工具/模型名称。

三个 mask 都是可审查草稿，见 `reports/cretan_archer/occlusion_mask_review.png`。编辑前检查：001 的持弓手指/握柄边界和穿过护腕的弓弦；002 的箭袋与头巾飘带交界；003 的白色短袖边缘、披肩扣和胸甲上缘。002、003 要在上一阶段真实通过后重新核对，不能将草稿直接标记批准。

不得编辑 mask 外区域。不得改脸、发型、头巾、比例、衣服或姿态；不得引入 CODEX 的头盔、高领、重甲。只用 Rig Master 的派生链生产像素。输出真实 RGBA PNG、1024×1536，不能烘焙黑底/棋盘格。保留原有透明度；本阶段不能把全图 Alpha 254 统一改成 255，否则会触发 mask 外改动门禁。

## 导入与逐阶段审查

PowerShell：

```powershell
Set-Location D:/Wanjie/documents/Wanjie
$archerPython = 'C:/Users/Lenovo/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
& $archerPython tools/cretan_archer_pipeline.py verify-frozen
& $archerPython tools/cretan_archer_pipeline.py import-stage --stage 1 --result D:/Wanjie/documents/Wanjie/work/cretan_archer/raw/001_external.png --tool-id '实际编辑工具及模型名称'
```

脚本拒绝尺寸不符、非 RGBA、无透明背景、mask 外任一 RGBA 像素变化，且不会覆盖已有输出。导入成功后查看实际生成的 `reports/cretan_archer/001_remove_bow_review.png`，确认去弓完整、手与衣服补全合理、无身份漂移。只有看过图且通过，才执行：

```powershell
& $archerPython tools/cretan_archer_pipeline.py review-stage --stage 1 --decision PASS --notes '填写实际观察结果，不复制占位文字'
```

未通过用 `--decision FAIL`，不要继续下一阶段。002、003 同样操作；把 stage 改成 2/3，result 对应 `002_external.png` / `003_external.png`。审查记录绑定 input、output、mask、prompt 的 SHA256；其中任何一项变化都使审查失效。重跑 prepare 不覆盖已有 mask、prompt 或 job。

如果原工具会重新编码未编辑区域的像素，需在该工具真正锁定保护区域后重新导出，不能用后期贴回原图来伪造局部编辑合格。已有失败输出需要另立版本，当前脚本拒绝覆盖；不会自动删除失败证据。

## 最后单独处理 Alpha

Rig Master 本身为 RGBA，Alpha 范围 0–254，无需黑底分离。源图脚下有可见投影；它不能成为会随脚旋转的身体部件。003 通过后，再从它的 Alpha 制作同画布 L 模式灰度 PNG：`work/cretan_archer/raw/complete_body_alpha.png`。

仅去除脚下背景投影，保护鞋底和内部暗色；原有不透明主体 254 可以归一到 255，保留轮廓抗锯齿。不要凭 RGB 黑色阈值删除暗色描边。该 Alpha 需要看白/灰背景确认，当前尚未制作，不能凭现有草稿推断脚底边界。

```powershell
& $archerPython tools/cretan_archer_pipeline.py import-matte --result D:/Wanjie/documents/Wanjie/work/cretan_archer/raw/complete_body_alpha.png
& $archerPython tools/cretan_archer_pipeline.py body-reviews
```

导入器生成新的 `work/cretan_archer/04_complete_body_rgba.png`，不覆盖 003，不改变任何 RGB。允许 Alpha 降低及 254→255；禁止凭 matte 在背景新增前景。所有删除区域仍需视觉审查。

查看新生成的 `complete_body_review.png` 和 `combat_scale_visual_review.png`（均在 `reports/cretan_archer/`）。后者按实际角色高度显示 256/192/128px，白/50%灰/棋盘背景；没有已确认的独立战场背景，棋盘不冒充战场。

在 `reports/cretan_archer/body_review_request.json` 逐项填写真实审查结果与 notes，保留当前图片 SHA，再执行：

```powershell
& $archerPython tools/cretan_archer_pipeline.py gate --review-file D:/Wanjie/documents/Wanjie/reports/cretan_archer/body_review_request.json
```

全部内容、格式、来源门禁通过才解锁正式拆件。缺图时退出码 2、status=NOT_RUN 是预期停止，绝不是 Body PASS。仅高倍可见的微小边缘瑕疵按战斗尺寸标准记录为 NON_BLOCKING_COMBAT_ARTIFACT，不恢复 Roman Guard 的像素级修补路线。

之后从当前文件和 SHA 记录继续 20 个正式部件、真实 Rig 和动画生产；这些下游工作当前尚未执行，脚本不会凭 Body PASS 自动声称完成。
