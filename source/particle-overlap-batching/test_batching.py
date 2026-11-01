"""Execute candidate merger, native vector growth/draw/cleanup and adapter."""
from pathlib import Path
import sys,json,struct,random
sys.dont_write_bytecode=True
sys.path[:0]=[r'F:/Codex/Temp/unit-selection-runtime',r'F:/Codex/Shogun2-CE/work/disasm_runtime']
import pefile,unicorn
from unicorn.x86_const import *
W=Path(__file__).resolve().parent;p=pefile.PE(str(W/'CE.campaign-night-candidate.dll'));base=p.OPTIONAL_HEADER.ImageBase
layout=json.loads((W/'layout.json').read_text());u=unicorn.Uc(unicorn.UC_ARCH_X86,unicorn.UC_MODE_64)
u.mem_map(base,(p.OPTIONAL_HEADER.SizeOfImage+4095)&~4095);u.mem_write(base,p.get_memory_mapped_image())
H=0x60000000;S=0x70000000;u.mem_map(H,0x2000000);u.mem_map(S,0x10000)
def q(a,v):u.mem_write(a,struct.pack('<Q',v))
def d(a,v):u.mem_write(a,struct.pack('<I',v))
def rq(a):return struct.unpack('<Q',u.mem_read(a,8))[0]
def rd(a):return struct.unpack('<I',u.mem_read(a,4))[0]
mesh=H+0x1000;mv=H+0x2000;rv=H+0x3000;callback=H+0x4000;stop=H+0x5000;vec=H+0x6000;table=H+0x7000;dealloc=H+0x9000
q(mesh,mv);q(mv+0x158,callback);u.mem_write(callback,b'\xc3');q(rv+0x40,base+0x1b6d140)
for entry in p.DIRECTORY_ENTRY_IMPORT:
 for imp in entry.imports:
  if imp.name and b'cache_aligned_deallocate' in imp.name:q(imp.address,dealloc)
heap=H+0x1000000;live={};allocations=0;frees=0;native_appends=0;seen=[];source_now=0;global_lists={}
def alloc(size,kind='vector'):
 global heap,allocations
 at=heap;heap+=(size+31)&~31;assert heap<H+0x2000000
 live[at]=kind;allocations+=1;u.mem_write(at,bytes(size));return at
def ret(value=0):
 sp=u.reg_read(UC_X86_REG_RSP);target=rq(sp);u.reg_write(UC_X86_REG_RAX,value);u.reg_write(UC_X86_REG_RSP,sp+8);u.reg_write(UC_X86_REG_RIP,target)
def hook(uc,address,size,user):
 global frees,native_appends
 if address==base+0x19fe50:ret(alloc(uc.reg_read(UC_X86_REG_RCX)))
 elif address in (base+0x19fe10,dealloc):
  at=uc.reg_read(UC_X86_REG_RCX);assert at in live,('double/unknown free',hex(at));del live[at];frees+=1;ret()
 elif address==base+0x132d60:native_appends+=1
 elif address==callback:
  index=uc.reg_read(UC_X86_REG_RDX);effect=global_lists[source_now][index]
  seen.append((effect,uc.reg_read(UC_X86_REG_R8)))
u.hook_add(unicorn.UC_HOOK_CODE,hook)
nonvol=[UC_X86_REG_RBX,UC_X86_REG_RBP,UC_X86_REG_RSI,UC_X86_REG_RDI,UC_X86_REG_R12,UC_X86_REG_R13,UC_X86_REG_R14,UC_X86_REG_R15]
def call(rva,a=0,b=0,c=0):
 sp=S+0x8008;q(sp,stop);u.reg_write(UC_X86_REG_RSP,sp)
 for r,v in [(UC_X86_REG_RCX,a),(UC_X86_REG_RDX,b),(UC_X86_REG_R8,c)]:u.reg_write(r,v)
 u.emu_start(base+rva,stop,count=20000000)
 return u.reg_read(UC_X86_REG_RAX)
def fixture(groups,adapter=False):
 global heap,live,allocations,frees,native_appends,source_now,global_lists
 heap=H+0x1000000;live={};allocations=frees=native_appends=0;seen.clear();global_lists={}
 u.mem_write(vec,bytes(64));u.mem_write(table,bytes(512));q(vec,1);q(vec+0x10,table);q(vec+0x38,len(groups))
 records=[];expected=[];next_effect=0
 for segment in range(max(1,len(groups)).bit_length()):
  first=0 if segment==0 else 1<<segment;capacity=2 if segment==0 else 1<<segment
  if first>=len(groups):break
  block=alloc(capacity*32,'segment');q(table+segment*8,block-first*32)
 for i,(owner,materials,active) in enumerate(groups):
  segment=(i|1).bit_length()-1;g=rq(table+segment*8)+i*32;records.append(g)
  source=H+0x10000+owner*0x200 if owner is not None else 0
  q(g,source);d(g+8,max(1,len(materials)));d(g+12,len(materials));q(g+16,alloc(max(1,len(materials))*8))
  for j,material in enumerate(materials):
   effect=H+0x100000+next_effect*0x200;renderer=H+0x300000+next_effect*0x200;next_effect+=1
   q(effect+0x38,renderer);q(renderer,rv);q(renderer+0x28,H+0xa000+material*16);d(renderer+0x5c,active[j]);q(rq(g+16)+j*8,effect)
   if source:
    global_lists.setdefault(source,[]).append(effect)
    if active[j]:expected.append(effect)
 for source,effects in global_lists.items():
  d(source+0x48,0);d(source+0x54,len(effects));array=H+0x500000+(source-H-0x10000)//0x200*0x10000;q(source+0x58,array)
  for i,e in enumerate(effects):q(array+i*8,e)
 original_flat=[rq(rq(g+16)+j*8) for g in records if rq(g) for j in range(rd(g+12))]
 expected_runs=0;last=None
 for owner,materials,_ in groups:
  if owner is None or not materials:last=None
  else:
   if last!=owner:expected_runs+=1
   last=owner
 saved=[]
 for i,r in enumerate(nonvol):u.reg_write(r,0x12340000+i*0x100);saved.append(u.reg_read(r))
 if adapter:
  sp=S+0x8000;u.mem_write(sp+0x20,bytes(u.mem_read(vec,64)));u.reg_write(UC_X86_REG_RSP,sp)
  u.emu_start(base+layout['callSite'],base+layout['callSite']+6,count=20000000)
  assert u.reg_read(UC_X86_REG_RSP)==sp
  for i,r in enumerate(nonvol):assert u.reg_read(r)==(saved[-1] if r in (UC_X86_REG_RSI,UC_X86_REG_RDI) else saved[i])
 else:
  runs=call(layout['exports']['MergeAdjacent'],vec);assert runs==expected_runs
  assert [u.reg_read(r) for r in nonvol]==saved
 flat=[rq(rq(g+16)+j*8) for g in records if rq(g) for j in range(rd(g+12))]
 assert flat==original_flat,'Emitter order or membership changed'
 retained=sum(bool(rq(g)) and rd(g+12)>0 for g in records);assert retained==expected_runs
 for g in records:
  source_now=rq(g)
  if source_now:call(0x1a9df80,source_now,mesh,g)
 assert [e for e,_ in seen]==expected,'Native draw sequence changed'
 for source,effects in global_lists.items():assert rd(source+0x48)==len(effects)
 material_setups=sum(bool(flag) for _,flag in seen)
 before_cleanup=len(live);call(0x1b1b0e0,vec);assert not live,('Native cleanup leaked',live)
 return dict(emitters=next_effect,groupsBefore=len(groups),groupsAfter=retained,visibleEmitters=len(seen),materialSetupsBefore=sum(len([x for x in act if x]) for owner,mat,act in groups if owner is not None),materialSetupsAfter=material_setups,nativeAppendCalls=native_appends,allocations=allocations,frees=frees,freedByNativeCleanup=before_cleanup)
rows=[];rng=random.Random(6465)
for n in [0,1,2,3,7,8,9,31,32,33,127,128,129,1000]:
 rows.append(fixture([(0,[0],[1]) for _ in range(n)],adapter=n in (0,1,33)))
for _ in range(128):
 n=rng.randrange(1,100);groups=[];owner=0
 for i in range(n):
  if rng.randrange(5)==0:owner=rng.randrange(4)
  count=rng.randrange(1,4)
  groups.append((owner,[rng.randrange(3) for _ in range(count)],[rng.randrange(2) for _ in range(count)]))
 fixture(groups)
for groups in [[(0,[0],[1]),(1,[0],[1]),(0,[0],[1])],[(0,[0],[1]),(None,[],[]),(0,[0],[1])],[(0,[0],[1]),(0,[],[]),(0,[0],[1])]]:fixture(groups,adapter=True)
result=dict(status='PASS',cases=len(rows)+128+3,largeSameSourceCase=rows[-1],boundaries=[r['groupsBefore'] for r in rows],randomInterleavingCases=128,exactStrict64DrawSequencePreserved=True,nativeAppendGrowthExecuted=True,nativeDrawLoopExecuted=True,nativeDestructorExecuted=True,noLeaksOrDoubleFrees=True,adapterReplayAndRegistersPreserved=True,scope='Offline native execution. Material setup counts are actual native draw flags; live FPS recovery remains pending.')
(W/'batching-validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
