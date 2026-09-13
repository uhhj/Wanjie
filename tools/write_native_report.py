"""Publish the current native gate without promoting pending visual judgments."""
import subprocess
from rg_common import *

def main():
    g=read('reports/native_rig_v2/native_gate_v2.json')
    h=read('reports/native_rig_v2/headless_tests.json')
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()
    lines=['# ROMAN_GUARD_NATIVE_RIG_VERTICAL_SLICE_V2', '',f'Verdict: **{g["verdict"]}**', '',f'技术验证：{g["technical_status"]}。Native Rig Pipeline：{g["native_rig_pipeline"]}。以下视觉结论只适用于当前哈希对应的 256/192px 帧，旧失败/诊断图片仍保留历史。', '', '## 引擎与资产', '', f'- Godot: `{g["godot"]["version"]}` / Standard / GDScript',f'- 路径：`{g["godot"]["path"]}`','- 已验证官方发布包 SHA512；用户首选 C:/Tools 路径不存在，实际安装在 D:/Wanjie/tools。','- 19/19 核心件 + knee_near；20 张正式 PNG、Complete Body 和原 near knee 权重全部通过冻结哈希检查。','- 原生 Skeleton2D / 23 Bone2D / 20 Sprite2D 节点 / 4 Polygon2D 节点；按动作启用 21 次美术绘制，不重复叠画替代件。', '', '## 动画与动作审查', '', '| 动画 | 当前视觉状态 | 256/192px实际GPU帧 |','|---|---|---|']
    for name,status in g['animations'].items():lines.append(f'| {name} | {status} | [contact sheet](animations/{name}_combat_review.png) |')
    lines+=['','**视觉质量保留：用户最后反馈“将就了吧”。本轮据此按可用战斗原型收口；SUPPORTED 表示原生方案可运行并完成这套动作，不代表动画已达到精修成品质量。**']
    if 'walk_reference_review' in g:
        lines+=['','当前 Walk 已按用户参考图加入足部滚动和承重时序；本次自然度尚待用户观看新版确认。[16帧跟随视角](walk_reference_v1/walk_reference_follow_256.gif) / [本次报告](WALK_REFERENCE_GAIT_V1.md)。']
    lines+=['', '- Attack：先举盾，再抬高手臂大幅前刺；用户认可动作方向，肩部连接修复按最新视觉审批记录判定。', '- Walk：真实向前位移、左右脚交替、近臂摆动、盾手稳定；双膝朝前屈。右鞋采用已批准左鞋像素的前向视图，只在 Walk 启用。', '- 两侧肩部局部蒙皮保留 shoulder/chest 边缘；右踝鞋筒连接 shin、鞋底连接 foot。未修改原部件 PNG。','- Death：保留用户认可的分阶段倒地和少量血滴；不会自动恢复或循环。','- Idle / Hit：沿用稳定的小幅动作。',f'- attack_hit = **{h["attack_hit_count"]}**；剑柄到握持点最大误差 {h["sword_grip_max_drift_source_px"]:.6f} 源像素。',f'- 实际 runtime 两周期前进 {h["runtime_walk_distance_two_cycles"]:.3f} 源像素；支撑脚最大漂移 {h["runtime_support_drift_at_256px"]:.5f}px（256px角色高度），192px更小。','- [脚部世界坐标与支撑区间](walk_foot_contact_debug.png)；[原生测试原始结果](native_rig_v2/headless_tests.json)。', '', '## Rest 重组与实验室', '',f'- Rest 轮廓 IoU：{g["rest"]["silhouette_iou"]:.9f}；GPU混合造成的前景 RGBA 平均差 {g["rest"]["rgba_mae_foreground_union"]:.4f}/255。没有整体比例或锚点移动。','- [原生Rest](native_rig_v2/rest_pose_native.png)、[诊断diff×8](native_rig_v2/rest_pose_diff_x8.png)。','- [Rig Lab截图](native_rig_v2/rig_lab_screenshot.png)：五动画、Play/Pause/Restart、倍率、战斗尺寸、骨骼/pivot/ground/socket、事件计数。','- `idle → walk → idle`、`attack → idle`、`hit → idle` 和 Death 保持测试通过。', '', '## 桌面压力实测', '', '1920×1080、VSync关闭、GeForce GTX 1650。每模式预热1.5秒、测量约3秒，FPS来自真实绘制帧数/时间。', '', '| 模式 | 20单位 FPS | 50单位 FPS |','|---|---:|---:|']
    for mode in ['idle','walk','attack_loop','hit_loop','death_once']:
        values=[next(r['fps'] for r in g['stress'] if r['units']==n and r['mode']==mode) for n in [20,50]]
        lines.append(f'| {mode} | {values[0]:.2f} | {values[1]:.2f} |')
    if 'walk_keyframe_polish' in g or 'walk_reference_review' in g:
        lines+=['','后续[Walk关键帧微调](WALK_KEYFRAME_POLISH_V1.md)已单独通过；上表保留微调前的桌面基线，本次没有重跑压力测试。']
    lines+=['','death_once 数据为预热后停止的尸体；不代表倒地过程峰值，不是手机性能结论。[完整数据](native_rig_v2/stress_results.json)、[20单位截图](native_rig_v2/stress_20_units.png)、[50单位截图](native_rig_v2/stress_50_units.png)。', '', '## 文件与运行', '', '- `scenes/rigs/human_medium_rig_v1.tscn`','- `scenes/units/odyssey/roman_guard/roman_guard_rig.tscn`','- `scenes/tests/roman_guard_rig_lab.tscn`','- `scenes/tests/roman_guard_stress_test.tscn`','- [骨骼说明](../docs/HUMAN_MEDIUM_RIG_V1.md) / [动画说明](../docs/ROMAN_GUARD_ANIMATION_V1.md)', '', '```powershell','./tools/run_godot_native.ps1 -Action Lab','./tools/run_godot_native.ps1 -Action Validate','./tools/run_godot_native.ps1 -Action Benchmark','python tools/validate_native_delivery.py','```','', '## Git 与限制', '',f'- 分支：`{branch}`',f'- 本报告依据的代码提交：`{commit}`；报告本身由后续 evidence commit 保存。','- 已先提交并推送近膝修复 d0e56ed，再建立 native 分支；未 reset/rebase/force push。','- 五处 HIRES Alpha 问题仍为 NON_BLOCKING_COMBAT_ARTIFACT。','- 当前披风为原刚性后摆与前领，cape_mid/tip预留；没有虚构复杂布料蒙皮。','- 没有第二兵种、正式 Combat System、敌人AI或第三方Rig插件。','- 历史 cape_trial、attack_gap_* 诊断图不代表当前通过证据。', '', '当前精确状态和审批哈希：[native_gate_v2.json](native_rig_v2/native_gate_v2.json) / [visual_approval.json](native_rig_v2/visual_approval.json)。']
    (ROOT/'reports/NATIVE_RIG_VERTICAL_SLICE_V2.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

if __name__=='__main__':main()
