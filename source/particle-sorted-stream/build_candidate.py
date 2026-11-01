from pathlib import Path
import sys,os,subprocess,struct,json,base64,hashlib,shutil
sys.dont_write_bytecode=True
sys.path.insert(0,r'F:/Codex/Shogun2-CE/work/disasm_runtime')
import pefile,capstone
W=Path(__file__).resolve().parent;R=W.parent.parent
cfg=json.loads((R/'source/current-installer.json').read_text());assert cfg['version']=='0.1.65-preview'
manifest=json.loads((R/'work/release-065/manifest.json').read_text());helper=json.loads((R/'work/release-065/helper.json').read_text())
sha=lambda b:hashlib.sha256(b).hexdigest()
raw=bytearray((Path(cfg['ceRoot'])/'empire.retail.x64.dll').read_bytes());assert sha(raw)==manifest['engineSourceSha256']
for op in manifest['enginePatches']:
 data=base64.b64decode(op['data']);raw[op['offset']:op['offset']+len(data)]=data
assert sha(raw)==manifest['engineEditedSha256'];p=pefile.PE(data=raw,fast_load=True)
vc=sorted(Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC').iterdir(),key=lambda x:tuple(map(int,x.name.split('.'))))[-1]/'bin/Hostx64/x64'
env=os.environ.copy();env['TEMP']=env['TMP']='F:/Codex/Temp'
def run(args):subprocess.run([str(a) for a in args],cwd=W,env=env,check=True)
(W/'merge.def').write_text('EXPORTS\nPrepareSource\nRenderStream\nBatchAdapter\nAllocate\nRelease\nClear\nSort\n')
run([vc/'cl.exe','/nologo','/c','/O1','/GS-','/Gs16384','/GR-','/EHs-c-','/Zl','/Oi','/Fo'+str(W/'merge.obj'),W/'stream.cpp'])
run([vc/'ml64.exe','/nologo','/c','/Fo'+str(W/'adapter.obj'),W/'adapter.asm'])
run([vc/'link.exe','/nologo','/dll','/noentry','/nodefaultlib','/machine:x64','/base:0x180000000','/out:'+str(W/'merge.dll'),'/def:'+str(W/'merge.def'),W/'merge.obj',W/'adapter.obj'])
module=pefile.PE(str(W/'merge.dll'));assert not getattr(module,'DIRECTORY_ENTRY_IMPORT',[])
assert not [e for block in getattr(module,'DIRECTORY_ENTRY_BASERELOC',[]) for e in block.entries if e.type]
section=next(s for s in module.sections if s.Name.startswith(b'.text'));origin=section.VirtualAddress
code=bytearray(section.get_data()[:section.Misc_VirtualSize]);exports={e.name.decode():e.address for e in module.DIRECTORY_ENTRY_EXPORT.symbols}
payload=bytearray(base64.b64decode(helper['payload']));slot=0x9300;start=helper['rva']+slot
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);md.detail=True
for ins in md.disasm(code,origin):
 assert not any(o.type==capstone.CS_OP_MEM and o.mem.base==capstone.x86.X86_REG_RIP for o in ins.operands) or exports['Allocate']<=ins.address<exports['Allocate']+7,'Unexpected constant reference'
for name,dest in [('Allocate',0x19fe50),('Release',0x19fe10),('Clear',0x1ac35a0),('Sort',0x1a9d1f0)]:
 off=exports[name]-origin
 if name=='Allocate':
  assert code[off:off+7]==bytes.fromhex('488b1500000000')
  struct.pack_into('<i',code,off+3,0x2e3fd98-(start+off+7));helper['fixups'].append(slot+off+3);off+=7
 assert code[off:off+5]==bytes.fromhex('e900000000')
 struct.pack_into('<i',code,off+1,dest-(start+off+5));helper['fixups'].append(slot+off+1)

unwind=[];info_offsets={};info_sizes={}
for entry in module.DIRECTORY_ENTRY_EXCEPTION:
 rva=entry.struct.UnwindData
 if rva in info_offsets:continue
 info=module.get_data(rva,4);assert info[0]&7==1 and info[0]>>3 in (0,4),'Unexpected unwind handler'
 size=4+((info[2]+1)&~1)*2+(12 if info[0]>>3==4 else 0)
 while len(code)%4:code.append(0)
 info_offsets[rva]=len(code);info_sizes[rva]=size;code.extend(module.get_data(rva,size))
for rva,offset in info_offsets.items():
 if code[offset]>>3==4:
  at=offset+info_sizes[rva]-12;a,b,c=struct.unpack_from('<III',code,at)
  assert c in info_offsets
  struct.pack_into('<III',code,at,start+a-origin,start+b-origin,start+info_offsets[c])
for entry in module.DIRECTORY_ENTRY_EXCEPTION:
 row=[start+entry.struct.BeginAddress-origin,start+entry.struct.EndAddress-origin,start+info_offsets[entry.struct.UnwindData]]
 helper['unwind'].append(row);unwind.append(row)
assert slot+len(code)<=0xa000
assert payload[slot:slot+len(code)]==bytes(len(code))
payload[slot:slot+len(code)]=code;helper['payload']=base64.b64encode(payload).decode();helper['unwind'].sort(key=lambda row:row[0])
assert all(a[1]<=b[0] for a,b in zip(helper['unwind'],helper['unwind'][1:]))
site=0x1b0ebc0;at=p.get_offset_from_rva(site);before=bytes(raw[at:at+6]);assert before==bytes.fromhex('e81b9ec30190')
target=start+exports['BatchAdapter']-origin;after=b'\xe8'+struct.pack('<i',target-site-5)+b'\x90';raw[at:at+6]=after
write=dict(offset=at,before=before.hex(),data=after.hex(),reason='Stream sorted source lists directly after gathering')
writes=[write]
manifest['enginePatches'].append(dict(offset=at,data=base64.b64encode(after).decode()))
site2=0x1aea3f0;at2=p.get_offset_from_rva(site2);before2=bytes(raw[at2:at2+5]);assert before2==bytes.fromhex('48895c2410')
target2=start+exports['PrepareSource']-origin;after2=b'\xe9'+struct.pack('<i',target2-site2-5)
raw[at2:at2+5]=after2;writes.append(dict(offset=at2,before=before2.hex(),data=after2.hex(),reason='Prepare sorted source and one empty marker without emitter buckets'))
manifest['enginePatches'].append(dict(offset=at2,data=base64.b64encode(after2).decode()));manifest['engineEditedSha256']=sha(raw)
(W/'candidate-engine-edited.bin').write_bytes(raw);(W/'candidate-manifest.json').write_text(json.dumps(manifest,separators=(',',':')));(W/'candidate-helper.json').write_text(json.dumps(helper,separators=(',',':')))
layout=dict(writes=writes,slot=slot,startRva=start,endRva=start+len(code),exports={n:start+a-origin for n,a in exports.items()},unwind=unwind,callSite=site,afterSort=True,sourcePrepareSite=0x1aea3f0)
(W/'layout.json').write_text(json.dumps(layout,indent=2))
(W/'merge.asm').write_text('\n'.join(f'{i.address:016x} {i.mnemonic} {i.op_str}' for i in md.disasm(bytes(code[:section.Misc_VirtualSize]),p.OPTIONAL_HEADER.ImageBase+start)))
shutil.copyfile(R/'work/unit-deselection/PePatchCandidate.cs',W/'PePatchCandidate.cs')
(W/'Emit-Candidate.ps1').write_text((R/'work/unit-drag-refresh/Emit-Candidate.ps1').read_text().replace('release-057','release-065'))
for name in ['mapping-layout.json','test_mapping_fix.py']:shutil.copyfile(R/'work/particle-overlap-order'/name,W/name)
print('Staged sorted adjacent-run merger:',len(code),'bytes in existing RX padding; no game changes.')
