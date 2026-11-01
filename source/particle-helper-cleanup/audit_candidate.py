from pathlib import Path
import sys,json,struct,bisect
sys.path.insert(0,'F:/Codex/Shogun2-CE/work/disasm_runtime')
import pefile,numpy as np,capstone
W=Path(__file__).resolve().parent;R=W.parent.parent
old=pefile.PE('D:/SteamLibrary/steamapps/common/Shogun 2 Complete Edition/RemasteredCE/CE.dll',fast_load=True)
new=pefile.PE(str(W/'CE.campaign-night-candidate.dll'),fast_load=True)
for p in [old,new]:p.parse_data_directories([3])
layout=json.loads((W/'cleanup-validation.json').read_text());lo=layout['removedStartRva'];hi=layout['removedEndRva'];base=old.OPTIONAL_HEADER.ImageBase
removed={tuple(row) for row in layout['removedUnwindRows']}
rows=lambda p:{(e.struct.BeginAddress,e.struct.EndAddress,e.struct.UnwindData) for e in p.DIRECTORY_ENTRY_EXCEPTION}
assert rows(new)==rows(old)-removed
assert new.OPTIONAL_HEADER.CheckSum==new.generate_checksum()
for sec in old.sections:
 name=sec.Name.rstrip(b'\0');target=next(s for s in new.sections if s.Name==sec.Name)
 if name in [b'.rcedata']:continue # Rebuilt combined runtime-function table.
 a=bytearray(sec.get_data());b=target.get_data()
 if sec.VirtualAddress<=lo<sec.VirtualAddress+sec.Misc_VirtualSize:
  offset=lo-sec.VirtualAddress;assert b[offset:offset+hi-lo]==bytes(hi-lo);a[offset:offset+hi-lo]=bytes(hi-lo)
 assert bytes(a)==b,name
# Search all pointer-sized byte alignments for absolute references into the old
# helper. Also inspect actual RIP-relative instructions, not just call opcodes.
abs_refs=[];relative_refs=[];unowned_candidates=[]
entries=sorted(rows(old));starts=[x[0] for x in entries]
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);md.detail=True
for sec in old.sections:
 data=sec.get_data()
 if sec.Name.rstrip(b'\0')!=b'.reloc':
  for align in range(8):
   n=(len(data)-align)//8
   if n<=0:continue
   values=np.frombuffer(data,dtype='<u8',count=n,offset=align)
   for i in np.flatnonzero((values>=base+lo)&(values<base+hi)):
    src=sec.VirtualAddress+int(i)*8+align
    if not lo<=src<hi:abs_refs.append(hex(src))
 if not sec.Characteristics&0x20000000:continue
 candidates=set()
 for align in range(4):
  n=(len(data)-align)//4
  values=np.frombuffer(data,dtype='<i4',count=n,offset=align).astype(np.int64)
  positions=np.arange(n,dtype=np.int64)*4+align
  targets=values+positions+sec.VirtualAddress+4
  for i in np.flatnonzero((targets>=lo)&(targets<hi)):
   rva=sec.VirtualAddress+int(positions[i])
   if not lo<=rva<hi:candidates.add(rva)
 owners=set()
 for rva in candidates:
  i=bisect.bisect_right(starts,rva)-1
  if i>=0 and entries[i][0]<=rva<entries[i][1]:owners.add(entries[i])
  else:unowned_candidates.append(hex(rva))
 for start,end,uw in owners:
  for ins in md.disasm(old.get_data(start,end-start),base+start):
   for op in ins.operands:
    if op.type==capstone.CS_OP_MEM and op.mem.base==capstone.x86.X86_REG_RIP:
     dest=ins.address+ins.size+op.mem.disp
     if base+lo<=dest<base+hi:relative_refs.append([hex(ins.address-base),ins.mnemonic,ins.op_str])
assert not abs_refs and not relative_refs,(abs_refs,relative_refs)
report=dict(status='PASS',removedRuntimeFunctionRows=len(removed),allRetainedRuntimeFunctionRowsIdentical=True,allOtherExecutableAndOriginalSectionsIdentical=True,legacyRegionZeroed=True,absolutePointersToLegacy=abs_refs,externalRipReferencesToLegacy=relative_refs,unownedArithmeticCandidates=unowned_candidates,peChecksumValid=True)
(W/'engine-delta-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
