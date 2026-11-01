"""Exercise the real CE EffectsView controller against synthetic GPU query results."""
from pathlib import Path
import sys,struct,json
sys.dont_write_bytecode=True
sys.path[:0]=['F:/Codex/Temp/unit-selection-runtime','F:/Codex/Shogun2-CE/work/disasm_runtime']
import pefile,unicorn
from unicorn.x86_const import *
W=Path(__file__).resolve().parent
p=pefile.PE('D:/SteamLibrary/steamapps/common/Shogun 2 Complete Edition/empire.retail.x64.dll',fast_load=True)
base=int(sys.argv[1],0) if len(sys.argv)>1 else p.OPTIONAL_HEADER.ImageBase
u=unicorn.Uc(unicorn.UC_ARCH_X86,unicorn.UC_MODE_64)
u.mem_map(base,(p.OPTIONAL_HEADER.SizeOfImage+4095)&~4095);u.mem_write(base,p.get_memory_mapped_image())
H=0x60000000;S=0x70000000
u.mem_map(H,0x10000);u.mem_map(S,0x10000)
view=H+0x1000;device=H+0x2000;viewport=H+0x3000;vt=H+0x4000;begin=H+0x5000;end=H+0x5100;callback=H+0x6000;stop=H+0x7000
def q(a,v):u.mem_write(a,struct.pack('<Q',v&((1<<64)-1)))
def d(a,v):u.mem_write(a,struct.pack('<I',v))
def f(a,v):u.mem_write(a,struct.pack('<f',v))
def rq(a):return struct.unpack('<Q',u.mem_read(a,8))[0]
def rd(a):return struct.unpack('<I',u.mem_read(a,4))[0]
def rf(a):return struct.unpack('<f',u.mem_read(a,4))[0]
q(base+0x3450230,device);q(begin,vt);q(end,vt);q(vt+0x40,callback)
state={};calls=[]
def ret(value=0):
 sp=u.reg_read(UC_X86_REG_RSP);target=rq(sp);u.reg_write(UC_X86_REG_RAX,value);u.reg_write(UC_X86_REG_RSP,sp+8);u.reg_write(UC_X86_REG_RIP,target)
def hook(uc,address,size,user):
 if address==callback:
  obj=uc.reg_read(UC_X86_REG_RCX);status=uc.reg_read(UC_X86_REG_RDX);output=uc.reg_read(UC_X86_REG_R8);calls.append(obj)
  ready=state['ready'];d(status,1 if ready else 0)
  if ready:q(output,state['start']+(state['particleTicks'] if obj==end else 0))
  ret(status)
 elif address==base+0x1a724f0:
  target=uc.reg_read(UC_X86_REG_RDX);u.mem_write(target,struct.pack('<4I',0,0,2560,1440));ret()
u.hook_add(unicorn.UC_HOOK_CODE,hook)
nonvol=[UC_X86_REG_RBX,UC_X86_REG_RBP,UC_X86_REG_RSI,UC_X86_REG_RDI,UC_X86_REG_R12,UC_X86_REG_R13,UC_X86_REG_R14,UC_X86_REG_R15]
original={0x1b2cc48:bytes(u.mem_read(base+0x1b2cc48,1)),0x1b2ccc7:bytes(u.mem_read(base+0x1b2ccc7,7)),0x2e7b750:bytes(u.mem_read(base+0x2e7b750,8))}
assert original[0x1b2cc48]==b'\x18' and original[0x1b2ccc7]==bytes.fromhex('488b8bb8000000')
def mode(candidate):
 for rva,data in original.items():u.mem_write(base+rva,data)
 if candidate:
  # Absolute seconds: use GPU timestamp frequency instead of whole-frame ticks.
  u.mem_write(base+0x1b2cc48,b'\x20')
  u.mem_write(base+0x2e7b750,struct.pack('<d',0.0033))
  # Both no-pending and not-ready paths enter here; zero the denominator to
  # reach the existing restore/exit path without reusing a stale measurement.
  u.mem_write(base+0x1b2ccc7,bytes.fromhex('31ff9090909090'))
 u.ctl_remove_cache(base+0x1b2cbd0,base+0x1b2ce10)
def fixture(scale=.7,frame_ms=16,particle_ms=6,frequency=1_000_000_000,ready=True,pending=True,enabled=True,override=0,cached_ms=6,start=1000):
 u.mem_write(view,bytes(0x100));u.mem_write(base+0x3462388,bytes([int(enabled)]));f(base+0x3462018,override)
 q(device+0x18,round(frame_ms*frequency/1000));q(device+0x20,frequency)
 q(view+0x80,begin);q(view+0x98,end);d(view+0xb0,int(pending));d(view+0xb4,0);q(view+0xb8,round(cached_ms*frequency/1000));f(view+0xe0,scale)
 state.update(ready=ready,start=start,particleTicks=round(particle_ms*frequency/1000));calls.clear()
 sp=S+0x8008;q(sp,stop);u.reg_write(UC_X86_REG_RSP,sp);u.reg_write(UC_X86_REG_RCX,view);u.reg_write(UC_X86_REG_RDX,viewport);u.reg_write(UC_X86_REG_R8,0)
 saved=[]
 for i,r in enumerate(nonvol):u.reg_write(r,0x12340000+i*0x100);saved.append(u.reg_read(r))
 u.emu_start(base+0x1b2cbd0,stop,count=200000)
 assert [u.reg_read(r) for r in nonvol]==saved
 assert u.reg_read(UC_X86_REG_RSP)==sp+8
 result={'scale':rf(view+0xe0),'retired':rd(view+0xb4),'timingTicks':rq(view+0xb8),'queryCalls':len(calls),'viewport':struct.unpack('<4I',u.mem_read(viewport,16))}
 f32=lambda x:struct.unpack('<f',struct.pack('<f',x))[0]
 assert result['viewport']==(0,0,int(f32(2560*result['scale'])),int(f32(1440*result['scale'])))
 return result
rows=[]
for candidate in [False,True]:
 mode(candidate)
 for frame in [12,16,24,32,48]:
  r=fixture(frame_ms=frame);rows.append({'candidate':candidate,'frameMs':frame,'particleMs':6,**r})
  if candidate:assert abs(r['scale']-.69)<1e-6
mode(False);stale_original=fixture(pending=False);notready_original=fixture(ready=False)
mode(True);stale_fixed=fixture(pending=False);notready_fixed=fixture(ready=False)
assert abs(stale_original['scale']-.69)<1e-6 and abs(notready_original['scale']-.69)<1e-6
assert abs(stale_fixed['scale']-.7)<1e-6 and abs(notready_fixed['scale']-.7)<1e-6
checks=10
for frequency in [1_000_000,10_000_000,27_000_000,1_000_000_000]:
 for frame in [8,16,33,80]:
  for cost in [0,1,3,3.2,3.4,6,20]:
   r=fixture(frame_ms=frame,particle_ms=cost,frequency=frequency)
   expected=.71 if cost<=3.3 else .69
   assert abs(r['scale']-expected)<1e-6,(frequency,frame,cost,r)
   assert r['retired']==1 and r['queryCalls']==2;checks+=1
for enabled,override,expected in [(False,0,1),(True,.5,.5),(True,2,1)]:
 r=fixture(enabled=enabled,override=override);assert abs(r['scale']-expected)<1e-6;assert r['queryCalls']==0;checks+=1
for frequency in [0,1_000_000_000]:
 for ready,pending in [(False,True),(True,False)]:
  r=fixture(frequency=frequency,ready=ready,pending=pending);assert abs(r['scale']-.7)<1e-6;checks+=1
for scale,cost,expected in [(.3,10,.3),(1,1,1)]:
 r=fixture(scale=scale,particle_ms=cost);assert abs(r['scale']-expected)<1e-6;checks+=1
for start in [0,2**63-1000,2**64-1000]:
 r=fixture(start=start);assert abs(r['scale']-.69)<1e-6 and r['timingTicks']==6_000_000;checks+=1
candidate_path=W/'CE.campaign-night-candidate.dll'
if candidate_path.exists():
 cp=pefile.PE(str(candidate_path),fast_load=True)
 for rva,n in [(0x1b2cbd0,0x240),(0x2e7b750,8)]:assert cp.get_data(rva,n)==bytes(u.mem_read(base+rva,n))
report={'status':'PASS','checks':checks,'base':hex(base),'nativeFunction':'181b2cbd0','originalFrameRelativeResponses':rows,'staleOriginal':stale_original,'staleCandidate':stale_fixed,'notReadyOriginal':notready_original,'notReadyCandidate':notready_fixed,'candidateBudgetMs':3.3,'gameFilesChanged':False,'reportedSpikeAttribution':'Controller mechanism reproduced; live contribution not yet measured.'}
name='native-validation.json' if base==p.OPTIONAL_HEADER.ImageBase else 'native-validation-'+hex(base)+'.json'
(W/name).write_text(json.dumps(report,indent=2));print(json.dumps({'status':'PASS','checks':checks,'base':hex(base)}))
