"""Reproduce installed particle shaders, then build appearance-preserving cost fixes.
Only stages files on F:. Never installs or launches the game.
"""
from pathlib import Path
import ctypes as C, hashlib, json, re, shutil, struct, difflib,sys
W=Path(sys.argv[sys.argv.index('--work')+1]) if '--work' in sys.argv else Path(__file__).resolve().parent
W.mkdir(parents=True,exist_ok=True)
ROOT=W.parent.parent
TARGET=Path(r'D:\SteamLibrary\steamapps\common\Shogun 2 Complete Edition\RemasteredCE\data\shaders.pack')
if '--baseline' in sys.argv:TARGET=Path(sys.argv[sys.argv.index('--baseline')+1])
OVERLAY=Path(sys.argv[sys.argv.index('--overlay')+1]) if '--overlay' in sys.argv else None
EXPECTED='557b8609be67db84a06369970b276b6eb3c4a4e8ddba803f5aa64544f17ff228'
def sha(b):return hashlib.sha256(b).hexdigest()
def readpack(raw):
    assert raw[:4]==b'PFHs'
    flags,_,deps,count,size=struct.unpack_from('<5I',raw,4)
    assert flags==0x41 and deps==0
    pos=32; entries={}
    for _ in range(count):
        at=pos;off,n=struct.unpack_from('<QI',raw,pos);pos+=20
        end=raw.index(0,pos);name=raw[pos:end].decode().replace('\\','/');pos=end+1
        assert off+n<=len(raw)
        entries[name]=dict(offset=off,size=n,index=at,data=raw[off:off+n])
    assert pos==32+size
    return entries,pos
def read_overlay(path):
    raw=Path(path).read_bytes();assert raw[:4]==b'PFHs'
    flags,_,deps,count,size=struct.unpack_from('<5I',raw,4);assert flags==0x64 and deps==0
    lzpath=sys.argv[sys.argv.index('--lz4')+1] if '--lz4' in sys.argv else r'F:\Codex\Workspaces\2026-10-16\ca\work\installer\lz4.dll'
    lz=C.CDLL(lzpath)
    lz.LZ4_decompress_safe.argtypes=[C.c_void_p,C.c_void_p,C.c_int,C.c_int]
    pos=32;entries={}
    for _ in range(count):
        at=pos;off,n,stored=struct.unpack_from('<QII',raw,pos);pos+=24
        end=raw.index(0,pos);name=raw[pos:end].decode().replace('\\','/');pos=end+1
        out=C.create_string_buffer(n);assert lz.LZ4_decompress_safe(raw[off:off+stored],out,stored,n)==n
        entries[name]=dict(offset=off,size=n,index=at,data=out.raw)
    assert pos==32+size
    return entries
dll=C.WinDLL('d3dcompiler_47.dll')
class Macro(C.Structure):_fields_=[('Name',C.c_char_p),('Definition',C.c_char_p)]
compilefn=dll.D3DCompileFromFile
compilefn.argtypes=[C.c_wchar_p,C.POINTER(Macro),C.c_void_p,C.c_char_p,C.c_char_p,C.c_uint,C.c_uint,C.POINTER(C.c_void_p),C.POINTER(C.c_void_p)]
compilefn.restype=C.c_long
disasm=dll.D3DDisassemble
disasm.argtypes=[C.c_void_p,C.c_size_t,C.c_uint,C.c_char_p,C.POINTER(C.c_void_p)]
disasm.restype=C.c_long
def take(blob):
    if not blob:return b''
    vt=C.cast(blob,C.POINTER(C.POINTER(C.c_void_p))).contents
    ptr=C.WINFUNCTYPE(C.c_void_p,C.c_void_p)(vt[3])(blob)
    size=C.WINFUNCTYPE(C.c_size_t,C.c_void_p)(vt[4])(blob)
    result=C.string_at(ptr,size);C.WINFUNCTYPE(C.c_ulong,C.c_void_p)(vt[2])(blob);return result
def assembly(code):
    blob=C.create_string_buffer(code);out=C.c_void_p()
    assert disasm(blob,len(code),0,None,C.byref(out))>=0
    return take(out).rstrip(b'\0').decode()
def normalize(text):
    return [s.split('//')[0].strip() for s in text.splitlines() if s.split('//')[0].strip() and not s.startswith('#')]
def compile_shader(filename,entry,stage,flags):
    macros=(Macro*1)(Macro(None,None));code=C.c_void_p();errors=C.c_void_p()
    hr=compilefn(str(FX/filename),macros,C.c_void_p(1),entry.encode(),(stage+'_5_0').encode(),flags,0,C.byref(code),C.byref(errors))
    warning=take(errors).decode(errors='replace')
    if hr<0:raise RuntimeError(warning)
    return take(code),warning
def interface(text):
    # Include buffer member offsets, resources/registers and stage signatures.
    # Strip only compiler liveness annotations; declarations/bindings must match.
    comments=text.split('ps_5_0')[0]
    return re.sub(r' \[unused\]','',comments).strip()
def replace_once(text,old,new):
    assert text.count(old)==1,old
    return text.replace(old,new,1)

def build():
    global FX
    original=TARGET.read_bytes();assert sha(original)==EXPECTED
    entries,index_end=readpack(original)
    effective=dict(entries)
    if OVERLAY:
        assert sha(OVERLAY.read_bytes())=='55b0baa62325ffce2a16533a8bc0605b687ede93e3c3b79b4319823d1d9ec097','Unexpected campaign override baseline'
        effective.update(read_overlay(OVERLAY))
    stage=W/'candidate-source';FX=stage/'fx';FX.mkdir(parents=True,exist_ok=True)
    (W/'personal_config.h').write_text('// Empty default runtime configuration.\n')
    sources={name:e['data'].decode().replace('\r\n','\n') for name,e in effective.items() if name.startswith('fx/')}
    for name,text in sources.items():
        p=stage/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8',newline='\n')
    variants=[]
    for name,e in effective.items():
        if not name.startswith('fxc/dx11_sm_5_0_default_') or '_ps_' not in name:continue
        filename,entry=name.removeprefix('fxc/dx11_sm_5_0_default_').removesuffix('.fxc').split('_ps_',1)
        if filename not in ('particle.hlsl','particle_screen_splat.hlsl','particle_distortion.hlsl'):continue
        if OVERLAY and filename!='particle.hlsl':continue
        raw=e['data'];at=raw.index(b'DXBC');assert at+struct.unpack_from('<I',raw,at+24)[0]==len(raw)
        oldasm=assembly(raw[at:]);matched=None
        for flags in [0,32768,2048,32768|2048,4096,32768|4096,4]:
            try:control,warning=compile_shader(filename,entry,'ps',flags)
            except RuntimeError:continue
            if normalize(assembly(control))==normalize(oldasm):matched=flags;break
        assert matched is not None,'Cannot reproduce '+name
        variants.append(dict(name=name,filename=filename,entry=entry,flags=matched,offset=at,oldasm=oldasm))
        print('Reproduced',name,flush=True)
    assert len(variants)==(2 if OVERLAY else 5)

    changed={}
    sky=sources['fx/sky.hlsl']
    # Restrict signature edits to the two full-quality SH functions.
    for fn in ['spherical_harmonic_single_tex','spherical_harmonic']:
        pat=r'(float3 '+fn+r'\([^\n]*out float3 ambient_up_light)\)'
        sky,n=re.subn(pat,r'\1, uniform bool up_only = false)',sky);assert n==1
    old='int terms = round(g_spherical_harmonic_terms);\n\tfor (int i = 0; i < terms; ++i)\n\t{'
    new='''int terms = round(g_spherical_harmonic_terms);
    // For the fog's fixed up normal only coefficients 0,2,7,8 contribute.
    // Preserve coefficient order and the runtime term count.
    static const int up_indices[4] = {0, 2, 7, 8};
    int count = up_only ? int(terms > 0) + int(terms > 2) + int(terms > 7) + int(terms > 8) : terms;
    for (int term = 0; term < count; ++term)
    {
        int i = up_only ? up_indices[term] : term;'''
    # First occurrence is full-quality single texture; LQ remains untouched.
    assert old in sky;sky=sky.replace(old,new,1)
    sky=replace_once(sky,'t_world_spherical_harmonics, world_position, direction, ambient_up_light);','t_world_spherical_harmonics, world_position, direction, ambient_up_light, up_only);')
    sky=replace_once(sky,'t_prev_world_spherical_harmonics, world_position, direction, ambient_up_light);','t_prev_world_spherical_harmonics, world_position, direction, ambient_up_light, up_only);')
    changed['fx/sky.hlsl']=sky
    light=sources['fx/lighting.hlsl']
    light=replace_once(light,'float3 get_ambient_light(float3 world_pos, float3 normal, bool use_spherical_harmonics = true, uniform bool LQ = false)','float3 get_ambient_light(float3 world_pos, float3 normal, bool use_spherical_harmonics = true, uniform bool LQ = false, uniform bool up_only = false)')
    light=replace_once(light,'return spherical_harmonic(world_pos, normal, ambient_up_light) * g_ambient_fudge_factor;','return spherical_harmonic(world_pos, normal, ambient_up_light, up_only) * g_ambient_fudge_factor;')
    changed['fx/lighting.hlsl']=light
    fog=sources['fx/fog_3k.hlsl']
    fog=replace_once(fog,'float3(0, 1, 0), use_spherical_harmonics, LQ);','float3(0, 1, 0), use_spherical_harmonics, LQ, true);')
    # Restrict the no-fog exit to this particle call site below. Other materials unchanged.
    changed['fx/fog_3k.hlsl']=fog
    particle=sources['fx/particle_volumetric.hlsl']
    particle=replace_once(particle,'if (bapply_fog)','if (bapply_fog && g_fog_lerp != 0.0f)')
    particle=replace_once(particle,'float4 norm2 = tex2D(s_normalmap_texture, input.tex_uv2_normal_uv2.zw);','''float4 norm2 = norm1;
    // These UVs coincide for the default normal map. The second sample is
    // needed only for distinct animation frames. Explicit gradients preserve
    // mip selection across the branch, including at particle boundaries.
    float2 normal_dx = ddx(input.tex_uv2_normal_uv2.zw);
    float2 normal_dy = ddy(input.tex_uv2_normal_uv2.zw);
    [branch] if (any(input.tex_uv1_normal_uv1.zw != input.tex_uv2_normal_uv2.zw))
        norm2 = tex2Dgrad(s_normalmap_texture, input.tex_uv2_normal_uv2.zw, normal_dx, normal_dy);''')
    # Retain the installed compiler's depth-before-normal-fetch ordering.
    start=particle.index('\tfloat4 norm1 =')
    end=particle.index('\n',particle.index('float4 normal_map =',start))
    normal_block=particle[start:end]
    particle=particle[:start]+particle[end:]
    particle=replace_once(particle,'\tfloat3 normal = unpack_normal(normal_map.rgb);',normal_block+'\n\n\tfloat3 normal = unpack_normal(normal_map.rgb);')
    changed['fx/particle_volumetric.hlsl']=particle
    for name,text in changed.items():(stage/name).write_text(text,encoding='utf-8',newline='\n')
    replacements={name:text.encode() for name,text in changed.items()}
    reports=[]
    for v in variants:
        blob,warning=compile_shader(v['filename'],v['entry'],'ps',v['flags']);asm=assembly(blob)
        name=v['name'];(W/'candidate-disassembly').mkdir(exist_ok=True)
        (W/'candidate-disassembly'/(Path(name).name+'.asm')).write_text(asm)
        if interface(asm)!=interface(v['oldasm']):
            (W/'interface-mismatch.diff').write_text('\n'.join(difflib.unified_diff(interface(v['oldasm']).splitlines(),interface(asm).splitlines())))
            raise AssertionError('Shader interface changed: '+name)
        assert normalize(asm)!=normalize(v['oldasm'])
        assert 'sample_d' in asm,'Conditional explicit-gradient sample missing'
        replacements[name]=effective[name]['data'][:v['offset']]+blob
        reports.append(dict(path=name,compilerFlags=v['flags'],controlMatchesInstalled=True,interfaceUnchanged=True,wrapperPreserved=True,warnings=warning,beforeSha256=sha(effective[name]['data']),sha256=sha(replacements[name])))
        print('Compiled/interface verified',name,flush=True)
    # Canonical archive body with explicit zero padding; recipes reproduce every
    # byte without keeping obsolete copies of replaced shader bodies.
    candidate=bytearray(original[:index_end])
    for name,e in sorted(entries.items(),key=lambda item:item[1]['offset']):
        data=replacements.get(name,e['data']);cursor=(len(candidate)+15)//16*16
        candidate.extend(b'\0'*(cursor-len(candidate)));candidate.extend(data)
        struct.pack_into('<QI',candidate,e['index'],cursor,len(data))
    if len(candidate)<len(original):candidate.extend(b'\0'*(len(original)-len(candidate)))
    newentries,_=readpack(candidate)
    for name,e in entries.items():assert newentries[name]['data']==replacements.get(name,e['data']),name
    spans=sorted((e['offset'],e['offset']+e['size']) for e in newentries.values());assert all(a[1]<=b[0] for a,b in zip(spans,spans[1:]))
    output=W/'shaders.particle-cost-candidate.pack';output.write_bytes(candidate)
    for name,data in replacements.items():
        p=W/'replacements'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    report=dict(status='COMPILED_AND_STAGED',beforeSha256=EXPECTED,sha256=sha(candidate),candidate=str(output),entryCount=len(entries),changedEntries=list(replacements),unchangedEntries=len(entries)-len(replacements),variants=reports,installed=False,gameplayTested=False)
    (W/'candidate-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='variants'},indent=2))
if __name__=='__main__':build()
