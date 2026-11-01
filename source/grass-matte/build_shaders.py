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
source=eff['fx/rigidgrasscommon.hlsl']['data'].decode().replace('\r\n','\n')
anchor='\tfloat d0 = 1.0;// dot(normalize(input.face_normal), input.camera_direction_distance.xyz);';assert source.count(anchor)==1
patch='''    // Grass is a matte dielectric in both dry and wet material permutations.
    // Limit narrow directional highlights without changing scene lighting.
    roughness = max(roughness, 0.9f);
    metalness = 0.0f;

'''
modified=source.replace(anchor,patch+anchor);(FX/'rigidgrasscommon.hlsl').write_text(modified)
replacements={'fx/rigidgrasscommon.hlsl':modified.encode()};reports=[]
for v in variants:
 candidate_source=modified if v['dither']=='texture' else modified.replace('load_jitter(input.texture_uv*64)','load_jitter(input.position.xy)')
 (FX/'rigidgrasscommon.hlsl').write_text(candidate_source)
 code,msg=compile_shader(v['file'],v['entry'],v['flags'],v['defines']);newasm=b.assembly(code)
 # Constant-buffer layouts, resource declarations and IO signatures must match.
 assert b.interface(newasm)==b.interface(v['oldasm']),('Interface changed',v['name'])
 assert b.normalize(newasm)!=b.normalize(v['oldasm'])
 raw=eff[v['name']]['data'];replacements[v['name']]=raw[:v['offset']]+code
 asm=W/'disassembly';asm.mkdir(exist_ok=True);(asm/(Path(v['name']).name+'.before.asm')).write_text(v['oldasm']);(asm/(Path(v['name']).name+'.after.asm')).write_text(newasm)
 reports.append(dict(path=v['name'],controlMatchesInstalled=True,interfaceUnchanged=True,compilerFlags=v['flags'],preservedDither=v['dither'],warnings=msg,beforeSha256=b.sha(raw),sha256=b.sha(replacements[v['name']])))
for n,data in replacements.items():
 p=W/'replacements'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
report=dict(status='PASS',roughnessFloor=0.9,metalness=0,compiledPixelVariants=6,changedAssets=list(replacements),variants=reports,unchangedVertexAndShadowShaders=True,sceneLightingSourceUnchanged=True,weatherLogicUnchanged=True,installed=False)
(W/'shader-validation.json').write_text(json.dumps(report,indent=2));print('PASS: six grass pixel variants compiled and interface-checked; vertex, shadow and scene-lighting code untouched.')
