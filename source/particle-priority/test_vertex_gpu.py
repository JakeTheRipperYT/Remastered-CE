"""Compare actual original/candidate vertex DXBC using D3D11 stream output."""
from pathlib import Path
import ctypes as C,json,struct,re,math,itertools,sys,runpy
TOOLS=Path(__file__).resolve().parent
W=Path(sys.argv[sys.argv.index('--work')+1]) if '--work' in sys.argv else TOOLS
# Reuse the verified D3D11 device/API support and run pixel checks too.
scope=runpy.run_path(str(TOOLS/'test_priority_gpu.py'));globals().update({k:v for k,v in scope.items() if not k.startswith('__')})
class InputElement(C.Structure):_fields_=[('name',C.c_char_p),('index',U),('format',U),('slot',U),('offset',U),('classification',U),('step',U)]
class StreamElement(C.Structure):_fields_=[('stream',U),('name',C.c_char_p),('index',U),('start',C.c_ubyte),('count',C.c_ubyte),('slot',C.c_ubyte)]
gs_source='''struct O{float4 p:SV_Position;float4 c:COLOR0;float4 uv0:TEXCOORD0;float4 uv1:TEXCOORD1;float4 pv:TEXCOORD3;float4 sl:TEXCOORD4;float4 wp:TEXCOORD5;};
[maxvertexcount(1)]void main(point O input[1],inout PointStream<O> output){output.Append(input[0]);}'''
file=W/'candidate-source/fx/stream_capture.hlsl';file.write_text(gs_source);b.FX=file.parent
gs_code=b.compile_shader(file.name,'main','gs',0)[0];code=C.create_string_buffer(gs_code);gs=P()
decl=(StreamElement*7)(*[StreamElement(0,name,index,0,4,0) for name,index in [(b'SV_Position',0),(b'COLOR',0),(b'TEXCOORD',0),(b'TEXCOORD',1),(b'TEXCOORD',3),(b'TEXCOORD',4),(b'TEXCOORD',5)]])
stride=U(112)
dev('CreateGeometryShaderWithStreamOutput',(P,C.cast(code,P)),(C.c_size_t,len(gs_code)),(C.POINTER(StreamElement),decl),(U,7),(C.POINTER(U),C.byref(stride)),(U,1),(U,0xffffffff),(P,None),(C.POINTER(P),C.byref(gs)))
ctx('GSSetShader',(P,gs),(P,None),(U,0));ctx('IASetPrimitiveTopology',(U,1));ctx('OMSetRenderTargets',(U,0),(P,None),(P,None))
rows=[]
for life,gamma,corner in itertools.product((-.01,0,.01,.2,.5,.8,.99,1,1.01),((0,0),(.5,.5),(1,1),(2,2),(1,2),(2,1),(.1,4)),((0,0),(1,0),(0,1),(1,1))):
    # time=5, lifetime=10. Includes inactive particles and all billboard corners.
    rows.append((*corner,5-life*10,10, 3,5,100, 1,2,3,.37, .5,.6,*gamma, .2,.3))
count=len(rows);payload=struct.pack('<'+str(count*17)+'f',*[v for row in rows for v in row]);vb=buffer(len(payload),1);upload(vb,payload)
ctx('IASetVertexBuffers',(U,0),(U,1),(C.POINTER(P),(P*1)(vb)),(C.POINTER(U),(U*1)(68)),(C.POINTER(U),(U*1)(0)))
capture=buffer(count*112,0x10);description=Buffer(count*112,3,0,0x20000,0,0);readback=P()
dev('CreateBuffer',(C.POINTER(Buffer),C.byref(description)),(P,None),(C.POINTER(P),C.byref(readback)))
entries,_=b.readpack(b.TARGET.read_bytes());entries.update(b.read_overlay(b.OVERLAY));report=json.loads((W/'candidate-validation.json').read_text());results=[]
for variant in report['variants']:
    if variant.get('kind')!='vs':continue
    name=variant['path'];before=entries[name]['data'];after=(W/'replacements'/name).read_bytes();oldcode=before[before.index(b'DXBC'):];newcode=after[after.index(b'DXBC'):]
    programs=[shader(c,'Vertex') for c in [oldcode,newcode]]
    layout=P();elements=(InputElement*6)(InputElement(b'TEXCOORD',0,16,0,0,0,0),InputElement(b'POSITION',0,16,0,8,0,0),InputElement(b'POSITION',1,6,0,16,0,0),InputElement(b'POSITION',2,2,0,28,0,0),InputElement(b'POSITION',3,2,0,44,0,0),InputElement(b'POSITION',4,16,0,60,0,0))
    blob=C.create_string_buffer(oldcode);dev('CreateInputLayout',(C.POINTER(InputElement),elements),(U,6),(P,C.cast(blob,P)),(C.c_size_t,len(oldcode)),(C.POINTER(P),C.byref(layout)))
    ctx('IASetInputLayout',(P,layout))
    asm=b.assembly(oldcode);members={};active=None
    bindings={n:int(i) for n,i in re.findall(r'^// (\w+)\s+cbuffer\s+.*?\s+cb(\d+)\s+1\s*$',asm,re.M)}
    for line in asm.splitlines():
        m=re.match(r'// cbuffer (\w+)',line)
        if m:active=m[1]
        m=re.search(r'//\s+(\w+)\s+(\w+)(?:\[\d+\])?;.*?Offset:\s*(\d+) Size:\s*(\d+)',line)
        if m and active:members[m[2]]=(active,int(m[3]),int(m[4]),m[1])
    sizes={int(i):int(n)*16 for i,n in re.findall(r'dcl_constantbuffer CB(\d+)\[(\d+)\]',asm)}
    cb={i:buffer(n,4) for i,n in sizes.items()};data={i:bytearray(n) for i,n in sizes.items()}
    def setvar(name,*values):
        if name not in members:return
        c,off,size,kind=members[name]
        assert len(values)*4<=size,(name,size)
        if off+len(values)*4>len(data[bindings[c]]):return
        struct.pack_into('<'+str(len(values))+'f',data[bindings[c]],off,*values)
    identity=(1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1)
    for key in ['view','view_projection','inv_view','projection','inv_projection']:setvar(key,*identity)
    params={'camera_position':(0,0,-10),'time_in_sec':(5,),'g_camera_aligned_x_axis':(1,0,0),'g_camera_aligned_y_axis':(0,1,0),'g_camera_aligned_z_axis':(0,0,1),'g_tpage_info':(4,.25,.25,16),'g_animation_length':(16,),'wind_particle_multiplier':(1,),'g_wind_direction':(.1,.2),'g_fade_with_height_scale':(1,)}
    for key,val in params.items():setvar(key,*val)
    setvar('screen_size',1920,1080,1/1920,1/1080)
    for bound in ['min','max']:
        for key in ['start_colour','end_colour']+['mid_'+str(i)+'_colour' for i in range(1,6)]:setvar('g_'+key+'_'+bound,.7,.6,.5,.8)
        setvar('g_wind_and_gravity_lod_ranges_'+bound,.1,.2,1000,1000)
        setvar('g_fade_info_thickness_and_lighting_'+bound,.1,.8,.5,1)
        setvar('g_anim_start_length_loops_and_damping_'+bound,0,16,1,.1)
        setvar('g_initial_rotation_and_rotation_speed_'+bound,.1,.2)
    for i in range(1,6):setvar('g_mid_'+str(i)+'_offset',i/6)
    for i,obj in cb.items():upload(obj,bytes(data[i]))
    ctx('VSSetConstantBuffers',(U,0),(U,14),(C.POINTER(P),(P*14)(*[cb.get(i,P()) for i in range(14)])))
    outputs=[]
    for program in programs:
        ctx('VSSetShader',(P,program),(P,None),(U,0));ctx('SOSetTargets',(U,1),(C.POINTER(P),(P*1)(capture)),(C.POINTER(U),(U*1)(0)))
        ctx('Draw',(U,count),(U,0));ctx('SOSetTargets',(U,0),(P,None),(P,None));ctx('CopyResource',(P,readback),(P,capture))
        mapped=Map();checked(ctx('Map',(P,readback),(U,0),(U,1),(U,0),(C.POINTER(Map),C.byref(mapped))))
        values=struct.unpack('<'+str(count*28)+'f',C.string_at(mapped.data,count*112));ctx('Unmap',(P,readback),(U,0));outputs.append(values)
    a,c=outputs
    assert all(math.isfinite(v) for v in a+c),(name,'nonfinite')
    error=max(abs(x-y) for x,y in zip(a,c))
    assert all(abs(x-y)<=2e-5+2e-5*abs(x) for x,y in zip(a,c)),(name,error)
    assert any(v!=0 for v in a),'No vertex output captured'
    results.append(dict(shader=name,vertices=count,comparedComponents=len(a),maxAbsoluteError=error));print(results[-1],flush=True)
output=dict(status='PASS_D3D11_HARDWARE_STREAM_OUTPUT' if hardware else 'PASS_D3D11_WARP_STREAM_OUTPUT',actualVertexBytecode=True,results=results)
(W/('vertex-validation-hardware.json' if hardware else 'vertex-validation.json')).write_text(json.dumps(output,indent=2))
