from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
new=(ROOT/'reports/roman_heavy_slash/attack_animation.tres').read_text(encoding='utf-8').split('[resource]\n',1)[1]
for file in ['resources/roman_guard_animations_v1.tres','scenes/units/odyssey/roman_guard/roman_guard_rig.tscn']:
 p=ROOT/file;s=p.read_text(encoding='utf-8');pattern=r'(\[sub_resource type="Animation"[^\n]*\]\n)resource_name = "attack_01"\n.*?(?=\n\[)'
 s,n=re.subn(pattern,lambda m:m[1]+new.rstrip()+'\n',s,flags=re.S);assert n==1;p.write_text(s,encoding='utf-8')
