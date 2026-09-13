"""Install exported Walk keys without reserializing the rig or other animations."""
import re,sys
from pathlib import Path
from rg_common import ROOT

def main():
    folder=sys.argv[1] if len(sys.argv)>1 else 'reports/walk_reference_v1'
    source=(ROOT/folder/'walk_animation.tres').read_text(encoding='utf-8')
    body=source.split('[resource]\n',1)[1].strip()
    pattern=r'\[sub_resource type="Animation" id="[^"]+"\]\r?\nresource_name = "walk".*?(?=\r?\n\[)'
    for name in ['resources/roman_guard_animations_v1.tres','scenes/units/odyssey/roman_guard/roman_guard_rig.tscn']:
        path=ROOT/name;before=path.read_bytes().decode('utf-8')
        match=re.search(pattern,before,re.S);assert match
        nl='\r\n' if '\r\n' in before else '\n'
        replacement=match.group().splitlines()[0]+nl+body.replace('\n',nl)+nl
        after=before[:match.start()]+replacement+before[match.end():]
        assert re.sub(pattern,'<WALK>',before,flags=re.S)==re.sub(pattern,'<WALK>',after,flags=re.S)
        path.write_bytes(after.encode('utf-8'))
    print('Only Walk resource key values installed')

if __name__=='__main__':main()
