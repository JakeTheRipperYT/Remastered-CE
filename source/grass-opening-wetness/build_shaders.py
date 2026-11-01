from pathlib import Path
import sys,ctypes as C,struct,json,hashlib
sys.path.insert(0,r'F:/Codex/Remastered-CE-Port/work/particle-camera-stability');import build_candidate as b
W=Path(__file__).parent;G=Path(r'D:/SteamLibrary/steamapps/common/Shogun 2 Complete Edition/RemasteredCE/data');FX=W/'compile/fx'
main,_=b.readpack((G/'shaders.pack').read_bytes());over=b.read_overlay(G/'rce_campaign_night_visuals.pack');eff={**main,**over}
(W/'personal_config.h').write_text('// Empty personal configuration\n')
def compile_shader(file,entry,flags,defines):
 macros=(b.Macro*(len(defines)+1))(*[b.Macro(n.encode(),b'1') for n in defines],b.Macro(None,None));blob=C.c_void_p();errors=C.c_void_p()
 hr=b.compilefn(str(FX/file),macros,C.c_void_p(1),entry.encode(),b'ps_5_0',flags,0,C.byref(blob),C.byref(errors));msg=b.take(errors).decode(errors='replace')
 if hr<0:raise RuntimeError(msg)
 return b.take(blob),msg
original_source=eff['fx/rigidgrasscommon.hlsl']['data'].decode().replace('\r\n','\n')
variants=[]
for name,e in eff.items():
 if not name.startswith('fxc/') or not any(t in name for t in ['_rigidgrass.hlsl_ps_','_rigidgrasswet.hlsl_ps_']) or name.endswith('_ps30_shadow.fxc'):continue
 file='rigidgrasswet.hlsl' if 'rigidgrasswet.hlsl' in name else 'rigidgrass.hlsl';entry=name.split('_ps_',1)[1][:-4];defines=[] if '_default_' in name else ['ENABLE_SHADOWS','SHADOWS_HARDWARE_GATHER_5_0']
 raw=e['data'];at=raw.index(b'DXBC');old=b.assembly(raw[at:]);match=None
 for dither in ['texture','screen']:
  control_source=original_source if dither=='texture' else original_source.replace('load_jitter(input.texture_uv*64)','load_jitter(input.position.xy)')
  (FX/'rigidgrasscommon.hlsl').write_text(control_source)
  for flags in [4096,36864]:
   try:code,msg=compile_shader(file,entry,flags,defines)
   except RuntimeError:continue
   if b.normalize(b.assembly(code))==b.normalize(old):match=flags;break
  if match is not None:break
 if match is None:
  import difflib
  (W/'control-mismatch.diff').write_text('\n'.join(difflib.unified_diff(b.normalize(old),b.normalize(b.assembly(code)))))
 assert match is not None,('Control did not match',name)
 variants.append(dict(name=name,file=file,entry=entry,flags=match,defines=defines,dither=dither,offset=at,oldasm=old))
 print('Control matched',name,flush=True)
assert len(variants)==6
source=original_source
old_start=source.index('\tif (u_wet)')
old_end=source.index('\tfloat d0 =',old_start)
assert 'roughness = max(roughness, 0.9f);' in source[old_start:old_end]
assert 'metalness = 0.0f;' in source[old_start:old_end]
new_block='    // Matte grass base, before the separately controlled wet coating.\n    roughness = max(roughness, 0.9f);\n    metalness = 0.0f;\n    // Match the immutable opening-ground wetness used by terrain puddles.\n    // A later rain/clear shader permutation cannot change the ground policy.\n    bool grass_ground_wet = rce_weather_managed()\n        ? (g_rce_weather_old_material.w > 0.5f) : u_wet;\n    if (grass_ground_wet)\n        roughness *= g_rain_vegetation_roughness_multiplier;\n\n'
modified=source[:old_start]+new_block+source[old_end:]
(FX/'rigidgrasscommon.hlsl').write_text(modified)
replacements={'fx/rigidgrasscommon.hlsl':modified.encode()};reports=[]
for v in variants:
 candidate_source=modified if v['dither']=='texture' else modified.replace('load_jitter(input.texture_uv*64)','load_jitter(input.position.xy)')
 (FX/'rigidgrasscommon.hlsl').write_text(candidate_source)
 code,msg=compile_shader(v['file'],v['entry'],v['flags'],v['defines']);newasm=b.assembly(code)
 # Constant-buffer layouts, resource declarations and IO signatures must match.
 # Existing IO and constant-buffer field layouts must survive; the named
 # weather buffer is deliberately added and bound by native program reflection.
 import re
 def signature(asm):return asm[asm.index('// Input signature:'):asm.index('ps_5_0')]
 assert signature(newasm)==signature(v['oldasm']),('IO changed',v['name'])
 assert '// cbuffer rce_weather_shared' in newasm
 for field,offset in [('g_rce_weather_surface',0),('g_rce_weather_old_material',48)]:
  assert re.search(field+r';.*Offset:\s*'+str(offset)+r'\s+Size:',newasm),field
 assert 'g_rain_vegetation_roughness_multiplier' in newasm

 assert b.normalize(newasm)!=b.normalize(v['oldasm'])
 raw=eff[v['name']]['data'];replacements[v['name']]=raw[:v['offset']]+code
 asm=W/'disassembly';asm.mkdir(exist_ok=True);(asm/(Path(v['name']).name+'.before.asm')).write_text(v['oldasm']);(asm/(Path(v['name']).name+'.after.asm')).write_text(newasm)
 reports.append(dict(path=v['name'],controlMatchesInstalled=True,ioSignaturesPreserved=True,namedWeatherBufferAdded=True,compilerFlags=v['flags'],preservedDither=v['dither'],warnings=msg,beforeSha256=b.sha(raw),sha256=b.sha(replacements[v['name']])))
for n,data in replacements.items():
 p=W/'replacements'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
report=dict(status='PASS',baseRoughnessFloor=0.9,metalness=0,wetnessFromOpeningGround=True,compiledPixelVariants=6,changedAssets=list(replacements),variants=reports,unchangedVertexAndShadowShaders=True,sceneLightingSourceUnchanged=True,weatherLogicUnchanged=True,installed=False)
(W/'shader-validation.json').write_text(json.dumps(report,indent=2));print('PASS: six grass pixel variants compiled and checked; base matte preserved and wetness follows opening-ground state.')
