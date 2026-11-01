from pathlib import Path
import sys,json,struct,base64,hashlib,shutil
sys.dont_write_bytecode=True
sys.path.insert(0,'F:/Codex/Shogun2-CE/work/disasm_runtime')
import pefile
W=Path(__file__).resolve().parent;R=W.parent.parent
cfg=json.loads((R/'source/current-installer.json').read_text());assert cfg['version']=='0.1.66-preview'
assert json.loads((W/'native-validation.json').read_text())['status']=='PASS'
assert len(json.loads((W/'threshold-references.json').read_text()))==1
m=json.loads((R/'work/release-066/manifest.json').read_text());helper=json.loads((R/'work/release-066/helper.json').read_text())
sha=lambda b:hashlib.sha256(b).hexdigest()
raw=bytearray((Path(cfg['ceRoot'])/'empire.retail.x64.dll').read_bytes());assert sha(raw)==m['engineSourceSha256']
for op in m['enginePatches']:
 data=base64.b64decode(op['data']);raw[op['offset']:op['offset']+len(data)]=data
assert sha(raw)==m['engineEditedSha256'];p=pefile.PE(data=raw,fast_load=True)
writes=[]
for rva,before,after,why in [
 (0x1b2cc48,b'\x18',b'\x20','Normalize particle GPU ticks by timestamp frequency, not whole-frame GPU cost'),
 (0x1b2ccc7,bytes.fromhex('488b8bb8000000'),bytes.fromhex('31ff9090909090'),'Hold resolution until a fresh completed particle timing is available'),
 (0x2e7b750,struct.pack('<d',.33),struct.pack('<d',.0033),'Absolute3.3ms particle GPU budget in the existing adaptive controller')]:
 at=p.get_offset_from_rva(rva);assert raw[at:at+len(before)]==before
 raw[at:at+len(after)]=after
 writes.append(dict(rva=rva,offset=at,before=before.hex(),data=after.hex(),reason=why))
 m['enginePatches'].append(dict(offset=at,data=base64.b64encode(after).decode()))
m['engineEditedSha256']=sha(raw)
(W/'candidate-engine-edited.bin').write_bytes(raw);(W/'candidate-manifest.json').write_text(json.dumps(m,separators=(',',':')))
(W/'candidate-helper.json').write_text(json.dumps(helper,separators=(',',':')))
(W/'layout.json').write_text(json.dumps(dict(writes=writes,helperUnchanged=True,stackAndUnwindUnchanged=True),indent=2))
for name in ['PePatchCandidate.cs']:shutil.copyfile(R/'work/particle-sorted-stream'/name,W/name)
(W/'Emit-Candidate.ps1').write_text((R/'work/particle-sorted-stream/Emit-Candidate.ps1').read_text().replace('release-065','release-066'))
print('Staged16bytes across3guarded writes; helper, shaders, archives and anti-flashing ordering unchanged.')
