"""Offline foot-roll targets for Walk keys, never a runtime rig modifier.

The lower sole profile is measured from the frozen forward shoe, in ankle-local
source pixels. Its support point changes as the heel rises. Integrating rotation
about that point prevents a planted toe from sliding during push-off.
"""
import math
import numpy as np

SOLE = np.array([[-65,104],[-15,120],[32,127],[78,123],[106,116]],float)
STRIDE = 387.0

def smooth(t):
    t=max(0.,min(1.,t))
    return t*t*(3-2*t)

def rotation(deg):
    a=math.radians(deg)
    return np.array([[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]])

def stance_pitch(u):
    if u<.125:return -12*(1-smooth(u/.125))
    return 28*smooth((u-.3125)/.1875)

# Fine integration is only for authoring. Godot plays the existing 49 keys.
U=np.linspace(0,.5,2401)
ROLL=np.zeros(len(U))
for i in range(1,len(U)):
    before=rotation(stance_pitch(U[i-1]));after=rotation(stance_pitch(U[i]))
    mid=rotation(stance_pitch((U[i-1]+U[i])/2))
    contact=SOLE[np.argmax((SOLE@mid.T)[:,1])]
    ROLL[i]=ROLL[i-1]+((before-after)@contact)[0]
ROLL-=np.interp(.25,U,ROLL)

def stance(u,center,ankle_y):
    pitch=stance_pitch(u)
    bottom=(SOLE@rotation(pitch).T)[:,1].max()
    return np.array([center+STRIDE/4-STRIDE*u+np.interp(u,U,ROLL),ankle_y+127-bottom]),pitch

def target(u,center,ankle_y):
    if u<.5:return stance(u,center,ankle_y)
    q=(u-.5)*2
    start,_=stance(.5,center,ankle_y);end,_=stance(0,center,ankle_y)
    s=smooth(q)
    # Tangent matches forward root speed at lift-off and touchdown.
    x=start[0]*(1-s)+end[0]*s-STRIDE/2*(2*q**3-3*q**2+q)
    y=start[1]*(1-s)+end[1]*s-42*math.sin(math.pi*q)
    # Toe stays down briefly after push-off, then clears for the next landing.
    pitch=28-40*smooth((q-.12)/.88)
    return np.array([x,y]),pitch
