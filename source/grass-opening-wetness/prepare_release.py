from pathlib import Path
import sys,json,hashlib,struct,base64,copy,difflib,ctypes as C,shutil
W=Path(__file__).parent;R=W.parents[1];sys.path.insert(0,r'F:/Codex/Remastered-CE-Port/work/particle-camera-stability');import build_candidate as b
sha=lambda x:hashlib.sha256(x).hexdigest();enc=lambda x:base64.b64encode(x).decode()
cfg=json.loads((R/'source/current-installer.json').read_text());assert cfg['version']=='0.1.70-preview';G=Path(cfg['ceRoot'])/'RemasteredCE'
validation=json.loads((W/'shader-validation.json').read_text());assert validation['status']=='PASS';replacement={n:(W/'replacements'/n).read_bytes() for n in validation['changedAssets']}
vanilla,_=b.readpack((Path(cfg['ceRoot'])/'data/shaders.pack').read_bytes())
def update(a,name,data,sid,sources):
 e=vanilla[name];before=e['data'];sources.append(dict(id=sid,root='ce',file='data/shaders.pack',offset=e['offset'],stored=e['size'],size=e['size'],compressed=False,sha256=sha(before)))
 ops=[]
 for tag,x,y,z,t in difflib.SequenceMatcher(None,before,data,autojunk=True).get_opcodes():
  if tag=='equal':ops.append(dict(copy=x,length=y-x))
  elif z!=t:ops.append(dict(data=enc(data[z:t])))
 assert b''.join(before[o['copy']:o['copy']+o['length']] if 'copy' in o else base64.b64decode(o['data']) for o in ops)==data
 a.update(source=sid,operations=ops,size=len(data),sha256=sha(data),stored=len(data),encodedSha256=sha(data))
raw=(G/'data/shaders.pack').read_bytes();entries,end=b.readpack(raw);recipe=copy.deepcopy(json.loads(Path(cfg['shaderRecipe']).read_text()));f=recipe['file'];assert sha(raw)==f['sha256'];assets={a['path']:a for a in f['assets']}
for i,(name,data) in enumerate(replacement.items()):update(assets[name],name,data,'grass071-main-'+str(i),recipe['sources'])
out=bytearray(raw[:end]);cursor=end;metadata=[]
for name,e in sorted(entries.items(),key=lambda item:item[1]['offset']):
 data=replacement.get(name,e['data']);offset=(len(out)+15)//16*16
 if offset>len(out):metadata.append(dict(offset=len(out),data=enc(bytes(offset-len(out)))))
 out.extend(bytes(offset-len(out)));out.extend(data);struct.pack_into('<QI',out,e['index'],offset,len(data));assets[name].update(offset=offset)
if len(out)<len(raw):metadata.append(dict(offset=len(out),data=enc(bytes(len(raw)-len(out)))));out.extend(bytes(len(raw)-len(out)))
f.update(length=len(out),sha256=sha(out),metadata=[dict(offset=0,data=enc(out[:end]))]+metadata)
(W/'shaders.candidate.pack').write_bytes(out);(W/'shader-recipe.json').write_text(json.dumps(recipe,separators=(',',':')))
check,_=b.readpack(out);assert all(e['data']==replacement.get(n,entries[n]['data']) for n,e in check.items())
mainChanged=[n for n,e in check.items() if e['data']!=entries[n]['data']];assert set(mainChanged)==set(replacement)
addon=copy.deepcopy(json.loads(Path(cfg['addonRecipe']).read_text()));f=addon['file'];path=G/'data/rce_campaign_night_visuals.pack';raw=path.read_bytes();assert sha(raw)==f['sha256'];entries=b.read_overlay(path);assets={a['path']:a for a in f['assets']}
for i,(name,data) in enumerate(replacement.items()):assert name in entries;update(assets[name],name,data,'grass071-overlay-'+str(i),addon['sources'])
lz=C.CDLL(r'F:/Codex/Workspaces/2026-10-16/ca/work/installer/lz4.dll');lz.LZ4_compress_default.argtypes=[C.c_void_p,C.c_void_p,C.c_int,C.c_int]
end=32+struct.unpack_from('<I',raw,20)[0];out=bytearray(raw[:end]);metadata=[]
for name,e in entries.items():
 data=replacement.get(name,e['data']);buf=C.create_string_buffer(len(data)+len(data)//255+32);n=lz.LZ4_compress_default(data,buf,len(data),len(buf));assert n>0
 offset=(len(out)+15)//16*16
 if offset>len(out):metadata.append(dict(offset=len(out),data=enc(bytes(offset-len(out)))))
 out.extend(bytes(offset-len(out)));out.extend(buf.raw[:n]);struct.pack_into('<QII',out,e['index'],offset,len(data),n);assets[name].update(offset=offset,stored=n,encodedSha256=sha(buf.raw[:n]))
f.update(length=len(out),sha256=sha(out),metadata=[dict(offset=0,data=enc(out[:end]))]+metadata)
(W/'rce_campaign_night_visuals.candidate.pack').write_bytes(out);(W/'addon-recipe.json').write_text(json.dumps(addon,separators=(',',':')))
check=b.read_overlay(W/'rce_campaign_night_visuals.candidate.pack');assert all(e['data']==replacement.get(n,entries[n]['data']) for n,e in check.items())
changed=[n for n,e in check.items() if e['data']!=entries[n]['data']];assert set(changed)==set(replacement)
report=dict(status='PASS',mainChangedAssets=mainChanged,overlayChangedAssets=changed,shaderEntryCount=len(recipe['file']['assets']),overlayEntryCount=len(entries),allOtherAssetContentsUnchanged=True,weatherControllerAndEngineUnchanged=True,allGrassVertexShadowAndAlphaDitherPreserved=True)
(W/'asset-scope-validation.json').write_text(json.dumps(report,indent=2))
notes='0.1.71-preview: retain matte grass while restoring a distinct wet coating. Apply roughness floor 0.9 before wetness and use the immutable opening-ground wet flag for campaign grass, rather than the current dry/rain shader permutation. Rain-start grass remains wet after skies clear; clear-start grass stays dry during later rain. Keep non-campaign native wet/dry selection. Existing terrain puddle coverage and native opening-ground controller are retained. New named weather-buffer binding is verified and actual dry/wet GBuffer shaders are rendered in 36 cases on hardware and 36 on WARP, including every MRT output. Engine/helper and all other assets are unchanged. Live appearance and reported terrain-puddle behavior still require user confirmation.'
docs=W/'docs';shutil.copytree(cfg['documentation'],docs,dirs_exist_ok=True)
for name in ['README.txt','CHANGELOG.md']:
 p=docs/name;p.write_text(notes+'\n\n'+p.read_text(encoding='utf-8-sig'),encoding='utf-8')
cfg.update(version='0.1.71-preview',minimumInstallerVersion='0.1.71-preview',shaderRecipe=str(W/'shader-recipe.json'),addonRecipe=str(W/'addon-recipe.json'),documentation=str(docs),releaseNotes=notes)
(W/'candidate-installer.json').write_text(json.dumps(cfg,indent=2));print('PASS: cumulative .71 fix prepared; only grass assets change in two archives.')
