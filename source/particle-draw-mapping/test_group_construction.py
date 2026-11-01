"""Run CE's real bucket builder and emitter sort using its shipped thresholds."""
import sys,struct,json,math
from pathlib import Path
sys.dont_write_bytecode=True
sys.path[:0]=[r'F:/Codex/Temp/unit-selection-runtime',r'F:/Codex/Shogun2-CE/work/disasm_runtime']
import pefile,unicorn
from unicorn.x86_const import *
w=Path(__file__).resolve().parent
p=pefile.PE(r'D:/SteamLibrary/steamapps/common/Shogun 2 Complete Edition/empire.retail.x64.dll');base=p.OPTIONAL_HEADER.ImageBase
u=unicorn.Uc(unicorn.UC_ARCH_X86,unicorn.UC_MODE_64);u.mem_map(base,(p.OPTIONAL_HEADER.SizeOfImage+4095)&~4095);u.mem_write(base,p.get_memory_mapped_image())
H=0x60000000;S=0x70000000;u.mem_map(H,0x400000);u.mem_map(S,0x10000)
def q(a,v):u.mem_write(a,struct.pack('<Q',v))
def d(a,v):u.mem_write(a,struct.pack('<I',v))
def rq(a):return struct.unpack('<Q',u.mem_read(a,8))[0]
def rd(a):return struct.unpack('<I',u.mem_read(a,4))[0]
source=H+0x1000;world=H+0x2000;camera=H+0x3000;wv=H+0x4000;cv=H+0x5000;ev=H+0x6000;getcam=H+0x8000;getcp=H+0x8100;getep=H+0x8200;stop=H+0x9000
q(source+0x90,world);q(world,wv);q(wv+0x48,getcam);q(camera,cv);q(cv+0x78,getcp);q(ev+0x50,getep)
d(source+0x38,16);d(source+0x3c,0);q(source+0x40,H+0xa000)
u.mem_write(0x18345d888,struct.pack('<f',128));u.mem_write(0x18345e328,struct.pack('<f',150000))
heap=H+0x100000
def alloc(size):
 global heap
 result=heap;heap+=(size+31)&~31;assert heap<H+0x400000;return result
def ret(value=0):
 sp=u.reg_read(UC_X86_REG_RSP);target=rq(sp);u.reg_write(UC_X86_REG_RAX,value);u.reg_write(UC_X86_REG_RSP,sp+8);u.reg_write(UC_X86_REG_RIP,target)
def hook(uc,addr,size,user):
 a=uc.reg_read(UC_X86_REG_RCX);b=uc.reg_read(UC_X86_REG_RDX);c=uc.reg_read(UC_X86_REG_R8)
 if addr==getcam:ret(camera)
 elif addr==getcp:u.mem_write(b,bytes(12));ret(b)
 elif addr==getep:ret(a+0x60)
 elif addr==base+0x19fe50:ret(alloc(a))
 elif addr==base+0x19fe10:ret()
 elif addr==base+0x132d60:
  n=rd(a+4);cap=rd(a);ptr=rq(a+8)
  if n==cap:
   new=alloc(max(8,cap*2)*8)
   if n:u.mem_write(new,bytes(u.mem_read(ptr,n*8)))
   ptr=new;q(a+8,ptr);d(a,max(8,cap*2))
  q(ptr+n*8,rq(b));d(a+4,n+1);ret()
 elif addr==base+0x1aafbb0:
  buf=bytearray(u.mem_read(b,32));n=struct.unpack_from('<I',buf,12)[0];old=struct.unpack_from('<Q',buf,16)[0];new=alloc(max(1,n)*8)
  if n:u.mem_write(new,bytes(u.mem_read(old,n*8)))
  struct.pack_into('<Q',buf,16,new);u.mem_write(a,bytes(buf));ret(a)
 elif addr==base+0x20a1b30:u.mem_write(a,bytes(u.mem_read(b,c)));ret(a)
u.hook_add(unicorn.UC_HOOK_CODE,hook)
def run(address,a,b=0,c=0):
 sp=S+0x8008;q(sp,stop);u.reg_write(UC_X86_REG_RSP,sp);u.reg_write(UC_X86_REG_RCX,a);u.reg_write(UC_X86_REG_RDX,b);u.reg_write(UC_X86_REG_R8,c)
 u.emu_start(address,stop,count=200000)
distance={'A':1000,'C':1230,'B':1120,'D':940,'E':900,'F':870,'G':1110};effects={n:H+0x10000+i*0x1000 for i,n in enumerate(distance)};reverse={v:k for k,v in effects.items()}
for n,e in effects.items():
 q(e,ev);u.mem_write(e+0x60,struct.pack('<3f',math.sqrt(distance[n]),0,0));run(base+0x1abfe80,source,e)
groups=[]
for i in range(rd(source+0x3c)):
 g=rq(source+0x40)+i*32;vec=rq(g+16);n=rd(g+12);run(base+0x1a9cec0,vec,vec+n*8,n)
 groups.append(dict(key=struct.unpack('<f',u.mem_read(g+24,4))[0],members=[reverse[rq(vec+j*8)] for j in range(n)]))
groups.sort(key=lambda g:g['key'],reverse=True)
vec=H+0x20000
for i,e in enumerate(effects.values()):q(vec+i*8,e)
run(base+0x1a9d1f0,vec,vec+len(effects)*8,len(effects))
global_order=[reverse[rq(vec+i*8)] for i in range(len(effects))];bucket_order=[n for g in groups for n in g['members']]
assert global_order!=bucket_order,(global_order,bucket_order)
result=dict(status='REPRODUCED_NATIVE_GROUP_ORDER_DIVERGENCE',thresholds=dict(sharedDistanceSquared=128,farDistanceSquared=150000),insertionOrder=list(distance),squaredDistances=distance,groups=groups,globalOrder=global_order,bucketOrder=bucket_order,scope='Original native bucket-builder and emitter-sort machine code. Allocation/vector helpers and camera/origin inputs are faithful fixtures; global concurrent-vector sort is represented by descending native group keys.')
(w/'native-group-construction-reproduction.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
