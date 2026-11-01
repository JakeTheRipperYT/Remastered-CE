"""Render original and candidate DXBC through D3D11 WARP and compare float pixels."""
from pathlib import Path
import ctypes as C,json,struct,re,math,itertools,sys
W=Path(sys.argv[sys.argv.index('--work')+1]) if '--work' in sys.argv else Path(__file__).resolve().parent
sys.path.insert(0,str(W))
import build_candidate as b
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
class Viewport(C.Structure):_fields_=[(n,C.c_float) for n in ['x','y','width','height','mindepth','maxdepth']]
class Texture3D(C.Structure):_fields_=[(n,U) for n in ['Width','Height','Depth','MipLevels','Format','Usage','BindFlags','CPUAccessFlags','MiscFlags']]
device=P();context=P();feature=U();create=C.WinDLL('d3d11.dll').D3D11CreateDevice;create.restype=H
create.argtypes=[P,U,P,U,P,U,U,C.POINTER(P),C.POINTER(U),C.POINTER(P)]
hardware='--hardware' in sys.argv
checked(create(None,1 if hardware else 5,None,0,None,0,7,C.byref(device),C.byref(feature),C.byref(context)))
def dev(name,*args):checked(call(device,deviceMethods,name,*args))
def ctx(name,*args):return call(context,contextMethods,name,*args)
def buffer(size,bind):
    out=P();d=Buffer(size,0,bind,0,0,0);dev('CreateBuffer',(C.POINTER(Buffer),C.byref(d)),(P,None),(C.POINTER(P),C.byref(out)));return out
def upload(obj,data):
    blob=C.create_string_buffer(data);ctx('UpdateSubresource',(P,obj),(U,0),(P,None),(P,C.cast(blob,P)),(U,0),(U,0))
def shader(code,stage):
    out=P();blob=C.create_string_buffer(code);dev('Create'+stage+'Shader',(P,C.cast(blob,P)),(C.c_size_t,len(code)),(P,None),(C.POINTER(P),C.byref(out)));return out
def texture(size=16,kind='colour',is3d=False,mips=1):
    initial=[];blobs=[]
    for mip in range(mips):
        width=max(1,size>>mip);depth=width if is3d else 1;values=[]
        for z in range(depth):
            for y in range(width):
                for x in range(width):
                    t=((x*17+y*29+z*11)%31)/30
                    if kind=='normal':v=(.45+.1*t,.7,.5,.48+.04*t)
                    elif kind in ('sh','prevsh'):
                        shift=.06 if kind=='prevsh' else 0
                        v=(.15+.02*t+shift,.18+.03*t+shift,.2+.04*t+shift,1)
                    elif kind=='depth':v=(.5,.5,.5,.5)
                    elif kind=='noise':v=(t,t,t,t)
                    else:v=(.3+.1*t,.25+.1*t,.2+.1*t,.8+.1*t)
                    values.extend(v)
        blob=(C.c_float*len(values))(*values);blobs.append(blob);initial.append(Initial(C.cast(blob,P),width*16,width*width*16))
    tex=P();ini=(Initial*mips)(*initial)
    if is3d:
        d=Texture3D(size,size,size,mips,2,1,8,0,0);dev('CreateTexture3D',(C.POINTER(Texture3D),C.byref(d)),(C.POINTER(Initial),ini),(C.POINTER(P),C.byref(tex)))
    else:
        d=Texture(size,size,mips,1,2,1,0,1,8,0,0);dev('CreateTexture2D',(C.POINTER(Texture),C.byref(d)),(C.POINTER(Initial),ini),(C.POINTER(P),C.byref(tex)))
    srv=P();dev('CreateShaderResourceView',(P,tex),(P,None),(C.POINTER(P),C.byref(srv)));return tex,srv

vsource='''cbuffer test_params:register(b0){float4 world;float4 params;float4 colour;float4 uv_params;};
struct O{float4 p:SV_Position;float4 c:COLOR0;float4 uv0:TEXCOORD0;float4 uv1:TEXCOORD1;float4 pv:TEXCOORD3;float4 sl:TEXCOORD4;float4 wp:TEXCOORD5;};
O main(uint id:SV_VertexID){float2 v=float2((id<<1)&2,id&2);O o;
o.p=float4(v*float2(2,-2)+float2(-1,1),0,1);o.c=colour;
float2 uv=v*uv_params.z; o.uv0=float4(uv,uv);o.uv1=float4(uv+.137,uv+uv_params.xy);
o.pv=float4(0,0,params.x,params.y);o.sl=float4(1,params.z,params.w,world.w);
o.wp=float4(world.xyz+float3(v.x*7,v.y*2,v.y*9),1);return o;}
'''
vp=W/'candidate-source/fx/gpu_test_vertex.hlsl';vp.write_text(vsource);b.FX=vp.parent
vs=b.compile_shader(vp.name,'main','vs',4096)[0];vshader=shader(vs,'Vertex');vcb=buffer(64,4)
ctx('VSSetShader',(P,vshader),(P,None),(U,0));ctx('VSSetConstantBuffers',(U,0),(U,1),(C.POINTER(P),(P*1)(vcb)))
ctx('IASetPrimitiveTopology',(U,4))
N=24;rt=P();rb=P();rtd=Texture(N,N,1,1,2,1,0,0,0x20,0,0);rbd=Texture(N,N,1,1,2,1,0,3,0,0x20000,0)
dev('CreateTexture2D',(C.POINTER(Texture),C.byref(rtd)),(P,None),(C.POINTER(P),C.byref(rt)))
dev('CreateTexture2D',(C.POINTER(Texture),C.byref(rbd)),(P,None),(C.POINTER(P),C.byref(rb)))
rtv=P();dev('CreateRenderTargetView',(P,rt),(P,None),(C.POINTER(P),C.byref(rtv)))
ctx('OMSetRenderTargets',(U,1),(C.POINTER(P),(P*1)(rtv)),(P,None))
view=Viewport(0,0,N,N,0,1);ctx('RSSetViewports',(U,1),(C.POINTER(Viewport),C.byref(view)))
sampler=P();sd=Sampler(0x15,3,3,3,0,1,1,(C.c_float*4)(0,0,0,0),0,3.4e38)
dev('CreateSamplerState',(C.POINTER(Sampler),C.byref(sd)),(C.POINTER(P),C.byref(sampler)))
ctx('PSSetSamplers',(U,0),(U,8),(C.POINTER(P),(P*8)(*[sampler]*8)))
textures={k:texture(size=s,kind=k,is3d=d,mips=m) for k,s,d,m in [('colour',32,False,6),('normal',32,False,6),('sh',9,False,1),('prevsh',9,False,1),('noise',4,False,1)]}
volume=texture(4,'noise',True);depth=texture(32,'depth')
def readpixels(program):
    ctx('ClearRenderTargetView',(P,rtv),(C.POINTER(C.c_float),(C.c_float*4)(-9,-9,-9,-9)))
    ctx('PSSetShader',(P,program),(P,None),(U,0));ctx('Draw',(U,3),(U,0));ctx('CopyResource',(P,rb),(P,rt))
    mapped=Map();checked(ctx('Map',(P,rb),(U,0),(U,1),(U,0),(C.POINTER(Map),C.byref(mapped))))
    out=b''.join(C.string_at(mapped.data+y*mapped.pitch,N*16) for y in range(N));ctx('Unmap',(P,rb),(U,0));return struct.unpack('<'+str(N*N*4)+'f',out)

entries,_=b.readpack(b.TARGET.read_bytes());report=json.loads((W/'candidate-validation.json').read_text());results=[]
if b.OVERLAY:entries.update(b.read_overlay(b.OVERLAY))
for variant in report['variants']:
    name=variant['path'];before=entries[name]['data'];after=(W/'replacements'/name).read_bytes()
    old=shader(before[before.index(b'DXBC'):],'Pixel');new=shader(after[after.index(b'DXBC'):],'Pixel')
    asm=b.assembly(before[before.index(b'DXBC'):]);members={};active=None
    bindings={name:(kind,int(slot)) for name,kind,slot in re.findall(r'^// (\w+)\s+(cbuffer|texture|sampler)\s+.*?\s+(?:cb|t|s)(\d+)\s+1\s*$',asm,re.M)}
    for line in asm.splitlines():
        m=re.match(r'// cbuffer (\w+)',line)
        if m:active=m[1]
        m=re.search(r'//\s+(\w+)\s+(\w+)(?:\[\d+\])?;.*?Offset:\s*(\d+) Size:\s*(\d+)',line)
        if m and active:members[m[2]]=(active,int(m[3]),int(m[4]),m[1])
    sizes={int(i):int(n)*16 for i,n in re.findall(r'dcl_constantbuffer CB(\d+)\[(\d+)\]',asm)}
    cbuffers={i:buffer(n,4) for i,n in sizes.items()};data={i:bytearray(n) for i,n in sizes.items()}
    def setv(name,*values):
        if name not in members:return
        cb,off,size,kind=members[name];slot=bindings[cb][1];fmt='I' if kind in ('bool','uint','int') else 'f'
        assert len(values)*4<=size,(name,size)
        struct.pack_into('<'+str(len(values))+fmt,data[slot],off,*values)
    def defaults():
        for x in data.values():x[:]=b'\0'*len(x)
        base={'camera_position':(0,25,0),'inv_projection':(1,0,0,0,0,1,0,0,0,0,1,0,0,0,1,0),'screen_size':(N,N,1/N,1/N),'g_render_target_dimensions':(N,N,1/N,1/N),'g_probe_grid_area':(-100,-100,100,100),'g_probe_grid_size':(3,),'g_specular_probe_lerp':(.5,),'g_spherical_harmonic_terms':(9,),'g_campaign_world_bounds':(-100,-100,100,100),'sun_direction':(.2,.9,.3),'sun_colour':(.8,.7,.6),'ambient_cube_lr':(.2,.25,.3,0,.2,.25,.3),'ambient_cube_tb':(.25,.3,.35,0,.2,.25,.3),'ambient_cube_fb':(.2,.25,.3,0,.2,.25,.3),'g_use_spherical_harmonics':(1,),'g_ambient_fudge_factor':(1,),'g_fog_density_constant':(.03,),'g_fog_density_height':(.05,),'g_fog_height_bottom':(0,),'g_fog_height_top':(100,),'g_fog_density_mie':(.2,),'g_fog_noise':(.4,),'g_fog_colour':(.4,.5,.6),'g_fog_lerp':(1,),'g_fog_y_multiplier':(1,),'g_campaign_density_scaling':(1,),'g_clear_distance_fade_out':(10,),'g_force_fog':(100000,200000),'g_camera_aligned_x_axis_PS':(1,0,0),'g_camera_aligned_y_axis_PS':(0,1,0),'g_camera_aligned_z_axis_PS':(0,0,1),'g_shroud_alpha_min_value':(1,),'g_soft_edge_factor':(1,),'g_distortion_divider':(1,)}
        for key,value in base.items():setv(key,*value)
    srvs=[P() for _ in range(16)]
    for resource,(kind,slot) in bindings.items():
        if kind!='texture':continue
        item=volume if resource=='t_volume_noise' else depth if resource=='gbuffer_readable_depth_texture' else textures['normal' if resource=='s_normalmap_texture' else 'prevsh' if resource=='t_prev_world_spherical_harmonics' else 'sh' if 'spherical_harmonics' in resource else 'noise' if 'noise' in resource else 'colour']
        srvs[slot]=item[1]
    ctx('PSSetShaderResources',(U,0),(U,16),(C.POINTER(P),(P*16)(*srvs)))
    array=(P*14)(*[cbuffers.get(i,P()) for i in range(14)])
    ctx('PSSetConstantBuffers',(U,0),(U,14),(C.POINTER(P),array))
    cases=[]
    # All SH bounds, probe blends, both normal-map paths; vary fog and mips.
    for terms,lerp,animated in itertools.product(range(10),(0,.5,1),(False,True)):
        cases.append(dict(terms=terms,probe=lerp,animated=animated,fog=1,depth=0,distance=200,uvscale=.2))
    for fog,readable,distance,scale,alpha in itertools.product((0,.35,1),(0,1),(1,3000),(.1,4),(.0001,.7)):
        cases.append(dict(terms=9,probe=.5,animated=True,fog=fog,depth=readable,distance=distance,uvscale=scale,alpha=alpha))
    for sh,mode,noise,shroud in itertools.product((0,1),(0,1),(0,.6),(0,1)):
        cases.append(dict(terms=9,probe=.5,animated=False,fog=.6,depth=0,distance=120,uvscale=1,sh=sh,mode=mode,noise=noise,shroud=shroud))
    if b.OVERLAY:
        for lighting,night in itertools.product((-2,-7.2718,-8.2718,-9.2718), (0,.5,1)):
            cases.append(dict(terms=9,probe=.5,animated=False,fog=.6,depth=0,distance=120,uvscale=1,lighting=lighting,night=night))
    maxerror=0;visible=0;nonzero=0;fingerprints=set()
    for case in cases:
        defaults();setv('g_spherical_harmonic_terms',case['terms']);setv('g_specular_probe_lerp',case['probe']);setv('g_fog_lerp',case['fog']);setv('g_readable_depth',case['depth'])
        setv('g_use_spherical_harmonics',case.get('sh',1));setv('g_fog_mode',case.get('mode',0));setv('g_fog_noise',case.get('noise',.4));setv('g_shroud_enabled',case.get('shroud',0))
        setv('g_cube_ambient_influence',case.get('night',.5))
        for slot,obj in cbuffers.items():upload(obj,bytes(data[slot]))
        animated=case['animated'];values=(0,10,case['distance'],case.get('lighting',.5), .5,.37,.4,1, .8,.7,.6,case.get('alpha',.7), .13 if animated else 0,-.07 if animated else 0,case['uvscale'],0)
        upload(vcb,struct.pack('<16f',*values));a=readpixels(old);c=readpixels(new)
        assert all(math.isfinite(x) for x in a+c),(name,case,'nonfinite')
        err=max(abs(x-y) for x,y in zip(a,c));maxerror=max(err,maxerror)
        assert all(abs(x-y)<=2e-5+2e-5*abs(x) for x,y in zip(a,c)),(name,case,err)
        visible+=sum(x!=-9 for x in a[::4])
        nonzero+=sum(x not in (-9,0) for x in a[::4]);fingerprints.add(hash(a))
    assert visible>0,'No fragments rendered'
    assert nonzero>0 and len(fingerprints)>1,('Test inputs did not exercise shader output',name,nonzero,len(fingerprints))
    results.append(dict(shader=name,cases=len(cases),comparedPixels=len(cases)*N*N,maxAbsoluteError=maxerror,visiblePixels=visible,nonzeroColourPixels=nonzero,distinctOutputs=len(fingerprints)))
    print(results[-1],flush=True)
out=dict(status='PASS_D3D11_HARDWARE' if hardware else 'PASS_D3D11_WARP',fullInstalledAndCandidatePixelShaders=True,featureLevel=hex(feature.value),renderSize=[N,N],cases=sum(x['cases'] for x in results),comparedPixels=sum(x['comparedPixels'] for x in results),results=results)
(W/('gpu-validation-hardware.json' if hardware else 'gpu-validation.json')).write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='results'},indent=2))
