"""Offline overlap demonstration through the installed alpha smoke shader."""
from pathlib import Path
import json,sys
W=Path(__file__).resolve().parent
exec(compile((W/'test_gpu.py').read_text(),str(W/'test_gpu.py'),'exec'),globals())
defaults();setv('g_fog_lerp',0);setv('g_readable_depth',0);setv('g_use_spherical_harmonics',0)
setv('sun_colour',0,0,0);setv('g_ambient_fudge_factor',0)
for name in ['ambient_cube_lr','ambient_cube_tb','ambient_cube_fb']:setv(name,0,0,0,0,0,0,0)
for slot,obj in cbuffers.items():upload(obj,bytes(data[slot]))
ctx('OMSetBlendState',(P,alpha_blend),(P,None),(U,0xffffffff))
brightness={'A':.15,'B':.35,'C':.85}
def render_order(order):
 ctx('ClearRenderTargetView',(P,rtv),(C.POINTER(C.c_float),(C.c_float*4)(0,0,0,0)))
 ctx('PSSetShader',(P,old),(P,None),(U,0))
 for name in order:
  v=brightness[name]
  upload(vcb,struct.pack('<16f',0,10,120,-1, .5,.37,.4,1, v,v,v,.65, 0,0,.2,0))
  ctx('Draw',(U,3),(U,0))
 ctx('CopyResource',(P,rb),(P,rt));mapped=Map()
 checked(ctx('Map',(P,rb),(U,0),(U,1),(U,0),(C.POINTER(Map),C.byref(mapped))))
 pixels=b''.join(C.string_at(mapped.data+y*mapped.pitch,N*16) for y in range(N))
 ctx('Unmap',(P,rb),(U,0));return struct.unpack('<'+str(N*N*4)+'f',pixels)
a=render_order(['B','A','C']);c=render_order(['C','B','A'])
assert all(math.isfinite(x) for x in a+c)
colour_error=max(abs(a[i]-c[i]) for i in range(len(a)) if i%4!=3)
alpha_error=max(abs(x-y) for x,y in zip(a[3::4],c[3::4]))
assert colour_error>.01 and alpha_error==0
out=dict(status='PASS',device='HARDWARE' if hardware else 'WARP',actualInstalledAlphaSmokeShader=True,lightingConstantsIdentical=True,onlyDrawOrderChanges=True,maxRGBJump=colour_error,maxAlphaDifference=alpha_error,firstOrder=['B','A','C'],secondOrder=['C','B','A'],scope='Offline overlapping triangles rendered with installed PS and source-alpha blending. Demonstrates mechanism, not live flashing identification.')
(W/('overlap-gpu-hardware.json' if hardware else 'overlap-gpu.json')).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
