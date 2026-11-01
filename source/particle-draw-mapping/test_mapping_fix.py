"""Execute the staged PE and all patched call sites; no live process/capture."""
import sys,json,struct,hashlib,random,itertools
from pathlib import Path
sys.dont_write_bytecode=True
sys.path[:0]=[r'F:/Codex/Temp/unit-selection-runtime',r'F:/Codex/Shogun2-CE/work/disasm_runtime']
import pefile,unicorn
from unicorn.x86_const import *
W=Path(__file__).resolve().parent
p=pefile.PE(str(W/'CE.campaign-night-candidate.dll'));base=p.OPTIONAL_HEADER.ImageBase
layout=json.loads((W/'mapping-layout.json').read_text());helper=json.loads((W/'candidate-helper.json').read_text())
section=p.get_section_by_rva(layout['startRva'])
assert section.Characteristics&0x20000000 and not section.Characteristics&0x80000000
assert not any(e.struct.BeginAddress<=layout['startRva']<e.struct.EndAddress for e in p.DIRECTORY_ENTRY_EXCEPTION)
u=unicorn.Uc(unicorn.UC_ARCH_X86,unicorn.UC_MODE_64)
u.mem_map(base,(p.OPTIONAL_HEADER.SizeOfImage+4095)&~4095);u.mem_write(base,p.get_memory_mapped_image())
H=0x60000000;S=0x70000000;u.mem_map(H,0x200000);u.mem_map(S,0x10000)
def q(a,v):u.mem_write(a,struct.pack('<Q',v))
def d(a,v):u.mem_write(a,struct.pack('<I',v))
source=H+0x1000;mesh=H+0x2000;group=H+0x3000;sv=H+0x4000;gv=H+0x5000;mv=H+0x6000;rv=H+0x7000;callback=H+0x8000;stop=H+0x9000
q(mesh,mv);q(mv+0x158,callback);u.mem_write(callback,b'\xc3');q(rv+0x40,base+0x1b6d140)
q(source+0x58,sv);q(group+0x10,gv)
effects=[H+0x10000+i*0x1000 for i in range(128)]
for i,e in enumerate(effects):q(e+0x38,e+0x80);q(e+0x80,rv)
seen=[]
def hook(uc,addr,size,user):
 if addr==callback:seen.append((uc.reg_read(UC_X86_REG_RCX),uc.reg_read(UC_X86_REG_RDX),uc.reg_read(UC_X86_REG_R8)))
 if addr==base+0x20a1b30:
  dest=uc.reg_read(UC_X86_REG_RCX);src=uc.reg_read(UC_X86_REG_RDX);n=uc.reg_read(UC_X86_REG_R8)
  uc.mem_write(dest,bytes(uc.mem_read(src,n)));uc.reg_write(UC_X86_REG_RAX,dest)
  sp=uc.reg_read(UC_X86_REG_RSP);target=struct.unpack('<Q',uc.mem_read(sp,8))[0]
  uc.reg_write(UC_X86_REG_RSP,sp+8);uc.reg_write(UC_X86_REG_RIP,target)
u.hook_add(unicorn.UC_HOOK_CODE,hook)
nonvol=[UC_X86_REG_RBX,UC_X86_REG_RBP,UC_X86_REG_RSI,UC_X86_REG_RDI,UC_X86_REG_R12,UC_X86_REG_R13,UC_X86_REG_R14,UC_X86_REG_R15]
rng=random.Random(6162);cases=0;paths=set()
def direct(site,n,index,target,changed):
 global cases
 seen.clear();d(source+0x54,n)
 for i in range(n):q(sv+i*8,effects[i])
 q(gv,target);sp=S+0x8000
 for i,r in enumerate(nonvol):u.reg_write(r,0x12340000+i*0x100)
 u.reg_write(UC_X86_REG_RBX,source);u.reg_write(UC_X86_REG_RDI,gv)
 saved=[u.reg_read(r) for r in nonvol]
 u.reg_write(UC_X86_REG_RSP,sp);u.reg_write(UC_X86_REG_RCX,mesh);u.reg_write(UC_X86_REG_RDX,index);u.reg_write(UC_X86_REG_R8,changed)
 u.emu_start(base+site,base+site+6,count=10000)
 expected=[] if target not in effects[:n] else [(mesh,effects.index(target),changed)]
 assert seen==expected,(site,n,index,target,seen,expected)
 assert u.reg_read(UC_X86_REG_RSP)==sp and [u.reg_read(r) for r in nonvol]==saved
 cases+=1
for site in layout['callSites']:
 for n in [1,2,7,32,128]:
  pairs=list(itertools.product(range(n),range(n))) if n<33 else [(rng.randrange(n),rng.randrange(n)) for _ in range(512)]
  for index,target in pairs:
   direct(site,n,index,effects[target],cases&1)
   paths.add('same' if index==target else 'previous' if target==index-1 else 'next' if target==index+1 else 'scan')
  for index in [0,n-1]:direct(site,n,index,H+0x190000,1)
 paths.add('missing')
# Run the entire actual native dispatcher, including active count/material checks
# and source cursor updates. Material transitions are computed on bucket order.
def full(order,active,materials):
 global cases
 n=len(order);seen.clear();d(source+0x54,n);d(source+0x48,0);d(group+0xc,n)
 for i in range(n):
  q(sv+i*8,effects[i]);q(gv+i*8,effects[order[i]])
  d(effects[i]+0x80+0x5c,active[i]);q(effects[i]+0x80+0x28,materials[i])
 sp=S+0x8008;q(sp,stop)
 u.reg_write(UC_X86_REG_RSP,sp);u.reg_write(UC_X86_REG_RCX,source);u.reg_write(UC_X86_REG_RDX,mesh);u.reg_write(UC_X86_REG_R8,group)
 u.emu_start(base+0x1a9df80,stop,count=100000)
 expected=[];previous=0
 for i in order:
  if active[i]:expected.append((mesh,i,int(materials[i]!=previous)));previous=materials[i]
 assert seen==expected,(order,active,seen,expected)
 assert struct.unpack('<I',u.mem_read(source+0x48,4))[0]==n
 cases+=1
full([0,2,1,3,4,5,6],[1,1,0,1,1,1,1],[H+0xa000]*7)
# Follow those indices into the actual shipped vertex upload routine. Mark each
# emitter's 40-byte particle vertex with its own identity; inactive G has no ring
# segments, so the original wrong index walks onward and copies A instead of B.
fixed_indices=[x[1] for x in seen]
for i in range(7):
 r=effects[i]+0x80;buf=H+0x100000+i*64;q(r+0x40,buf);u.mem_write(buf,bytes([i+1])*40)
 d(r+0x6c,0);d(r+0x70,int(i!=2));u.mem_write(r+0x74,b'\x01');d(r+0x78,0);d(r+0x7c,0);u.mem_write(r+0x80,b'\x00')
def upload(indices):
 result=[];params=H+0x191000;indices_at=H+0x192000;output=H+0x190000
 d(params,40);d(params+4,40);q(params+8,output)
 for index in indices:
  d(indices_at,index);d(indices_at+4,min(index+1,6));sp=S+0x8008;q(sp,stop)
  u.reg_write(UC_X86_REG_RSP,sp);u.reg_write(UC_X86_REG_RCX,params);u.reg_write(UC_X86_REG_RDX,indices_at);u.reg_write(UC_X86_REG_R8,source)
  u.emu_start(base+0x1b76850,stop,count=10000)
  copied=bytes(u.mem_read(output,40));assert len(set(copied))==1;result.append(copied[0]-1)
 return result
old_upload=upload([0,2,3,4,5,6]);new_upload=upload(fixed_indices)
assert old_upload==[0,3,3,4,5,6] and new_upload==[0,1,3,4,5,6],(old_upload,new_upload)
for _ in range(256):
 n=rng.randrange(1,65);order=list(range(n));rng.shuffle(order)
 full(order,[rng.randrange(2) for i in order],[H+0xa000+8*rng.randrange(4) for i in order])
receipt=dict(status='PASS',cases=cases,callSites=[hex(x) for x in layout['callSites']],paths=sorted(paths),nativeWholeDispatcherCases=257,registerAndStackPreservation=True,materialTransitionsPreserved=True,executableNonWritableAdapter=True,leafWithoutStackChanges=True,engineSha256=hashlib.sha256((W/'CE.campaign-night-candidate.dll').read_bytes()).hexdigest(),scope='Offline native execution of emitted candidate. Live flashing acceptance remains pending.')
receipt['actualNativeVertexUpload']={'oldEmitterIndices':old_upload,'fixedEmitterIndices':new_upload,'missingVisibleEmitterCorrected':True,'duplicateEmitterCorrected':True,'memcpyOnlyFixture':True}
(W/'mapping-fix-validation.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
