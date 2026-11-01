"""Stage only the native branch that prevents emitter-group coalescing."""
from pathlib import Path
import json,base64,hashlib,struct,shutil,sys
sys.dont_write_bytecode=True
sys.path.insert(0,r'F:/Codex/Shogun2-CE/work/disasm_runtime');import pefile
R=Path(__file__).resolve().parent.parent.parent;W=R/'work/particle-overlap-order';W.mkdir(exist_ok=True)
cfg=json.loads((R/'source/current-installer.json').read_text());assert cfg['version']=='0.1.63-preview'
m=json.loads((R/'work/release-063/manifest.json').read_text())
raw=bytearray((Path(cfg['ceRoot'])/'empire.retail.x64.dll').read_bytes());sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(raw)==m['engineSourceSha256']
for op in m['enginePatches']:
 b=base64.b64decode(op['data']);raw[op['offset']:op['offset']+len(b)]=b
assert sha(raw)==m['engineEditedSha256']
p=pefile.PE(data=raw,fast_load=True);site=0x1abff30;at=p.get_offset_from_rva(site);before=bytes(raw[at:at+6])
assert before==bytes.fromhex('0f84c7000000')
after=b'\xe9'+struct.pack('<i',0x1abfffd-site-5)+b'\x90';raw[at:at+6]=after
write=dict(offset=at,before=before.hex(),data=after.hex(),reason='Give each transparent emitter an independent native distance-sort key; do not coalesce into averaged buckets')
m['enginePatches'].append(dict(offset=at,data=base64.b64encode(after).decode()));m['engineEditedSha256']=sha(raw)
(W/'candidate-engine-edited.bin').write_bytes(raw);(W/'candidate-manifest.json').write_text(json.dumps(m,separators=(',',':')))
(W/'layout.json').write_text(json.dumps(dict(writes=[write],siteRva=site,targetRva=0x1abfffd,noNewCode=True,noStackOrUnwindChange=True),indent=2))
for name in ['helper.json']:shutil.copyfile(R/'work/release-063'/name,W/'candidate-helper.json')
shutil.copyfile(R/'work/unit-deselection/PePatchCandidate.cs',W/'PePatchCandidate.cs')
(W/'Emit-Candidate.ps1').write_text((R/'work/unit-drag-refresh/Emit-Candidate.ps1').read_text().replace('release-057','release-063'))
shutil.copyfile(R/'work/particle-code-investigation/mapping-layout.json',W/'mapping-layout.json')
shutil.copyfile(R/'work/particle-code-investigation/test_mapping_fix.py',W/'test_mapping_fix.py')
print('Staged six-byte strict emitter-order candidate; installed game unchanged.')
