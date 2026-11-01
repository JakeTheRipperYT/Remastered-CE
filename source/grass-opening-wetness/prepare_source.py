from pathlib import Path
import shutil
R=Path(r'F:/Codex/Remastered-CE-Port');old=R/'work/grass-matte';W=R/'work/grass-opening-wetness'
shutil.copytree(old/'compile',W/'compile',dirs_exist_ok=True)
for n in ['personal_config.h','GrassFixture.cs']:shutil.copyfile(old/n,W/n)
s=(old/'build_shaders.py').read_text();a=s.index("\nsource=eff['fx/rigidgrasscommon.hlsl']")+1;z=s.index("replacements={'fx/rigidgrasscommon.hlsl'",a)
s=s[:a]+'''source=original_source
old_start=source.index('\\tif (u_wet)')
old_end=source.index('\\tfloat d0 =',old_start)
assert 'roughness = max(roughness, 0.9f);' in source[old_start:old_end]
assert 'metalness = 0.0f;' in source[old_start:old_end]
new_block='''+repr('''    // Matte grass base, before the separately controlled wet coating.
    roughness = max(roughness, 0.9f);
    metalness = 0.0f;
    // Match the immutable opening-ground wetness used by terrain puddles.
    // A later rain/clear shader permutation cannot change the ground policy.
    bool grass_ground_wet = rce_weather_managed()
        ? (g_rce_weather_old_material.w > 0.5f) : u_wet;
    if (grass_ground_wet)
        roughness *= g_rain_vegetation_roughness_multiplier;

''')+'''
modified=source[:old_start]+new_block+source[old_end:]
(FX/'rigidgrasscommon.hlsl').write_text(modified)
'''+s[z:]
s=s.replace(" assert b.interface(newasm)==b.interface(v['oldasm']),('Interface changed',v['name'])",''' # Existing IO and constant-buffer field layouts must survive; the named
 # weather buffer is deliberately added and bound by native program reflection.
 import re
 def signature(asm):return asm[asm.index('// Input signature:'):asm.index('ps_5_0')]
 assert signature(newasm)==signature(v['oldasm']),('IO changed',v['name'])
 assert '// cbuffer rce_weather_shared' in newasm
 for field,offset in [('g_rce_weather_surface',0),('g_rce_weather_old_material',48)]:
  assert re.search(field+r';.*Offset:\\s*'+str(offset)+r'\\s+Size:',newasm),field
 assert 'g_rain_vegetation_roughness_multiplier' in newasm
''')
s=s.replace('interfaceUnchanged=True','ioSignaturesPreserved=True,namedWeatherBufferAdded=True').replace("roughnessFloor=0.9,metalness=0", "baseRoughnessFloor=0.9,metalness=0,wetnessFromOpeningGround=True")
s=s.replace('interface-checked; vertex, shadow and scene-lighting code untouched.','checked; base matte preserved and wetness follows opening-ground state.')
(W/'build_shaders.py').write_text(s)
# Keep exact historical compile dependencies used to reproduce installed grass bytecode.
for name in ['lighting.hlsl','sky.hlsl','fog_3k.hlsl']:shutil.copyfile(old/'compile/fx'/name,W/'compile/fx'/name)
