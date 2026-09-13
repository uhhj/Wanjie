"""Offline diagnostic only; native GPU captures remain the animation art gate."""
import math
import numpy as np
from PIL import Image,ImageDraw
import cretan_archer_pipeline as p
from build_cretan_archer_native_data import rotation,vec

def main():
    data=p.load('resources/cretan_archer_rig_v1.json');anims=p.load('resources/cretan_archer_animations_v1.json')
    root=p.ROOT/p.WORK/'self_repair/repaired_parts';out=p.ROOT/p.REPORT/'native/key_diagnostics';out.mkdir(parents=True,exist_ok=True)
    images={n:Image.open(root/(n+'.png')).convert('RGBA') for n in data['draw_order']}
    for name,entry in anims.items():
        if name not in ['walk','attack_01','death']:continue
        indexes=[int(i*(len(entry['poses'])-1)/7) for i in range(8)];tiles=[]
        for index in indexes:
            pose=entry['poses'][index];tf={};globalr=rotation(pose['visual_rotation']);offset=vec([400,400])+vec(pose['visual_offset'])
            for n,rec in data['bones'].items():
                off=vec(rec['local_position'])
                if n=='pelvis':off+=pose['pelvis_offset']
                for side in ['near','far']:
                    if n=='leg_'+side+'_thigh':off+=pose['hip_offsets'][side]
                    if n=='arm_'+side+'_upper':off+=pose['shoulder_offsets'][side]
                if n=='arrow_socket':off=vec(pose['bow_draw_point'])
                par=rec['parent'];rr,pp=tf[par] if par else (np.eye(2),vec([0,0]))
                angle=pose['arrow_rotation'] if n=='arrow_socket' else pose['rotations'][n]
                tf[n]=(rr@rotation(angle),pp+rr@off)
            result=Image.new('RGBA',(2100,2100))
            for n in data['draw_order']:
                if n=='arrow_single' and not pose['arrow_visible']:continue
                bone=data['attachments'][n];rr,pp=tf[bone]
                if n=='bow_string':
                    points=[vec([-54,-575]),vec(pose['bow_draw_point']),vec([-125,515])]
                    pts=[tuple(globalr@(pp+rr@q-vec(data['origin']))+vec(data['origin'])+offset) for q in points]
                    ImageDraw.Draw(result).line(pts,fill=(66,48,29,255),width=2);continue
                pivot=vec([282,725]) if n=='arrow_single' else vec(data['bones'][bone]['pivot'])
                finalr=globalr@rr;translation=globalr@(pp-rr@pivot-vec(data['origin']))+vec(data['origin'])+offset
                inv=finalr.T;tr=-inv@translation
                layer=images[n].transform(result.size,Image.Transform.AFFINE,tuple([*inv[0],tr[0],*inv[1],tr[1]]),Image.Resampling.BICUBIC)
                result.alpha_composite(layer)
            v=result.resize((401,401),Image.Resampling.LANCZOS);tiles.append((entry['times'][index],p.composite(v,'#d6e1e7')))
        sheet=Image.new('RGB',(1604,858),'#eee');d=ImageDraw.Draw(sheet)
        for i,(t,img) in enumerate(tiles):
            x=i%4*401;y=i//4*429;sheet.paste(img,(x,y+28));d.text((x+6,y+5),f'{name} {t:.3f}s | offline diagnostic',font=p.font(14),fill='black')
        sheet.save(out/(name+'.png'))
    print(str(out))
if __name__=='__main__':main()
