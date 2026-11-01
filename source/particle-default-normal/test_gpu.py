"""Render the installed smoke PS with real old/repacked normal maps, offline."""
from pathlib import Path
import sys,shutil,json
sys.dont_write_bytecode=True
W=Path(__file__).resolve().parent;R=W.parent.parent
prior=R/'work/particle-camera-stability'
shutil.copyfile(prior/'build_candidate.py',W/'build_candidate.py')
shutil.copytree(prior/'candidate-source',W/'candidate-source',dirs_exist_ok=True)
shutil.copyfile(prior/'personal_config.h',W/'personal_config.h')
# Reference shader changes only the channel reader to RGB, retaining the
# inherited decode, rotation, sunlight, ambient, alpha, fog and depth math.
p=W/'candidate-source/fx/particle_volumetric.hlsl';source=p.read_text()
old='unpack_rxbg_normal(lerp(norm1, norm2, input.pos_in_view_interpolate.w))'
assert source.count(old)==1
p.write_text(source.replace(old,'(lerp(norm1, norm2, input.pos_in_view_interpolate.w).rgb * 2.0f - 1.0f)'))
script=(prior/'test_camera_gpu.py').read_text()
script=script.split("    # Reproduce moving depth discontinuities.")[0]
script=script.replace("W=Path(sys.argv[sys.argv.index('--work')+1]) if '--work' in sys.argv else Path(__file__).resolve().parent",f"W=Path({str(W)!r})")
script=script.replace("entries,_=b.readpack(b.TARGET.read_bytes());report=json.loads((W/'candidate-validation.json').read_text());results=[]", "entries,_=b.readpack(b.TARGET.read_bytes());report=json.loads((W/'candidate-validation.json').read_text());results=[]\n"+'''
def dds_texture(raw):
    height,width=struct.unpack_from('<II',raw,12);mips=struct.unpack_from('<I',raw,28)[0]
    compressed=raw[84:88]==b'DXT5';fmt=77 if compressed else 87
    offset=128;initial=[];blobs=[]
    for mip in range(mips):
        w=max(1,width>>mip);h=max(1,height>>mip)
        pitch=max(1,(w+3)//4)*16 if compressed else w*4
        size=pitch*(max(1,(h+3)//4) if compressed else h)
        blob=C.create_string_buffer(raw[offset:offset+size]);blobs.append(blob)
        initial.append(Initial(C.cast(blob,P),pitch,size));offset+=size
    assert offset==len(raw)
    tex=P();desc=Texture(width,height,mips,1,fmt,1,0,1,8,0,0)
    dev('CreateTexture2D',(C.POINTER(Texture),C.byref(desc)),(C.POINTER(Initial),(Initial*mips)(*initial)),(C.POINTER(P),C.byref(tex)))
    srv=P();dev('CreateShaderResourceView',(P,tex),(P,None),(C.POINTER(P),C.byref(srv)));return tex,srv
original_normal=dds_texture((W.parent/'particle-code-investigation/installed/data.pack/effects/textures/default_pfx_packed_normal.dds').read_bytes())
corrected_normal=dds_texture((W/'default_pfx_packed_normal.dds').read_bytes())
''')
script=script.replace("old=shader(before[before.index(b'DXBC'):],'Pixel');new=shader(after[after.index(b'DXBC'):],'Pixel')", "old=shader(before[before.index(b'DXBC'):],'Pixel');new=shader(after[after.index(b'DXBC'):],'Pixel')")
script=script.replace("maxerror=0;visible=0;nonzero=0;fingerprints=set()", "maxerror=0;visible=0;nonzero=0;fingerprints=set();baseline_error=0;alpha_error=0;changed_pixels=0")
script=script.replace("    for case in cases:", "    for scale,rot in itertools.product((.01,.03,.1,.3,1,3,8,16), (0,.7,2.4)):\n        cases.append(dict(terms=9,probe=.5,animated=False,fog=0,depth=0,distance=120,uvscale=scale,rotation=rot))\n    for case in cases:")
script=script.replace(".37,.4,1, .8", ".37,case.get('rotation',.4),1, .8")
script=script.replace("upload(vcb,struct.pack('<16f',*values));a=readpixels(old);c=readpixels(new)", '''upload(vcb,struct.pack('<16f',*values))
        slot=bindings['s_normalmap_texture'][1]
        ctx('PSSetShaderResources',(U,slot),(U,1),(C.POINTER(P),(P*1)(original_normal[1])))
        a=readpixels(new);wrong=readpixels(old)
        ctx('PSSetShaderResources',(U,slot),(U,1),(C.POINTER(P),(P*1)(corrected_normal[1])))
        c=readpixels(old)
        baseline_error=max(baseline_error,max(abs(x-y) for x,y in zip(a,wrong)))
        alpha_error=max(alpha_error,max(abs(x-y) for x,y in zip(c[3::4],wrong[3::4])))
        changed_pixels+=sum(abs(x-y)>0.001 for x,y in zip(c,wrong))''')
# BC3 colour endpoint/interpolation rounding differs between WARP/hardware and
# the byte decoder used for the uncompressed texture. Bound that quantization
# effect explicitly; alpha/coverage must still match bit-for-bit.
script=script.replace("abs(x-y)<=2e-5+2e-5*abs(x)","abs(x-y)<=0.005+0.005*abs(x)")
script=script.replace("    print(results[-1],flush=True)","    results[-1].update(originalWrongChannelMaxError=baseline_error,alphaError=alpha_error,changedComponents=changed_pixels)\n    assert alpha_error==0 and changed_pixels>0 and baseline_error>0.001\n    print(results[-1],flush=True)")
script+='''
out=dict(status='PASS_D3D11_HARDWARE' if hardware else 'PASS_D3D11_WARP',actualInstalledPixelShaders=True,realBC3SourceAndRepackedBGRA8=True,reference='Same shader with RGB read, retaining inherited decode; corrected texture rendered through unchanged installed RAB shader',results=results,cases=sum(x['cases'] for x in results),scope='Offline D3D11 rendering. Proves correct normal-channel sampling and unchanged alpha, not live flashing resolution.')
(W/('gpu-validation-hardware.json' if hardware else 'gpu-validation.json')).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
'''
sys.path.insert(0,str(W));import build_candidate as b
b.FX=W/'candidate-source/fx'
entries,_=b.readpack(b.TARGET.read_bytes());entries.update(b.read_overlay(Path(r'D:/SteamLibrary/steamapps/common/Shogun 2 Complete Edition/RemasteredCE/data/rce_campaign_night_visuals.pack')))
variants=[]
for entry in ['ps30_volumetric_particle','ps30_volumetric_particle_alpha']:
 name='fxc/dx11_sm_5_0_default_particle.hlsl_ps_'+entry+'.fxc'
 code,warnings=b.compile_shader('particle.hlsl',entry,'ps',4096)
 original=entries[name]['data'];offset=original.index(b'DXBC')
 target=W/'replacements'/name;target.parent.mkdir(exist_ok=True,parents=True);target.write_bytes(original[:offset]+code)
 variants.append(dict(path=name))
(W/'candidate-validation.json').write_text(json.dumps(dict(variants=variants)))
# Read effective override PS rather than the inactive copy in shaders.pack.
script=script.replace("if b.OVERLAY:entries.update(b.read_overlay(b.OVERLAY))", "entries.update(b.read_overlay(Path(r'D:/SteamLibrary/steamapps/common/Shogun 2 Complete Edition/RemasteredCE/data/rce_campaign_night_visuals.pack')))")
exec(compile(script,str(W/'gpu_fixture.py'),'exec'),globals())
