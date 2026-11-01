"""Execute actual grass GBuffer DXBC across starting/current weather combinations."""
from pathlib import Path
import sys,json,struct,ctypes as C,re,math,itertools
W=Path(__file__).parent
sys.path.insert(0,r'F:/Codex/Remastered-CE-Port/work/particle-camera-stability');import build_candidate as b
prefix=Path(r'F:/Codex/Remastered-CE-Port/work/particle-camera-stability/test_camera_gpu.py').read_text().split('\ndef texture(')[0]
prefix=prefix.replace('import build_candidate as b','import build_candidate as b')
exec(compile(prefix,str(W/'d3d_fixture.py'),'exec'),globals())
N=4
vs='''struct O {float4 p:SV_Position;float4 c:COLOR0;float4 w:TEXCOORD0;float2 uv:TEXCOORD1;float3 n:TEXCOORD2;float4 clip:TEXCOORD3;float3 face:TEXCOORD4;float4 cd:TEXCOORD5;float4 prev:TEXCOORD6;};
O main(uint id:SV_VertexID){O o;float2 uv=float2((id<<1)&2,id&2);o.p=float4(uv*float2(2,-2)+float2(-1,1),.5,1);o.c=float4(.6,.7,.2,1);o.w=float4(0,0,0,1);o.uv=float2(.5,.5);o.n=float3(0,1,0);o.clip=o.p;o.face=o.n;o.cd=float4(0,0,1,0);o.prev=float4(0,0,0,1);return o;}'''
file=W/'gpu_test_vs.hlsl';file.write_text(vs);code=P();errors=P();macros=(b.Macro*1)(b.Macro(None,None));hr=b.compilefn(str(file),macros,P(1),b'main',b'vs_5_0',4096,0,C.byref(code),C.byref(errors));assert hr>=0,b.take(errors);vertex=shader(b.take(code),'Vertex')
ctx('VSSetShader',(P,vertex),(P,None),(U,0));ctx('IASetPrimitiveTopology',(U,4))
# Disable culling; all output textures are floating point.
raster=P();desc=struct.pack('<6I3fI',3,1,0,0,0,0,0,0,0,0);blob=C.create_string_buffer(desc)
dev('CreateRasterizerState',(P,C.cast(blob,P)),(C.POINTER(P),C.byref(raster)));ctx('RSSetState',(P,raster));vp=Viewport(0,0,N,N,0,1);ctx('RSSetViewports',(U,1),(C.POINTER(Viewport),C.byref(vp)))
targets=[];views=[];readbacks=[]
for i in range(5):
 t=P();d=Texture(N,N,1,1,2,1,0,0,32,0,0);dev('CreateTexture2D',(C.POINTER(Texture),C.byref(d)),(P,None),(C.POINTER(P),C.byref(t)));view=P();dev('CreateRenderTargetView',(P,t),(P,None),(C.POINTER(P),C.byref(view)))
 rb=P();d=Texture(N,N,1,1,2,1,0,3,0,0x20000,0);dev('CreateTexture2D',(C.POINTER(Texture),C.byref(d)),(P,None),(C.POINTER(P),C.byref(rb)));targets.append(t);views.append(view);readbacks.append(rb)
ctx('OMSetRenderTargets',(U,5),(C.POINTER(P),(P*5)(*views)),(P,None))
def solid(colour,size=1):
 values=(C.c_float*(size*size*4))(*(list(colour)*(size*size)));init=Initial(C.cast(values,P),size*16,size*size*16);t=P();d=Texture(size,size,1,1,2,1,0,0,8,0,0);dev('CreateTexture2D',(C.POINTER(Texture),C.byref(d)),(C.POINTER(Initial),C.byref(init)),(C.POINTER(P),C.byref(t)));view=P();dev('CreateShaderResourceView',(P,t),(P,None),(C.POINTER(P),C.byref(view)));return t,view
tex=[solid((.15,.4,.1,1)),solid((.3,.4,0,.8)),solid((1,1,1,1),64)]
ctx('PSSetShaderResources',(U,0),(U,3),(C.POINTER(P),(P*3)(*[v for t,v in tex])))
sampler=P();d=Sampler(0x15,3,3,3,0,1,1,(C.c_float*4)(0,0,0,0),0,3.4e38);dev('CreateSamplerState',(C.POINTER(Sampler),C.byref(d)),(C.POINTER(P),C.byref(sampler)));ctx('PSSetSamplers',(U,0),(U,3),(C.POINTER(P),(P*3)(sampler,sampler,sampler)))
cb={name:buffer(n,4) for name,n in [('camera_VS_PS',704),('rigid_config_PS',48),('grass_PS',48),('rce_weather_shared',112)]}
camera=bytearray(704)
for i in range(4):struct.pack_into('<f',camera,224+(i*4+i)*4,1)
struct.pack_into('<4f',camera,608,N,N,1/N,1/N);upload(cb['camera_VS_PS'],bytes(camera));upload(cb['grass_PS'],struct.pack('<12f',.01,*([0]*11)))
def run(path,managed,opening,wetmult):
 raw=path.read_bytes();dx=raw[raw.index(b'DXBC'):];ps=shader(dx,'Pixel');asm=b.assembly(dx)
 slots={n:int(i) for n,i in re.findall(r'//\s+(\w+)\s+cbuffer\s+NA\s+NA\s+cb(\d+)\s+1',asm)}
 for name,slot in slots.items():ctx('PSSetConstantBuffers',(U,slot),(U,1),(C.POINTER(P),(P*1)(cb[name])))
 values=[0.0]*12;values[8]=wetmult;upload(cb['rigid_config_PS'],struct.pack('<12f',*values))
 values=[0.0]*28;values[0]=managed;values[15]=opening;upload(cb['rce_weather_shared'],struct.pack('<28f',*values))
 ctx('PSSetShader',(P,ps),(P,None),(U,0))
 for v in views:ctx('ClearRenderTargetView',(P,v),(C.POINTER(C.c_float),(C.c_float*4)(-7,-7,-7,-7)))
 ctx('Draw',(U,3),(U,0));result=[]
 for t,rb in zip(targets,readbacks):
  ctx('CopyResource',(P,rb),(P,t));m=Map();checked(ctx('Map',(P,rb),(U,0),(U,1),(U,0),(C.POINTER(Map),C.byref(m))));result.append(struct.unpack('<4f',C.string_at(m.data,16)));ctx('Unmap',(P,rb),(U,0))
 method(ps,2,U)(ps);assert all(math.isfinite(x) for row in result for x in row);assert result[2][1]>=0,('No pixels rendered',result)
 return result
rows=[]
for managed,opening,mult in itertools.product([0,1,2],[0,1],[.25,.5,1.0]):
 pair=[]
 for wet in [False,True]:
  name='fxc/dx11_sm_5_0_default_rigidgrass'+('wet' if wet else '')+'.hlsl_ps_ps30_gbuffer.fxc'
  result=run(W/'replacements'/name,managed,opening,mult);expected=.9*(mult if (opening if managed else wet) else 1)
  assert abs(result[2][1]-expected)<1e-5,(managed,opening,mult,wet,result[2],expected)
  assert abs(result[2][0])<1e-6
  pair.append(result)
 if managed:assert pair[0]==pair[1],('Current weather changed opening ground material',managed,opening,mult)
 rows.append(dict(managed=managed,openingWet=opening,multiplier=mult,currentWetAndDryMatch=bool(managed),roughness=[r[2][1] for r in pair]))
report=dict(status='PASS_D3D11_HARDWARE' if hardware else 'PASS_D3D11_WARP',actualCompiledGrassGBufferShaders=True,draws=len(rows)*2,startingWetSurvivesCurrentClear=True,startingClearIgnoresCurrentRain=True,allFiveGBufferOutputsMatchAcrossIncomingPermutation=True,nonCampaignFallbackRetained=True,results=rows)
(W/('gpu-validation-hardware.json' if hardware else 'gpu-validation.json')).write_text(json.dumps(report,indent=2));print(report['status'],report['draws'],'actual grass shader draws')
