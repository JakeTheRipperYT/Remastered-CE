"""Remove only the superseded0.1.65 helper and its metadata."""
from pathlib import Path
import sys,json,base64,hashlib,struct,re,shutil
sys.dont_write_bytecode=True
sys.path.insert(0,'F:/Codex/Shogun2-CE/work/disasm_runtime');import pefile
W=Path(__file__).resolve().parent;R=W.parent.parent
cfg=json.loads((R/'source/current-installer.json').read_text());assert cfg['version']=='0.1.67-preview'
m=json.loads((R/'work/release-067/manifest.json').read_text());h=json.loads((R/'work/release-067/helper.json').read_text())
old=json.loads((R/'work/particle-overlap-batching/layout.json').read_text());live=json.loads((R/'work/particle-sorted-stream/layout.json').read_text())
lo,hi=old['startRva'],old['endRva'];a=lo-h['rva'];b=hi-h['rva'];assert b-a==324 and a==0x4900
payload=bytearray(base64.b64decode(h['payload']));before=bytes(payload)
p=pefile.PE(str(Path(cfg['ceRoot'])/'RemasteredCE/CE.dll'),fast_load=True)
assert hashlib.sha256(p.__data__).hexdigest()==m['engineFinalSha256']
assert p.get_data(lo,hi-lo)==payload[a:b]
site=live['callSite'];code=p.get_data(site,6);assert code[0]==0xe8
assert site+5+struct.unpack_from('<i',code,1)[0]==live['exports']['BatchAdapter']
incoming=[]
for sec in p.sections:
 if not sec.Characteristics&0x20000000:continue
 data=sec.get_data()
 for match in re.finditer(rb'[\xe8\xe9]',data):
  off=match.start()
  if off+5>len(data):continue
  src=sec.VirtualAddress+off;dest=src+5+struct.unpack_from('<i',data,off+1)[0]
  if lo<=dest<hi and not lo<=src<hi:incoming.append([hex(src),hex(dest)])
assert not incoming
# Injected helpers use explicit relocation/fixup lists. Check every remaining
# RIP-relative reference before removing the old helper's own native-call fixup.
removed_fixups=[x for x in h['fixups'] if a<=x<b]
for x in h['fixups']:
 if x in removed_fixups:continue
 dest=h['rva']+x+4+struct.unpack_from('<i',payload,x)[0]
 assert not lo<=dest<hi,(hex(x),hex(dest))
removed_rows=[row for row in h['unwind'] if lo<=row[0]<hi]
assert removed_rows==old['unwind']
retained_rows=[row for row in h['unwind'] if row not in removed_rows]
for begin,end,info in retained_rows:
 assert not lo<=info<hi and not (begin<hi and end>lo)
 off=info-h['rva'];head=payload[off:off+4]
 if head[0]>>3&4:
  tail=off+4+((head[2]+1)&~1)*2;chain=struct.unpack_from('<III',payload,tail)
  assert not any(lo<=x<hi for x in chain)
payload[a:b]=bytes(b-a)
assert payload[:a]==before[:a] and payload[b:]==before[b:]
h['payload']=base64.b64encode(payload).decode();h['fixups']=[x for x in h['fixups'] if x not in removed_fixups];h['unwind']=retained_rows
raw=bytearray((Path(cfg['ceRoot'])/'empire.retail.x64.dll').read_bytes());assert hashlib.sha256(raw).hexdigest()==m['engineSourceSha256']
for op in m['enginePatches']:
 data=base64.b64decode(op['data']);raw[op['offset']:op['offset']+len(data)]=data
assert hashlib.sha256(raw).hexdigest()==m['engineEditedSha256']
(W/'candidate-engine-edited.bin').write_bytes(raw);(W/'candidate-manifest.json').write_text(json.dumps(m,separators=(',',':')));(W/'candidate-helper.json').write_text(json.dumps(h,separators=(',',':')))
report=dict(status='PASS',removedStartRva=lo,removedEndRva=hi,removedBytes=b-a,removedFixups=removed_fixups,removedUnwindRows=removed_rows,remainingHelperBytesUnchanged=True,editedEngineUnchanged=True,externalDirectBranches=[],activeBatchHook=live['exports']['BatchAdapter'])
(W/'cleanup-validation.json').write_text(json.dumps(report,indent=2))
for name in ['PePatchCandidate.cs']:shutil.copyfile(R/'work/particle-dynres-controller'/name,W/name)
(W/'Emit-Candidate.ps1').write_text((R/'work/particle-dynres-controller/Emit-Candidate.ps1').read_text().replace('release-066','release-067'))
# Existing tests execute the retained current helpers; use their unchanged RVAs.
for name in ['test_stream.py','test_unwind.py','layout.json']:
 shutil.copyfile(R/'work/particle-sorted-stream'/name,W/name)
print(json.dumps(report,indent=2))
