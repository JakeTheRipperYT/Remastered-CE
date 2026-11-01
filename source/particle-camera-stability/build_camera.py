"""Correct CE particle depth addressing; stage only, preserve current60 baseline."""
from pathlib import Path
import sys,json,hashlib,ctypes as C
W=Path(sys.argv[sys.argv.index('--work')+1]) if '--work' in sys.argv else Path(__file__).resolve().parent
W.mkdir(parents=True,exist_ok=True);P=W.parent/'particle-priority-2'
sys.path.insert(0,str(P));import build_candidate as b
G=Path(r'D:/SteamLibrary/steamapps/common/Shogun 2 Complete Edition/RemasteredCE')
if '--game-root' in sys.argv:G=Path(sys.argv[sys.argv.index('--game-root')+1])
MAIN='bdad67a5548b3b181dd28acc589b8875bc0f1bf2cac8d4e1432a3f8551e12459';OVERLAY='703dc62e15c5931f7d797df70743db1e290070364a55826d23a5e4e0b1fe9a4f'
sha=lambda x:hashlib.sha256(x).hexdigest()
def patch(source):
    old='float scene_depth = gbuffer_eyespace_depth(depth_uv);'
    assert source.count(old)==1
    return source.replace(old,'''// Address the actual readable-depth texture. CE's legacy helper
        // multiplies UVs by screen_size-1 and can fetch a neighbouring pixel
        // or the wrong region when the particle/depth targets differ in size.
#if defined(AA_SAMPLE_COUNT)
        uint depth_width, depth_height, depth_samples;
        aa_gbuffer_readable_depth_texture.GetDimensions(depth_width, depth_height, depth_samples);
        int2 depth_pixel = get_safe_pixel_coords(depth_uv, uint2(depth_width, depth_height));
        float scene_depth = compute_eye_depth(depth_uv,
            unpack_depth(aa_gbuffer_readable_depth_texture.Load(depth_pixel, 0).r));
#else
        float scene_depth = eyespace_depth(depth_uv, gbuffer_readable_depth_texture);
#endif''',1)
def guard_depth_overloads(source):
    # These overloads call clipspace_depth, which is declared only in the
    # non-MSAA branch. Keep the Texture2D helpers in that branch as well.
    start=source.index('float eyespace_depth(in const float2 uv, Texture2D tex, SamplerState sam)')
    end=source.index('//\n// gbuffer_eyespace_depth()',start)
    return source[:start]+'#if !defined(AA_SAMPLE_COUNT)\n'+source[start:end]+'#endif\n\n'+source[end:]
def main():
    raw=(G/'data/shaders.pack').read_bytes();assert sha(raw)==MAIN
    assert sha((G/'data/rce_campaign_night_visuals.pack').read_bytes())==OVERLAY
    entries,_=b.readpack(raw);effective=dict(entries);effective.update(b.read_overlay(G/'data/rce_campaign_night_visuals.pack'))
    sources={n:e['data'].decode().replace('\r\n','\n') for n,e in effective.items() if n.startswith('fx/')}
    stage=W/'candidate-source';stage.mkdir(exist_ok=True);(W/'personal_config.h').write_text('// Empty runtime personal configuration.\n')
    vanilla_path=Path(sys.argv[sys.argv.index('--vanilla')+1]) if '--vanilla' in sys.argv else G.parent/'data/shaders.pack'
    vanilla,_=b.readpack(vanilla_path.read_bytes())
    legacy={n:e['data'].decode().replace('\r\n','\n') for n,e in vanilla.items() if n.startswith('fx/')}
    variants=[];replacement={'fx/particle_volumetric.hlsl':patch(sources['fx/particle_volumetric.hlsl']).encode(),'fx/gbuffer_msaa.hlsl':guard_depth_overloads(sources['fx/gbuffer_msaa.hlsl']).encode()}
    for name,e in effective.items():
        if not name.startswith('fxc/dx11_sm_5_0_default_') or '_ps_' not in name:continue
        file,entry=name.removeprefix('fxc/dx11_sm_5_0_default_').removesuffix('.fxc').split('_ps_',1)
        if file not in ('particle.hlsl','particle_distortion.hlsl','particle_screen_splat.hlsl'):continue
        # Main smoke uses current weather-aware60 shaders. Other three shaders
        # retain earlier compiled bodies: control-match their corresponding
        # sources, applying only the addressing fix to each compiled variant.
        current=file=='particle.hlsl'
        control_sources=sources if current else legacy
        b.FX=stage/'fx'
        for n,text in control_sources.items():
            p=stage/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8',newline='\n')
        position=e['data'].index(b'DXBC');old=e['data'][position:];oldasm=b.assembly(old)
        control,warnings=b.compile_shader(file,entry,'ps',4096)
        assert b.normalize(b.assembly(control))==b.normalize(oldasm),'Control mismatch '+name
        (stage/'fx/particle_volumetric.hlsl').write_text(patch(control_sources['fx/particle_volumetric.hlsl']),encoding='utf-8',newline='\n')
        (stage/'fx/gbuffer_msaa.hlsl').write_text(guard_depth_overloads(control_sources['fx/gbuffer_msaa.hlsl']),encoding='utf-8',newline='\n')
        code,warnings=b.compile_shader(file,entry,'ps',4096);asm=b.assembly(code)
        assert b.interface(asm)==b.interface(oldasm),'Interface mismatch '+name
        replacement[name]=e['data'][:position]+code
        (W/'disassembly').mkdir(exist_ok=True);(W/'disassembly'/(Path(name).name+'.asm')).write_text(asm)
        variants.append(dict(path=name,kind='ps',controlMatchesInstalled=True,interfaceUnchanged=True,compilerFlags=4096,warnings=warnings))
    # Publish the cumulative current source, rather than a historical control.
    for n,text in sources.items():
        p=stage/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8',newline='\n')
    (stage/'fx/particle_volumetric.hlsl').write_bytes(replacement['fx/particle_volumetric.hlsl'])
    (stage/'fx/gbuffer_msaa.hlsl').write_bytes(replacement['fx/gbuffer_msaa.hlsl'])
    for n,data in replacement.items():
        p=W/'replacements'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    assert len(variants)==5
    report=dict(status='STAGED_CAMERA_DEPTH_CANDIDATE',baselineVersion='0.1.60-preview',beforeMainSha256=MAIN,beforeOverlaySha256=OVERLAY,changedEntries=list(replacement),variants=variants,installed=False,flashingConfirmedFixed=False)
    (W/'candidate-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='variants'},indent=2))
    if '--check-msaa' in sys.argv:
        counts=[]
        for count in [2,4,8]:
            macros=(b.Macro*3)(b.Macro(b'AA_SAMPLE_COUNT',str(count).encode()),b.Macro(b'MTB_ENABLE_MSAA',b'1'),b.Macro(None,None))
            code=C.c_void_p();errors=C.c_void_p()
            result=b.compilefn(str(b.FX/'particle.hlsl'),macros,C.c_void_p(1),b'ps30_volumetric_particle_alpha',b'ps_5_0',4096,0,C.byref(code),C.byref(errors))
            warning=b.take(errors).decode(errors='replace');assert result>=0,warning;b.take(code);counts.append(count)
        (W/'msaa-compile-validation.json').write_text(json.dumps(dict(status='PASS',sampleCounts=counts,scope='Candidate compile checks only; not multisample draw comparisons',legacyTwoDimensionalOverloadsGuarded=True),indent=2))
if __name__=='__main__':main()
