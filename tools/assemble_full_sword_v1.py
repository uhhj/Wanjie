"""Keep original sword pixels; extract only generated missing grip from RGB reference."""
from rg_common import *
from cleanup_roman_guard_alpha_v2 import components
RAW='work/candidates/full_sword_v1_raw.png'
ORIGINAL='work/candidates/parts/sword.png'
OUT='work/candidates/parts/full_sword_v1.png'

def main():
    orig=rgba(ORIGINAL); generated=Image.open(ROOT/RAW).convert('RGB'); rgb=np.array(generated)
    assert generated.size==orig.size
    yy,xx=np.indices(rgb.shape[:2]);u=np.array([.829,.559]);u/=np.linalg.norm(u)
    along=(xx-270)*u[0]+(yy-839)*u[1];across=(xx-270)*u[1]-(yy-839)*u[0]
    roi=(along>=-8)&(along<=118)&(abs(across)<26)
    # Embedded checker squares are near-neutral and bright. Selection is restricted
    # to the actual grip corridor; no source body/weapon alpha is globally processed.
    spread=rgb.max(axis=2).astype(int)-rgb.min(axis=2).astype(int)
    selected=roi&((spread>22)|(rgb.max(axis=2)<120))
    labels,cc=components(selected);main_label=max(cc,key=lambda k:cc[k]['area']);selected=labels==main_label
    gm=Image.fromarray(selected.astype(np.uint8)*255)
    grip=Image.fromarray(np.dstack([rgb,np.array(gm)]))
    # A skin/red-cloth remnant on the old extraction lies outside the sword itself.
    remove=Image.new('L',orig.size);ImageDraw.Draw(remove).polygon([(322,903),(344,903),(351,916),(338,938),(322,934)],fill=255)
    o=np.array(orig);rem=np.array(remove)>0
    red_cloth=(xx>=330)&(xx<=355)&(yy>=919)&(yy<=960)&(o[:,:,0].astype(int)>2*o[:,:,1].astype(int))&(o[:,:,2]>=o[:,:,1])&(o[:,:,1]<45)
    rem|=red_cloth
    # Exclude the cloth-side pixels outside the observed straight guard outline.
    rem|=(xx>=330)&(xx<338+.7*(951-yy))&(yy>=919)&(yy<=951)
    remove=Image.fromarray(rem.astype(np.uint8)*255)
    removed=int(((o[:,:,3]>0)&rem).sum());o[rem]=0
    base=Image.fromarray(o);result=Image.alpha_composite(grip,base)
    a=np.array(result);a[a[:,:,3]==0,:3]=0;result=Image.fromarray(a);result.save(ROOT/OUT)
    gm.save(ROOT/'work/masks/full_sword_grip_v1.png');remove.save(ROOT/'work/masks/full_sword_remove_skin_v1.png')
    protected=(np.array(orig)[:,:,3]>0)&~rem
    # Original RGB retained even along partially transparent sword edges: replace
    # original covered pixels exactly, avoiding generated metallic redesign.
    a[protected]=np.array(orig)[protected];result=Image.fromarray(a);result.save(ROOT/OUT)
    _,parts=components(a[:,:,3]>32)
    write('reports/full_sword_assembly_v1.json',{'status':'VISUAL_REVIEW_REQUIRED','original':ORIGINAL,'original_sha256':sha(ORIGINAL),'generated_reference':RAW,'generated_reference_sha256':sha(RAW),'generated_reference_mode':'RGB_EMBEDDED_CHECKER_NOT_TRANSPARENT','output':OUT,'output_sha256':sha(OUT),'canvas':list(result.size),'mode':result.mode,'grip_source':'AI generated isolated grip; original visible metallic pixels retained','grip_pixels':int(selected.sum()),'removed_skin_remnant_pixels':removed,'protected_original_changed_pixels':int(np.any(a[protected]!=np.array(orig)[protected],axis=1).sum()),'components_over_32_alpha':sorted([p['area'] for p in parts.values()],reverse=True),'alpha_min':int(a[:,:,3].min()),'alpha_max':int(a[:,:,3].max()),'timestamp':now()})
    items=[]
    for label,color in [('white',(255,255,255)),('gray',(128,128,128))]:
        bg=Image.new('RGBA',result.size,color+(255,));bg.alpha_composite(result)
        items.append((label+' / complete sword',bg.crop((220,780,650,1130)).convert('RGB')))
    sheet(items,'reports/full_sword_review_v1.png',2,(430,350))
    detail=Image.new('RGBA',result.size,'white');detail.alpha_composite(result)
    detail.crop((230,795,430,960)).resize((800,660)).save(ROOT/'reports/full_sword_grip_review_v1.png')

if __name__=='__main__':main()
