from pathlib import Path
import sys,json,struct,random,math
sys.dont_write_bytecode=True
sys.path[:0]=[r'F:/Codex/Temp/unit-selection-runtime',r'F:/Codex/Shogun2-CE/work/disasm_runtime']
import pefile,unicorn
from unicorn.x86_const import *
W=Path(__file__).resolve().parent;p=pefile.PE(str(W/'CE.campaign-night-candidate.dll'));base=p.OPTIONAL_HEADER.ImageBase
layout=json.loads((W/'layout.json').read_text());u=unicorn.Uc(unicorn.UC_ARCH_X86,unicorn.UC_MODE_64)
u.mem_map(base,(p.OPTIONAL_HEADER.SizeOfImage+4095)&~4095);u.mem_write(base,p.get_memory_mapped_image())
H=0x60000000;S=0x70000000;u.mem_map(H,0x3000000);u.mem_map(S,0x10000)
def q(a,v):u.mem_write(a,struct.pack('<Q',v))
def d(a,v):u.mem_write(a,struct.pack('<I',v))
def rq(a):return struct.unpack('<Q',u.mem_read(a,8))[0]
def rd(a):return struct.unpack('<I',u.mem_read(a,4))[0]
def f32(x):return struct.unpack('<f',struct.pack('<f',x))[0]
mesh=H+0x1000;mv=H+0x2000;rv=H+0x3000;callback=H+0x4000;stop=H+0x5000;vec=H+0x6000;table=H+0x7000
world=H+0xa000;wv=H+0xb000;camera=H+0xc000;cv=H+0xd000;ev=H+0xe000;sv=H+0xf000
getcam=H+0x8000;getcp=H+0x8100;getep=H+0x8200;source_draw=H+0x8300;dealloc=H+0x8400;pass_=H+0x8500
q(mesh,mv);q(mv+0x158,callback);u.mem_write(callback,b'\xc3');q(rv+0x40,base+0x1b6d140)
q(world,wv);q(wv+0x48,getcam);q(camera,cv);q(cv+0x78,getcp);q(ev+0x50,getep);q(sv+0xa0,source_draw)
for entry in p.DIRECTORY_ENTRY_IMPORT:
 for imp in entry.imports:
  if imp.name and b'cache_aligned_deallocate' in imp.name:q(imp.address,dealloc)
heap=H+0x1000000;live={};allocations=frees=position_calls=camera_calls=0;cam=(0,0,0);seen=[];runs=[];source_now=0
def alloc(n,kind='native'):
 global heap,allocations
 at=heap;heap+=(n+31)&~31;assert heap<H+0x3000000;live[at]=kind;allocations+=1;u.mem_write(at,bytes(n));return at
def ret(value=0):
 sp=u.reg_read(UC_X86_REG_RSP);target=rq(sp);u.reg_write(UC_X86_REG_RAX,value);u.reg_write(UC_X86_REG_RSP,sp+8);u.reg_write(UC_X86_REG_RIP,target)
def hook(uc,a,size,user):
 global frees,position_calls,camera_calls,source_now
 x=uc.reg_read(UC_X86_REG_RCX);y=uc.reg_read(UC_X86_REG_RDX)
 if a==base+0x19fe50:ret(alloc(x))
 elif a in [base+0x19fe10,dealloc]:assert x in live,hex(x);del live[x];frees+=1;ret()
 elif a==getcam:camera_calls+=1;ret(camera)
 elif a==getcp:u.mem_write(y,struct.pack('<3f',*cam));ret(y)
 elif a==getep:position_calls+=1;u.mem_write(y,bytes(u.mem_read(x+0x60,12)));ret(y)
 elif a==source_draw:
  assert y==pass_;g=uc.reg_read(UC_X86_REG_R8);source_now=x
  runs.append((x,[rq(rq(g+16)+i*8) for i in range(rd(g+12))]))
  uc.reg_write(UC_X86_REG_RDX,mesh);uc.reg_write(UC_X86_REG_RIP,base+0x1a9df80)
 elif a==callback:
  i=uc.reg_read(UC_X86_REG_RDX);e=rq(rq(source_now+0x58)+i*8);seen.append((e,uc.reg_read(UC_X86_REG_R8)))
u.hook_add(unicorn.UC_HOOK_CODE,hook)
nonvol=[UC_X86_REG_RBX,UC_X86_REG_RBP,UC_X86_REG_RSI,UC_X86_REG_RDI,UC_X86_REG_R12,UC_X86_REG_R13,UC_X86_REG_R14,UC_X86_REG_R15]
def call(rva,a=0,b=0):
 sp=S+0x8008;q(sp,stop);u.reg_write(UC_X86_REG_RSP,sp);u.reg_write(UC_X86_REG_RCX,a);u.reg_write(UC_X86_REG_RDX,b)
 saved=[]
 for i,r in enumerate(nonvol):u.reg_write(r,0x12340000+i*0x100);saved.append(u.reg_read(r))
 u.emu_start(base+rva,stop,count=50000000)
 assert [u.reg_read(r) for r in nonvol]==saved,(hex(rva),hex(u.reg_read(UC_X86_REG_RIP)),[(r,hex(u.reg_read(r)),hex(v)) for r,v in zip(nonvol,saved) if u.reg_read(r)!=v],len(seen))
 return u.reg_read(UC_X86_REG_RAX)
rng=random.Random(6566)
def fixture(counts,camera_position=(0,0,0),adapter=False,ties=False):
 global heap,live,allocations,frees,position_calls,camera_calls,cam
 heap=H+0x1000000;live={};allocations=frees=position_calls=camera_calls=0;cam=camera_position;seen.clear();runs.clear()
 owners=[];effects=[];active={};mats={};expected_records=[]
 for si,n in enumerate(counts):
  source=H+0x10000+si*0x200;owners.append(source);u.mem_write(source,bytes(0xb0));q(source,sv);q(source+0x90,world)
  array=H+0x500000+si*0x10000;d(source+0x50,n);d(source+0x54,n);q(source+0x58,array)
  for j in range(n):
   i=len(effects);e=H+0x100000+i*0x200;r=H+0x300000+i*0x200;effects.append(e);q(array+j*8,e);q(e,ev);q(e+0x38,r);q(r,rv)
   position=(float(j%3),0,4.0) if ties else (rng.uniform(-80,80),rng.uniform(0,10),rng.uniform(-80,80))
   u.mem_write(e+0x60,struct.pack('<3f',*position));position=struct.unpack('<3f',u.mem_read(e+0x60,12))
   delta=[f32(x-y) for x,y in zip(position,cam)];key=f32(f32(f32(delta[1]*delta[1])+f32(delta[0]*delta[0]))+f32(delta[2]*delta[2]))
   active[e]=rng.randrange(4)!=0;mats[e]=rng.randrange(3);d(r+0x5c,int(active[e]));q(r+0x28,H+0x90000+mats[e]*16)
   expected_records.append((key,source,e))
  call(0x1aea3f0,source)
  assert rd(source+0x3c)==int(n>0)
  for j in range(n):
   e=rq(array+j*8);assert struct.unpack('<f',u.mem_read(e+0xb8,4))[0]==next(k for k,s,x in expected_records if x==e)
  before=allocations;call(0x1aea3f0,source);assert allocations==before,'Source preparation must reuse its marker storage'
  d(source+0x48,0)
 markers=[s for s,n in zip(owners,counts) if n];rng.shuffle(markers)
 u.mem_write(vec,bytes(64));u.mem_write(table,bytes(512));q(vec,1);q(vec+0x10,table);q(vec+0x38,len(markers));groups=[]
 for segment in range(max(1,len(markers)).bit_length()):
  first=0 if segment==0 else 1<<segment;capacity=2 if segment==0 else 1<<segment
  if first>=len(markers):break
  block=alloc(capacity*32,'segment');q(table+segment*8,block-first*32)
 for i,s in enumerate(markers):
  g=rq(table+((i|1).bit_length()-1)*8)+i*32;groups.append(g);q(g,s)
  # Actual native empty-vector copy used by the gather worker.
  call(0x1c5470,g+8,rq(s+0x40)+8)
 before=allocations
 if adapter:
  sp=S+0x8000;u.mem_write(sp+0x20,bytes(u.mem_read(vec,64)));u.reg_write(UC_X86_REG_RSP,sp);u.reg_write(UC_X86_REG_R14,pass_)
  u.emu_start(base+layout['callSite'],base+layout['callSite']+6,count=50000000)
 else:call(layout['exports']['RenderStream'],vec,pass_)
 stream_allocations=allocations-before;assert stream_allocations==int(bool(effects))
 assert all(rq(g)==0 for g in groups)
 flattened=[e for _,run in runs for e in run]
 assert len(flattened)==len(effects) and set(flattened)==set(effects)
 key_by={e:k for k,s,e in expected_records}
 assert [key_by[e] for e in flattened]==sorted(key_by.values(),reverse=True)
 if not ties:assert flattened==[e for _,_,e in sorted(expected_records,reverse=True)]
 assert [e for e,_ in seen]==[e for e in flattened if active[e]]
 assert all(a[0]!=b[0] for a,b in zip(runs,runs[1:]))
 for s,n in zip(owners,counts):assert rd(s+0x48)==n
 call(0x1b1b0e0,vec)
 for s in owners:
  call(0x1ac35a0,s+0x38)
  if rq(s+0x40):call(0x19fe10,rq(s+0x40))
 assert not live,live
 return dict(emitters=len(effects),sources=len(markers),streamScratchAllocations=stream_allocations,sourceMarkerAllocations=len(markers),cameraCallsPerPreparation=camera_calls//2,emitterPositionCallsPerPreparation=position_calls//2,drawRuns=len(runs),allocations=allocations,frees=frees)
rows=[]
for counts in [[],[0],[1],[1000],[500,500],[31,0,8,17],[1]*33]:rows.append(fixture(counts,adapter=len(counts)%2==0))
for _ in range(32):fixture([rng.randrange(0,20) for _ in range(rng.randrange(1,9))],tuple(f32(rng.uniform(-10,10)) for _ in range(3)))
for _ in range(4):fixture([10,10,10],ties=True)
result=dict(status='PASS',cases=len(rows)+36,fixtures=rows,exactDistanceOrderPreserved=True,uniqueKeySequenceMatchesStrict64=True,stableSourceTiePriority=True,nativeSortAndClearExecuted=True,nativeEmptyVectorGatherCopyExecuted=True,nativeDrawAndDestructorExecuted=True,noLeaksOrDoubleFrees=True,scope='Offline native source preparation and streamed draw; allocator/camera/position functions are controlled fixtures. Actual live FPS remains unmeasured.')
(W/'stream-validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
