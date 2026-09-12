"""Validate exact frozen-metal + generated-grip provenance, never a whole-weapon redraw."""
from rg_common import *

def validate_completion(part, file):
    if part['name']!='sword': raise ValueError('Grip completion is restricted to sword')
    recipe=read(part['completion_recipe'])
    if sha(part['completion_recipe'])!=part['completion_recipe_sha256']: raise ValueError('Sword recipe changed')
    for key in ['original','generated_reference','grip_mask','remove_mask']:
        if sha(recipe[key])!=recipe[key+'_sha256']: raise ValueError('Sword input changed: '+key)
    if sha(file)!=recipe['output_sha256']: raise ValueError('Completed sword output changed')
    original=np.array(rgba(recipe['original'])); raw=np.array(Image.open(ROOT/recipe['generated_reference']).convert('RGB'))
    grip=np.array(mask(recipe['grip_mask'])); remove=np.array(mask(recipe['remove_mask']))>0
    base=original.copy();base[remove]=0
    expected=np.array(Image.alpha_composite(Image.fromarray(np.dstack([raw,grip])),Image.fromarray(base)))
    protected=(original[:,:,3]>0)&~remove;expected[protected]=original[protected];expected[expected[:,:,3]==0,:3]=0
    if not np.array_equal(expected,np.array(rgba(file))): raise ValueError('Sword is not exact recorded local completion')
    if recipe.get('protected_original_changed_pixels')!=0: raise ValueError('Sword original visible pixels changed')
    return True
