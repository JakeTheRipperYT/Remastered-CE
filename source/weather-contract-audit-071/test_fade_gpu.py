"""Execute fade shader math on D3D11 WARP, with actual cubemap sampling.
The sky function is taken from the staged source. SampleLevel(0) replaces Sample
only for compute-stage legality; the test cubemaps have one mip and constant faces.
"""
from pathlib import Path
import ctypes as C,re,json,struct
W=Path(__file__).resolve().parent
U=C.c_uint;P=C.c_void_p;H=C.c_long
header=sorted(Path('C:/Program Files (x86)/Windows Kits/10/Include').glob('*/um/d3d11.h'))[-1].read_text()
def methods(name):
 text=header.split('typedef struct '+name+'Vtbl')[1].split('} '+name+'Vtbl')[0]
 return {n:i for i,n in enumerate(re.findall(r'STDMETHODCALLTYPE\s*\*(\w+)\s*\)',text))}
deviceMethods=methods('ID3D11Device');contextMethods=methods('ID3D11DeviceContext')
def method(obj,index,result,*args):return C.WINFUNCTYPE(result,P,*args)(C.cast(obj,C.POINTER(C.POINTER(P))).contents[index])
def checked(result):
 if result<0:raise RuntimeError(hex(result&0xffffffff))
def call(obj,table,name,*typed):
 types=[t for t,v in typed];values=[v for t,v in typed]
 return method(obj,table[name],H,*types)(obj,*values)
class Buffer(C.Structure):_fields_=[(n,U) for n in ['ByteWidth','Usage','BindFlags','CPUAccessFlags','MiscFlags','StructureByteStride']]
class Texture(C.Structure):_fields_=[(n,U) for n in ['Width','Height','MipLevels','ArraySize','Format','SampleCount','SampleQuality','Usage','BindFlags','CPUAccessFlags','MiscFlags']]
class Initial(C.Structure):_fields_=[('data',P),('pitch',U),('slice',U)]
class Map(C.Structure):_fields_=[('data',P),('pitch',U),('slice',U)]
class Sampler(C.Structure):_fields_=[('Filter',U),('AddressU',U),('AddressV',U),('AddressW',U),('MipLODBias',C.c_float),('MaxAnisotropy',U),('ComparisonFunc',U),('BorderColor',C.c_float*4),('MinLOD',C.c_float),('MaxLOD',C.c_float)]
source=(W/'stage/fx/sky.hlsl').read_text();start=source.index('float3 get_sky_colour(');brace=source.index('{',start);level=1;end=brace+1
while level:
 if source[end]=='{':level+=1
 elif source[end]=='}':level-=1
 end+=1
sky=source[start:end].replace('.Sample( s_sky, transformed_direction )','.SampleLevel( s_sky, transformed_direction,0 )').replace('.Sample(s_sky,transformed_direction)','.SampleLevel(s_sky,transformed_direction,0)')
compute='''#include "weather_transition.hlsl"
TextureCube t_sky:register(t0); TextureCube t_rce_weather_previous_sky:register(t1);
SamplerState s_sky:register(s0);
static const float3 g_sun_direction=float3(1,0,0);
static const float4 g_sky_exposure_clamp_threshold_falloff=float4(1,1000,1000,1);
static const float4 g_sky_gamma_etc=float4(1,0,0,1);
'''+sky+'''
RWStructuredBuffer<float4> output:register(u0);
[numthreads(1,1,1)]void test(uint3 id:SV_DispatchThreadID) {
 output[0]=float4(get_sky_colour(float3(.5,.5,.5)),1);
 output[1]=float4(rce_weather_managed()?rce_puddle_mix(.8,.8,1):1,rce_weather_snow(),rce_puddle_material(float3(.6,.1,.15)).x,1);
 bool cullEnabled=rce_weather_managed()?g_rce_weather_new_range.w>0.0f:true;
 float cullThreshold=rce_weather_managed()?g_rce_weather_new_range.w:1.0f;
 output[2]=float4(rce_puddle_mix(.72,.72,1),rce_puddle_mix(.98,.98,1),cullEnabled && rce_puddle_mix(.98,.98,1,true)>=cullThreshold?1:0,0);
 float visible=0;
 for(uint k=0;k<512;k++)visible+=rce_precipitation_visibility(float4(k*.0137,k*.0371,0,0));
 output[3]=float4(visible/512,0,0,0);
}
'''
shaderFile=W/'shader-compile/fx/fade_gpu_test.hlsl';shaderFile.write_text(compute)
helper=Path('F:/Codex/Shogun2-CE/work/compile_sss_edge_fix.py').read_text();scope={'C':C}
exec(helper[helper.index('dll=C.WinDLL'):helper.index('def compile_shader')],scope)
Macro=scope['Macro'];code=P();errors=P();macros=(Macro*1)(Macro(None,None))
hr=scope['compilefn'](str(shaderFile),macros,P(1),b'test',b'cs_5_0',4096,0,C.byref(code),C.byref(errors))
message=scope['take'](errors).decode(errors='replace');assert hr>=0,message;bytecode=scope['take'](code)
device=P();context=P();feature=U();d3d=C.WinDLL('d3d11.dll');create=d3d.D3D11CreateDevice;create.restype=H
create.argtypes=[P,U,P,U,P,U,U,C.POINTER(P),C.POINTER(U),C.POINTER(P)]
checked(create(None,5,None,0,None,0,7,C.byref(device),C.byref(feature),C.byref(context)))
def buffer(desc):
 out=P();checked(call(device,deviceMethods,'CreateBuffer',(C.POINTER(Buffer),C.byref(desc)),(P,None),(C.POINTER(P),C.byref(out))));return out
constant=buffer(Buffer(112,0,4,0,0,0));output=buffer(Buffer(64,0,0x80,0,0x40,16));readback=buffer(Buffer(64,3,0,0x20000,0,0))
program=P();blob=C.create_string_buffer(bytecode)
checked(call(device,deviceMethods,'CreateComputeShader',(P,C.cast(blob,P)),(C.c_size_t,len(bytecode)),(P,None),(C.POINTER(P),C.byref(program))))
uav=P();uavDesc=(U*6)(0,1,0,4,0,0)
checked(call(device,deviceMethods,'CreateUnorderedAccessView',(P,output),(P,C.cast(uavDesc,P)),(C.POINTER(P),C.byref(uav))))
resources=[];textures=[]
for colour in [(0,0,1,1),(1,0,0,1)]:
 pixel=(C.c_float*4)(*colour);initial=(Initial*6)(*[Initial(C.cast(pixel,P),16,16) for _ in range(6)])
 texture=P();description=Texture(1,1,1,6,2,1,0,1,8,0,4)
 checked(call(device,deviceMethods,'CreateTexture2D',(C.POINTER(Texture),C.byref(description)),(C.POINTER(Initial),initial),(C.POINTER(P),C.byref(texture))))
 resource=P();checked(call(device,deviceMethods,'CreateShaderResourceView',(P,texture),(P,None),(C.POINTER(P),C.byref(resource))))
 resources.append(resource);textures.append(texture)
sampler=P();samplerDesc=Sampler(0x15,3,3,3,0,1,1,(C.c_float*4)(0,0,0,0),0,3.4e38)
checked(call(device,deviceMethods,'CreateSamplerState',(C.POINTER(Sampler),C.byref(samplerDesc)),(C.POINTER(P),C.byref(sampler))))
def ctx(name,*typed):call(context,contextMethods,name,*typed)
ctx('CSSetShader',(P,program),(P,None),(U,0))
ctx('CSSetConstantBuffers',(U,0),(U,1),(C.POINTER(P),(P*1)(constant)))
ctx('CSSetUnorderedAccessViews',(U,0),(U,1),(C.POINTER(P),(P*1)(uav)),(P,None))
ctx('CSSetShaderResources',(U,0),(U,2),(C.POINTER(P),(P*2)(*resources)))
ctx('CSSetSamplers',(U,0),(U,1),(C.POINTER(P),(P*1)(sampler)))
rows=[]
for reverse in [False,True]:
 previous=None
 for step in range(33):
  p=step/32;oldWet=1 if reverse else 0;newWet=oldWet;wet=oldWet;coverage=1-p if reverse else p
  data=(C.c_float*28)(1,wet,p,p, 1,.7,.05,0, 1,.7,.05,0, ( .6 if oldWet else 1),.1,.15,oldWet, (.6 if newWet else 1),.1,.15,newWet, 128,1024,.1,coverage, 128,1024,.1,oldWet)
  ctx('UpdateSubresource',(P,constant),(U,0),(P,None),(P,C.cast(data,P)),(U,0),(U,0))
  ctx('Dispatch',(U,1),(U,1),(U,1));ctx('CopyResource',(P,readback),(P,output))
  mapped=Map();checked(call(context,contextMethods,'Map',(P,readback),(U,0),(U,1),(U,0),(C.POINTER(Map),C.byref(mapped))))
  values=struct.unpack('<16f',C.string_at(mapped.data,64));ctx('Unmap',(P,readback),(U,0))
  expected=(1-p,0,p,1,p,1-.4*wet,1)
  selected=values[:4]+values[5:8]
  assert all(abs(a-b)<.0001 for a,b in zip(selected,expected)),(reverse,p,values,expected)
  assert all(__import__('math').isfinite(x) for x in values)
  assert values[8]<=values[9]+.00001,(p,values)
  if previous:
   sign=-1 if reverse else 1
   assert all(abs(values[k]-previous[k])<.0001 for k in (4,8,9)),(reverse,p,values,previous)
   assert sign*(values[12]-previous[12])>=-.0001
   assert max(abs(values[k]-previous[k]) for k in (4,8,9,12))<.45
  if step==0:assert abs(values[12]-oldWet)<.0001
  if step==32:assert abs(values[12]-(1-oldWet))<.0001
  assert abs(values[4]-wet)<.0001
  assert values[10]==oldWet, "Grass culling changed with incoming rain"
  previous=values;rows.append(dict(reverse=reverse,progress=p,sky=list(values[:3]),puddle=values[4],snow=values[5],roughness=values[6],edge=values[8],centre=values[9],precipitationCoverage=values[12]))
 # After the fade ends, mode2 must retain the same ground without requesting
 # sky/sun blending or changing the native steady rain opacity.
 data[0]=2
 ctx('UpdateSubresource',(P,constant),(U,0),(P,None),(P,C.cast(data,P)),(U,0),(U,0))
 ctx('Dispatch',(U,1),(U,1),(U,1));ctx('CopyResource',(P,readback),(P,output))
 mapped=Map();checked(call(context,contextMethods,'Map',(P,readback),(U,0),(U,1),(U,0),(C.POINTER(Map),C.byref(mapped))))
 held=struct.unpack('<16f',C.string_at(mapped.data,64));ctx('Unmap',(P,readback),(U,0))
 assert abs(held[4]-wet)<.0001 and abs(held[6]-(1-.4*wet))<.0001 and held[10]==oldWet
 assert held[:4]==(0,0,1,1) and abs(held[12]-coverage)<.0001,held

data=(C.c_float*28)();ctx('UpdateSubresource',(P,constant),(U,0),(P,None),(P,C.cast(data,P)),(U,0),(U,0))
ctx('Dispatch',(U,1),(U,1),(U,1));ctx('CopyResource',(P,readback),(P,output))
mapped=Map();checked(call(context,contextMethods,'Map',(P,readback),(U,0),(U,1),(U,0),(C.POINTER(Map),C.byref(mapped))))
disabled=struct.unpack('<16f',C.string_at(mapped.data,64));ctx('Unmap',(P,readback),(U,0))
assert all(abs(a-b)<.0001 for a,b in zip(disabled,(0,0,1,1,1,1,.6,1))),disabled
report=dict(status='PASS_D3D11_WARP',deviceFeatureLevel=hex(feature.value),samples=len(rows),actualCubemapSampling=True,actualStagedSkyFunction=True,initialPuddleCoverageAndMaterialsPermanent=True,steadyModeKeepsIncomingRainStrengthAndNativeSky=True,grassCullingStaysAtOpeningPolicy=True,stableParticleDensityTapersToZero=True,snowAndRoughnessContinuous=True,disabledNativeRenderingPreserved=True,results=rows)
(W/'fade-gpu-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='results'},indent=2))
