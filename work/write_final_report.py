import sys,subprocess,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from rg_common import *

original_validation=json.loads(subprocess.check_output(['git','show','7ae2cac:reports/validation_run.json'],cwd=ROOT,text=True,encoding='utf-8'))
test_run=next(r for r in original_validation['runs'] if r['script']=='test_pipeline_safety.py')
assert test_run['exit_code']==0 and 'Ran 12 tests' in test_run['stderr']
write('reports/tool_tests.json',{'status':'PASS','test_count':12,'execution_timestamp':original_validation['timestamp'],'record_recovered_from_commit':'7ae2cac','note':'Executed test evidence retained separately from later production-only validation runs. Tests used isolated synthetic fixtures, not real formal parts.','run':test_run})
source=read('art_source/odyssey/roman_guard/source_manifest.json'); parts=read('reports/parts_validation.json'); integrity=read('reports/complete_body_integrity.json')
commits=subprocess.check_output(['git','log','--format=%h %s'],cwd=ROOT,text=True,encoding='utf-8').strip().splitlines()
remote_url=subprocess.check_output(['git','remote','get-url','origin'],cwd=ROOT,text=True,encoding='utf-8').strip()
manual=['reports/complete_body_review.png','reports/complete_body_detail_review.png','reports/001_hand_matte_review.png','reports/equipment_extraction_review.png','reports/occlusion_mask_review.png','reports/helmet_edge_review.png']
for p in manual: assert (ROOT/p).is_file()
status={
 'task':'ROMAN_GUARD_AI_RIG_ASSET_PIPELINE_V1','verdict':'BLOCKED','art_pipeline':'STOP_ART_PIPELINE','repository_root':str(ROOT),
 'source':{'external_path':source['external_source'],'project_path':source['source_file'],'sha256':source['sha256'],'dimensions':[source['width'],source['height']],'rgba':source['rgba'],'read_only':True},
 'image_editing':{'tool_detected':'YES','tool':'image_gen.imagegen','model':'not disclosed','actual_calls':3,'native_mask_parameter':False,'raw_result_modes':['RGB','RGB','RGB'],'api_key_configured':False},
 'ai_stages':{'remove_shield':'EXECUTED_INTERMEDIATE_REVIEW_PASS','remove_sword':'EXECUTED_ART_FAIL','remove_cape':'EXECUTED_ART_FAIL'},
 'complete_body':{'status':'FAIL','file':'work/03_complete_body_base.png','sha256':sha('work/03_complete_body_base.png'),'blockers':['Diagonal skirt/cloth seams after sword removal','Raised metal collar not justified by frozen visible design','Local alpha edge quality still requires art correction']},
 'parts':{'required_count':19,'candidate_generated_extracted_count':3,'candidate_names':EQUIPMENT,'formal_generated_extracted_count':0,'formal_missing_count':19,'body_masks_missing_count':16},
 'recomposition':{'gate':'FAIL','execution':'NOT_RUN','reason':'Formal parts not approved; no fabricated recomposed or diff PNG'},
 'joint_tests':{'elbows':'NOT_RUN','knees':'NOT_RUN','shield':'NOT_RUN','sword':'NOT_RUN','reason':'Formal parts gate failed; synthetic tool tests are not character joint validation'},
 'godot_handoff':'NOT_READY','tools_tests':{'status':'PASS','count':12},
 'manual_review_images':manual,'manual_edit_resume_document':'docs/IMAGE_EDIT_MANUAL_HANDOFF.md',
 'git':{'repository':ROOT.name,'branch':'feature/roman-guard-ai-rig-assets-v1','commits_before_this_report':commits,'final_report_commit_subject':'chore: rename local repository to Wanjie and configure origin','remote':remote_url,'note':'Repository renamed to Wanjie on user request. Push and clean-tree verification are reported after committing this report; use git log / git status for current state.'},
 'timestamp':now()}
write('reports/final_status.json',status)
text=f'''# 最终验收：ROMAN_GUARD_AI_RIG_ASSET_PIPELINE_V1

**Verdict: BLOCKED**  
**STOP_ART_PIPELINE — Godot handoff: NOT_READY**

工程准备和真实 AI 尝试已完成；美术结果没有被伪标为通过。当前候选底版有裙甲接缝与未经确认的高领甲，正式人体拆分已停止。没有创建第二兵种。

项目仓库：`{ROOT}`。远端：`{remote_url}`。代码、资产、报告都在此目录。原始 PNG 保持只读，未覆盖。

## Source

- 外部原图：`{source['external_source']}`
- 仓库副本：`{source['source_file']}`
- SHA256：`{source['sha256']}`
- Dimensions：1024 × 1536
- RGBA：YES；原始 alpha 范围 0–254，原值完整保留。
- 两份源文件的最终 SHA256 相同。

## Image editing 与 AI 阶段

工具检测：**YES — image_gen.imagegen**，实际调用三次。后端模型标识未公开，不冒称 Image 2.5。环境变量未发现已配置图像 API key，项目没有已存在的图像 endpoint。工具没有独立 mask 参数。

三份原始返回图都是 RGB，棋盘格被绘入背景；没有直接作为透明素材使用。已记录原始结果、实际输入/输出 SHA256、实际提示词、区域参考、工具、时间、后处理 mask 和透明轮廓。受约束合成后的三张候选均是同画布 RGBA。

| 阶段 | 产物 | 状态 |
|---|---|---|
| remove shield | `work/01_no_shield.png` | 实际完成；通过中间图审查；补全持盾拳头 |
| remove sword | `work/02_no_shield_no_sword.png` | 实际完成；美术 FAIL，裙甲/红布斜向拼接痕迹明显 |
| remove cape | `work/03_complete_body_base.png` | 实际完成；美术 FAIL，高领甲结构待纠正、局部 alpha 边缘待修 |

Complete body：**FAIL**。双手双腿均存在，盾剑披风已移除，但结构与原设计连续性未达到生产标准。

三阶段 mask 外改动像素均为 **0**。最终已检查的冠饰/头盔区域及可见脸区域改动像素为 **0**。去披风 mask 曾误触头盔后缘，已缩小范围并恢复原像素；旧候选及记录已归档。数值证据：`complete_body_integrity.json`。这些检查不替代美术验收。

## Parts 与验证

| 项目 | 实际状态 |
|---|---|
| 必需 core parts | 19 |
| 已生成/提取候选 | 3：shield、sword、cape；均直接使用母图可见像素 |
| 正式部件 | **0 / 19** |
| 正式缺件 | **19** |
| 人体 mask | 16 件待正确底版与边界审查；未生成随机切线或空 mask |
| 同画布、RGBA | 3 张阶段候选和 3 张装备候选均满足；不代表正式通过 |
| Recomposition | 验收门禁 FAIL；实际 NOT_RUN，缺正式部件 |
| elbows / knees | NOT_RUN |
| shield socket / sword thrust | NOT_RUN |
| Godot handoff | **NOT_READY** |

正式 parts 目录只有 `.gitkeep`，没有假 PNG。剑柄在拳头后方仍有缺失，披风在身体后方的连续布面仍需补全；这些候选没有被冒充为可独立动画的完整装备。

没有生成虚假的 `roman_guard_recomposed.png`、`recomposition_diff.png` 或 `joint_rotation_test.png`。相应 JSON 清楚记录 NOT_RUN。脚本在真实 19 件通过后才生成这些图。

六个要求的基础脚本均已建立，另有真实结果导入/归档、部件提取、hash 审查和 Godot 门禁工具。已执行 **12 项隔离脚本测试，全通过**，包括错误源 SHA、RGB 假透明、画布不符、保护区约束、旧审查失效以及 18 个旋转预览用例的报告输出。测试是脚本验证，**不是**罗马盾兵的关节验收。详见 `tool_tests.json`。

## 人工需要看的图片

以下六张是当前需要检查的图，路径均相对仓库根目录：

'''+''.join(f'- `{p}`\n' for p in manual)+f'''

修正顺序：先处理 B 的接缝，再以通过的 B 作为 C 输入，保守补全颈肩甲；不能整体重画人物。每张所需 input + mask + prompt、归档/导入命令和续跑条件已经列在 `docs/IMAGE_EDIT_MANUAL_HANDOFF.md`。返回合格图片后可从同一流水线继续，无须重建工程。

## Git 与 Godot

仓库名称：`{ROOT.name}`；GitHub 所有者：`uhhj`；本地分支：`feature/roman-guard-ai-rig-assets-v1`。本报告写入前已有提交：

'''+''.join(f'- `{c}`\n' for c in commits)+'''

头盔保护区修正已提交为 `dcced3e`。用户随后确认将本地仓库改名为 `Wanjie`，并推送到 `https://github.com/uhhj/Wanjie.git`。本报告的路径更正随 `chore: rename local repository to Wanjie and configure origin` 提交。推送后的提交 SHA 与工作区检查见交付消息，也可运行 `git log --oneline` / `git status --short`。

用户确认从零建立仓库，因此没有既有原生 rig 可调用。按照素材门禁，没有开始创建 Godot 4.7.2 的 Skeleton2D/Bone2D 正式场景、HUMAN_MEDIUM_RIG_V1 或五个动画；没有安装第三方插件。只有完整素材和实际重组/关节验收都通过之后才能开始。
'''
(ROOT/'reports/FINAL_VERDICT.md').write_text(text,encoding='utf-8')
print('BLOCKED report written; 12 executed tool tests retained; 6 exact review images listed.')
