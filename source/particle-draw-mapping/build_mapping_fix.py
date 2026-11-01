"""Stage a bounded native emitter-index fix; never install or launch anything."""
from pathlib import Path
import sys,struct,json,base64,hashlib,shutil
sys.dont_write_bytecode=True
sys.path.insert(0,r'F:/Codex/Shogun2-CE/work/disasm_runtime')
import pefile,capstone
W=Path(__file__).resolve().parent;R=W.parent.parent
sha=lambda x:hashlib.sha256(x).hexdigest()
cfg=json.loads((R/'source/current-installer.json').read_text());assert cfg['version']=='0.1.61-preview'
m=json.loads((R/'work/release-061/manifest.json').read_text());raw=bytearray((Path(cfg['ceRoot'])/'empire.retail.x64.dll').read_bytes());assert sha(raw)==m['engineSourceSha256']
for op in m['enginePatches']:
 data=base64.b64decode(op['data']);raw[op['offset']:op['offset']+len(data)]=data
assert sha(raw)==m['engineEditedSha256']
p=pefile.PE(data=raw,fast_load=True)
helper=json.loads((R/'work/release-061/helper.json').read_text())
payload=bytearray(base64.b64decode(helper['payload']))
# build_controller.py aligns the preserved 0.1.32 payload to 0x5000;
# 0x4884..0x5000 is explicit zero-fill, outside every existing code/data object.
prefix=base64.b64decode(json.loads((R/'work/release-032/helper.json').read_text())['payload'])
assert len(prefix)==0x4884 and payload[:len(prefix)]==prefix
slot=0x4890;start=helper['rva']+slot
buf=bytearray();labels={};branches=[]
def emit(h):buf.extend(bytes.fromhex(h))
def label(n):labels[n]=len(buf)
def branch(op,n):emit(op);branches.append((len(buf),n));emit('00')
# The three callers all hold source in RBX and the actual bucket entry in RDI.
# RCX(mesh), R8(state-change), all nonvolatile registers and RSP stay intact.
emit('4c8b4b58') # mov r9,[rbx+58] -- globally sorted emitter vector
emit('4c8b17') # mov r10,[rdi] -- emitter whose visibility was just checked
emit('4d3914d1');branch('74','draw') # cmp [r9+rdx*8],r10
emit('85d2');branch('74','next')
emit('4d3954d1f8');branch('75','next') # adjacent previous slot
emit('ffca');branch('eb','draw')
label('next');emit('8d4201');emit('3b4354');branch('73','scan')
emit('4d3914c1');branch('75','scan')
emit('89c2');branch('eb','draw')
label('scan');emit('31d2')
label('loop');emit('3b5354');branch('73','missing')
emit('4d3914d1');branch('74','draw')
emit('ffc2');branch('eb','loop')
label('draw');emit('488b01ff a058010000') # tail-dispatch original mesh virtual +158
label('missing');emit('c3') # bounded failure for an absent stale entry
for at,n in branches:
 disp=labels[n]-(at+1);assert -128<=disp<128;buf[at]=disp&255
assert slot+len(buf)<=0x5000<helper['writableDataOffset']
assert payload[len(prefix):0x5000]==bytes(0x5000-len(prefix))
assert all(not (a<start+len(buf) and start<b) for a,b,_ in helper['unwind'])
payload[slot:slot+len(buf)]=buf
helper['payload']=base64.b64encode(payload).decode()
writes=[]
def put(at,data,reason):
 before=bytes(raw[at:at+len(data)]);writes.append(dict(offset=at,before=before.hex(),data=data.hex(),reason=reason));raw[at:at+len(data)]=data
sites=[0x1a9dfec,0x1ac0609,0x1ac0735]
for site in sites:
 at=p.get_offset_from_rva(site);assert raw[at:at+6]==bytes.fromhex('ff9058010000')
 put(at,b'\xe8'+struct.pack('<i',start-site-5)+b'\x90','Resolve emitter identity before native draw callback')
m['enginePatches'] += [dict(offset=o['offset'],data=base64.b64encode(bytes.fromhex(o['data'])).decode()) for o in writes]
m['engineEditedSha256']=sha(raw)
(W/'candidate-engine-edited.bin').write_bytes(raw);(W/'candidate-manifest.json').write_text(json.dumps(m,separators=(',',':')))
(W/'candidate-helper.json').write_text(json.dumps(helper,separators=(',',':')))
(W/'mapping-layout.json').write_text(json.dumps(dict(startRva=start,endRva=start+len(buf),labels=labels,callSites=sites,writes=writes,leaf=True,stackBytes=0),indent=2))
shutil.copyfile(R/'work/unit-deselection/PePatchCandidate.cs',W/'PePatchCandidate.cs')
(W/'Emit-Candidate.ps1').write_text((R/'work/unit-drag-refresh/Emit-Candidate.ps1').read_text().replace('release-057','release-061'))
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64)
(W/'mapping-adapter.asm').write_text('\n'.join(f'{i.address:016x} {i.mnemonic} {i.op_str}' for i in md.disasm(bytes(buf),p.OPTIONAL_HEADER.ImageBase+start)))
print('Staged',len(buf),'byte leaf adapter at',hex(start),'and three original virtual call sites; no game files changed.')
