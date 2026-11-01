"""Stage priority-ordered particle work against accepted private 0.1.59."""
from pathlib import Path
import sys,json,hashlib,ctypes as C,struct
W=Path(sys.argv[sys.argv.index('--work')+1]) if '--work' in sys.argv else Path(__file__).resolve().parent
W.mkdir(parents=True,exist_ok=True);P=W.parent/'particle-cost-audit'
sys.path.insert(0,str(P));import build_candidate as b
G=Path(r'D:/SteamLibrary/steamapps/common/Shogun 2 Complete Edition/RemasteredCE')
if '--game-root' in sys.argv:G=Path(sys.argv[sys.argv.index('--game-root')+1])
BASE='72f63419db64ce21fab8b4c03e3d9a2dd1ffa41735ea2857f9578add2f9429e6'
OVERLAY='069d979bcc8ed47465bad1a416fc2c37a21111ed31ffc5798c56b4456607d112'
sha=lambda x:hashlib.sha256(x).hexdigest()
def edit(text,old,new):
    assert text.count(old)==1,old[:120]
    return text.replace(old,new,1)
def body(text,signature):
    start=text.index(signature);opening=text.index('{',start);depth=1;end=opening+1
    while depth:
        depth+=(text[end]=='{')-(text[end]=='}');end+=1
    return start,end,text[start:end]
def fog_split(source):
    start,end,f=body(source,'float3 get_fog_colour_inscattering(')
    loopstart=f.index('\t\t// Raymarch');loopend=f.index('\n\t\t// Apply constant terms',loopstart)
    oldloop=f[loopstart:loopend]
    # Density noise contributes only to analytic height/constant fog. It does
    # not affect the atmospheric extinction accumulated in the original loop.
    noise_start=oldloop.index('\t\t\t// Noise starts one')
    noise_end=oldloop.index('\n\t\t\t// Compute optical depth',noise_start)
    noise=oldloop[noise_start:noise_end]
    noise_loop='''
        // First integrate density noise, without atmospheric exponentials.
        // When noise is disabled every original sample contributes exactly 1.
        if (!LQ && g_fog_noise > 0) {
            [loop] for (int s = 0; s < num_steps; ++s) {
                float fs = float(s) + jitter;
                float distance = min(step*0.5f + step*fs, camera_distance);
                float3 p = camera_position_modified + view_dir * distance;
'''+noise+'''
            }
        } else total_noise = num_steps;
        // Native shadow sampling is disabled (V is always 1).
        shadow = num_steps;
'''
    # Preserve the exact original scattering accumulation. Remove the unrelated
    # noise/mask/shadow work; the installed variant has DISABLE_FOG_MASK=1.
    atmospheric=oldloop.replace(noise,'')
    mask_start=atmospheric.index('\t\t\tconst float2 mask_uv')
    mask_end=atmospheric.index('\n\t\t\t// Integrate section',mask_start)
    atmospheric=atmospheric[:mask_start]+atmospheric[mask_end:]
    # shadow += V is unnecessary because V is identically 1 in the native shader.
    atmospheric=atmospheric.replace('shadow += V;','')
    # Original c assignment is moved along with the atmospheric loop.
    cstart=loopend;cend=f.index('\n\t\t// use height fog clear distance',cstart)
    old_c=f[cstart:cend]
    # Separate normalization/mask setup from the phase-function calculation.
    norm_start=old_c.index('\t\tshadow /= num_steps;')
    phase=old_c[:old_c.index('\n\t\t// Compute full integral')]
    normal=old_c[norm_start:]
    f=f[:loopstart]+noise_loop+normal+f[cend:]
    # Analytic fog changes view_dir for height noise. Scattering needs the
    # original unperturbed ray, so recover the exact original expression.
    anchor='\n\t\tfog = max(fog_h * total_height_fog_mask, fog_c * total_fog_mask);'
    insertion=anchor+'''
        // Once RGB fog is fully opaque, atmospheric radiance is multiplied
        // by zero in the original final blend. Skip only that unused work.
        [branch] if (any(max(fog, forced_fog_factor) < 1.0f)) {
            view_dir = (world_pos - camera_position) / unmodified_camera_distance;
'''+atmospheric+phase+'''
        }
'''
    f=edit(f,anchor,insertion)
    return source[:start]+f+source[end:]
def stage():
    raw=(G/'data/shaders.pack').read_bytes();assert sha(raw)==BASE
    assert sha((G/'data/rce_campaign_night_visuals.pack').read_bytes())==OVERLAY
    entries,_=b.readpack(raw);effective=dict(entries);effective.update(b.read_overlay(G/'data/rce_campaign_night_visuals.pack'))
    original={n:e['data'].decode().replace('\r\n','\n') for n,e in effective.items() if n.startswith('fx/')}
    stage=W/'candidate-source';b.FX=stage/'fx';b.FX.mkdir(parents=True,exist_ok=True);(W/'personal_config.h').write_text('// Empty runtime personal configuration.\n')
    for name,text in original.items():
        p=stage/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8',newline='\n')
    variants=[]
    for name,e in effective.items():
        if not name.startswith('fxc/dx11_sm_5_0_default_'):continue
        rest=name.removeprefix('fxc/dx11_sm_5_0_default_').removesuffix('.fxc')
        if '_ps_' in rest:
            filename,entry=rest.split('_ps_',1);kind='ps'
            if filename!='particle.hlsl':continue
        elif '_vs_' in rest:
            filename,entry=rest.split('_vs_',1);kind='vs'
            if filename not in ('particle.hlsl','particle_distortion.hlsl','particle_screen_splat.hlsl'):continue
        else:continue
        pos=e['data'].index(b'DXBC')
        oldasm=b.assembly(e['data'][pos:]);flags=None
        for candidateflags in ([4096] if kind=='ps' else [0,4096,32768,32768|4096,2048,4096|2048]):
            try:control,w=b.compile_shader(filename,entry,kind,candidateflags)
            except RuntimeError:continue
            if b.normalize(b.assembly(control))==b.normalize(oldasm):flags=candidateflags;break
        if flags is None:
            import difflib
            (W/'control-mismatch.diff').write_text('\n'.join(difflib.unified_diff(b.normalize(oldasm),b.normalize(b.assembly(control)),n=2)))
            raise AssertionError('Control mismatch '+name)
        variants.append(dict(name=name,filename=filename,kind=kind,flags=flags,entry=entry,oldasm=oldasm,offset=pos))
    changed={'fx/fog_3k.hlsl':fog_split(original['fx/fog_3k.hlsl'])}
    # Priority2: only the native alpha-blended techniques. Native registration
    # 181a21620 selects SRC_ALPHA/INV_SRC_ALPHA and disables depth writes.
    # Additive techniques do not receive this flag.
    particle=original['fx/particle_volumetric.hlsl']
    particle=edit(particle,'uniform bool output_normal_only=false)','uniform bool output_normal_only=false, uniform bool alpha_blended=false)')
    particle=edit(particle,'\tfloat4 norm1 =','''    // Exactly zero alpha is a blend identity for registered alpha techniques.
    // Do not reject faint pixels or additive particles.
    if (alpha_blended && colour.a == 0.0f) discard;
\tfloat4 norm1 =''')
    changed['fx/particle_volumetric.hlsl']=particle
    wrappers=original['fx/particle.hlsl']
    wrappers=edit(wrappers,'volumetric_particle_pixel( input, false, true, false, true )','volumetric_particle_pixel( input, false, true, false, true, false, true )')
    wrappers=edit(wrappers,'volumetric_particle_pixel( input, true, true, false, true )','volumetric_particle_pixel( input, true, true, false, true, false, true )')
    changed['fx/particle.hlsl']=wrappers
    # Priority3: at a zero probe blend the current probe contributes nothing.
    # The original shader still evaluated it before lerping to previous.
    sky=original['fx/sky.hlsl']
    anchor='float3 colour = spherical_harmonic_single_tex(t_world_spherical_harmonics, world_position, direction, ambient_up_light, up_only);'
    sky=edit(sky,anchor,'''[branch] if (g_specular_probe_lerp == 0.0f)
        return spherical_harmonic_single_tex(t_prev_world_spherical_harmonics, world_position, direction, ambient_up_light, up_only);
    '''+anchor)
    changed['fx/sky.hlsl']=sky
    # Priority4 audit: the native constructor registers only full quality and
    # additive techniques, not the unused _lq source wrappers. No invented menu
    # switch or unrequested image-quality reduction is introduced.
    # Priority5: reduce repeated vertex calculations without changing native
    # particle records, sorting, draw topology, simulation or lifetime.
    particle=edit(particle,'float2 expansion = float2(pow_abs(life_unary, gamma.x), pow_abs(life_unary, gamma.y));','''float2 expansion;
    [branch] if (gamma.x == gamma.y) {
        // A shared scale curve needs only one exponentiation, and gamma=1
        // is the identity. Other curves retain the original implementation.
        float value;
        [branch] if (gamma.x == 1.0f) value = life_unary;
        else value = pow_abs(life_unary, gamma.x);
        expansion = float2(value, value);
    } else expansion = float2(pow_abs(life_unary, gamma.x), pow_abs(life_unary, gamma.y));''')
    changed['fx/particle_volumetric.hlsl']=particle
    # Screen splats have their own copy of the expansion calculation.
    splat=original['fx/particle_screen_splat.hlsl']
    old='float2 expansion = float2(pow_abs(life_unary, gamma.x), pow_abs(life_unary, gamma.y));'
    if old in splat:
        splat=edit(splat,old,'''float2 expansion;
    [branch] if (gamma.x == 1.0f) expansion.x = life_unary;
    else expansion.x = pow_abs(life_unary, gamma.x);
    expansion.y = pow_abs(life_unary, gamma.y);''')
        changed['fx/particle_screen_splat.hlsl']=splat
    for name,text in changed.items():(stage/name).write_text(text,encoding='utf-8',newline='\n')
    replacements={n:t.encode() for n,t in changed.items()};reports=[]
    for v in variants:
        code,warnings=b.compile_shader(v['filename'],v['entry'],v['kind'],v['flags']);asm=b.assembly(code)
        # The helper compares reflection comments including stage signatures.
        if b.interface(asm.replace('vs_5_0','ps_5_0'))!=b.interface(v['oldasm'].replace('vs_5_0','ps_5_0')):
            import difflib
            (W/'interface-mismatch.diff').write_text('\n'.join(difflib.unified_diff(b.interface(v['oldasm'].replace('vs_5_0','ps_5_0')).splitlines(),b.interface(asm.replace('vs_5_0','ps_5_0')).splitlines(),n=2)))
            raise AssertionError('Interface changed '+v['name'])
        (W/'disassembly').mkdir(exist_ok=True);(W/'disassembly'/(Path(v['name']).name+'.asm')).write_text(asm)
        replacements[v['name']]=effective[v['name']]['data'][:v['offset']]+code
        reports.append(dict(path=v['name'],kind=v['kind'],interfaceUnchanged=True,controlMatchesInstalled=True,warnings=warnings))
    for name,data in replacements.items():
        p=W/'replacements'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    (W/'candidate-validation.json').write_text(json.dumps(dict(status='STAGED_PRIORITY_1',variants=reports,changedEntries=list(replacements)),indent=2))
    print('Staged priority1 fog split',list(replacements))
if __name__=='__main__':stage()
