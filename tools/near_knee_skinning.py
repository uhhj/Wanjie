"""Source-derived triangular skinning; stationary knee socket / rotating shin.

This changes the articulation transform, never the texture or ownership mask.
The same vertices, triangles and two-bone weights are exported for native Godot.
"""
import math
from rg_common import *

def build_mesh(im,pivot,plate_polygon):
    x0,y0,x1,y1=im.getchannel('A').getbbox()
    # Regular topology with a narrow, plate-adjacent stationary zone.
    xs=list(range(x0-2,x1+10,8));ys=list(range(y0-2,y1+10,8))
    vertices=np.array([(x,y) for y in ys for x in xs],float)
    # Blend the greave immediately below the plate, not the ankle or foot.
    polygon=np.array(plate_polygon,float);distance=np.full(len(vertices),999.)
    for a,b in zip(polygon,np.roll(polygon,-1,axis=0)):
        ab=b-a;t=np.clip(((vertices-a)*ab).sum(axis=1)/(ab*ab).sum(),0,1)
        distance=np.minimum(distance,np.linalg.norm(vertices-a-t[:,None]*ab,axis=1))
    t=np.clip(distance/32,0,1)
    weights=t*t*(3-2*t)
    triangles=[];nx=len(xs)
    for j in range(len(ys)-1):
        for i in range(nx-1):
            a=j*nx+i;triangles.extend([[a,a+1,a+nx],[a+1,a+nx+1,a+nx]])
    return {'vertices':vertices.tolist(),'triangles':triangles,'shin_weights':weights.tolist(),
            'stationary_socket_weights':(1-weights).tolist(),'pivot':list(pivot),
            'texture_canvas':list(im.size),'coordinate_space':'source canvas pixels',
            'bones':['near_knee_socket','leg_near_shin'],'no_texture_or_mask_expansion':True}

def vertices_at(mesh,angle):
    v=np.array(mesh['vertices']);p=np.array(mesh['pivot']);r=math.radians(angle)
    rotation=np.array([[math.cos(r),math.sin(r)],[-math.sin(r),math.cos(r)]])
    rotated=(v-p)@rotation.T+p
    return v+(rotated-v)*np.array(mesh['shin_weights'])[:,None]

def deform(im,mesh,angle):
    if angle==0:return im.copy()
    src=np.array(im,dtype=float);src[:,:,:3]*=src[:,:,3:4]/255
    out=np.zeros_like(src);original=np.array(mesh['vertices']);dest=vertices_at(mesh,angle)
    h,w=src.shape[:2]
    for ids in mesh['triangles']:
        s=original[ids];d=dest[ids]
        x0=max(0,int(np.floor(d[:,0].min())));x1=min(w,int(np.ceil(d[:,0].max()))+1)
        y0=max(0,int(np.floor(d[:,1].min())));y1=min(h,int(np.ceil(d[:,1].max()))+1)
        if x1<=x0 or y1<=y0:continue
        yy,xx=np.mgrid[y0:y1,x0:x1];matrix=np.column_stack((d[1]-d[0],d[2]-d[0]))
        uv=(np.stack((xx,yy),axis=-1)-d[0])@np.linalg.inv(matrix).T
        inside=(uv[:,:,0]>=-1e-8)&(uv[:,:,1]>=-1e-8)&(uv.sum(axis=2)<=1+1e-8)
        coords=s[0]+uv[:,:,0,None]*(s[1]-s[0])+uv[:,:,1,None]*(s[2]-s[0])
        sx=np.clip(coords[:,:,0],0,w-1);sy=np.clip(coords[:,:,1],0,h-1)
        ix=sx.astype(int);iy=sy.astype(int);fx=(sx-ix)[:,:,None];fy=(sy-iy)[:,:,None]
        ix1=np.minimum(ix+1,w-1);iy1=np.minimum(iy+1,h-1)
        sampled=(src[iy,ix]*(1-fx)+src[iy,ix1]*fx)*(1-fy)+(src[iy1,ix]*(1-fx)+src[iy1,ix1]*fx)*fy
        out[y0:y1,x0:x1][inside]=sampled[inside]
    alpha=out[:,:,3:4];out[:,:,:3]=np.divide(out[:,:,:3]*255,alpha,out=np.zeros_like(out[:,:,:3]),where=alpha>0)
    return Image.fromarray(np.rint(np.clip(out,0,255)).astype(np.uint8))
