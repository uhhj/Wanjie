# 高斯步枪兵图像编辑交接 V1

当前环境无图像生成/修补接口，需要把下面的 input+mask+prompt 交给图像编辑工具（Image 2.5 或同等能力），结果放回后由流水线继续。

## Job 001_remove_rifle

- **Input**：`art_source/odyssey/gauss_rifleman/OD_UNIT_05_GAUSS_RIFLEMAN_RIG_MASTER_V1.png`（1024×1536 RGBA，只读）
- **Mask**：`work/gauss_rifleman/masks/remove_rifle_draft.png`（草案，覆盖步枪全长+双手+裕量；审查图 `reports/gauss_rifleman/occlusion_mask_review.png`）
- **Prompt**：`work/gauss_rifleman/prompts/001_remove_rifle.txt`（移除步枪、补全胸前挂具/双手/前侧小臂/枪托遮挡区，禁止重新设计、禁止残留枪械部件、透明背景）
- **输出要求**：1024×1536，RGBA 透明背景；除 mask 区域外与输入逐像素一致

## 返回后操作

```text
把结果保存为 work/gauss_rifleman/raw/001_remove_rifle.png，然后执行：
python tools/import_gauss_completion.py import-result 001_remove_rifle --result work/gauss_rifleman/raw/001_remove_rifle.png
```

导入工具会校验尺寸、mask 外零改动，生成 `work/gauss_rifleman/001_no_rifle.png` 并更新 job 记录为 IMPORTED_PENDING_ART_REVIEW。美术审查通过后继续拆件，不重跑已完成步骤。

## 注意

- 若编辑工具返回 RGB（棋盘格画进背景），导入工具会拒绝并要求先抠透明底。
- mask 是草案：编辑前可按审查图微调多边形（坐标在 masks/remove_rifle_draft.json）。
- 后续可能的第二个 job（前侧手/小臂细节补全）在拆件阶段按需建立。
