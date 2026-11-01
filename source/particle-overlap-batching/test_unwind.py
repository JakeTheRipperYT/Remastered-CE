from pathlib import Path
import sys,ctypes as C,json,struct
sys.dont_write_bytecode=True
sys.path[:0]=[r'F:/Codex/Temp/unit-selection-runtime',r'F:/Codex/Shogun2-CE/work/disasm_runtime']
import pefile,capstone,unicorn
from unicorn.x86_const import *
W=Path(__file__).resolve().parent;p=pefile.PE(str(W/'CE.campaign-night-candidate.dll'));image=p.get_memory_mapped_image();layout=json.loads((W/'layout.json').read_text())
source=Path('F:/Codex/Remastered-CE-Port/source/test_night_unwind.py').read_text()
exec(source[source.index('k=C.WinDLL'):source.index('for base in [')])
rows=layout['unwind'];results=[]
def q(u,a,v):u.mem_write(a,struct.pack('<Q',v))
def d(u,a,v):u.mem_write(a,struct.pack('<I',v))
for base in [0x180000000,0x230000000,0x7ff600000000]:
 host=k.VirtualAlloc(base,0x4000000,0x3000,4);hs=k.VirtualAlloc(stack,ssize,0x3000,4);assert host==base and hs==stack
 try:
  C.memmove(base,image,len(image));u=unicorn.Uc(unicorn.UC_ARCH_X86,unicorn.UC_MODE_64);u.mem_map(base,0x4000000);u.mem_write(base,image);u.mem_map(stack,ssize);u.mem_map(stop,4096)
  call_stop=[None]
  def stop_call(uc,address,size,user):
   if address==call_stop[0]:uc.emu_stop()
  u.hook_add(unicorn.UC_HOOK_CODE,stop_call)
  for name in ['MergeAdjacent','BatchAdapter']:
   for owners in [[],[1],[1,1],[1,2,1],[1,0,1]]:
    seed(u);v=stack+0x18000 if name=='MergeAdjacent' else sp+0x28;tab=stack+0x18200;groups=stack+0x18400;items=stack+0x18800
    u.mem_write(v,bytes(64));q(u,v+0x10,tab);q(u,v+0x38,len(owners));q(u,tab,groups);q(u,tab+8,groups);q(u,tab+16,groups)
    for i,owner in enumerate(owners):
     g=groups+i*32;q(u,g,owner);d(u,g+8,8);d(u,g+12,1);q(u,g+16,items+i*64);q(u,items+i*64,0x12340000+i)
    u.reg_write(UC_X86_REG_RCX,v)
    expected=[u.reg_read(r) if r not in [UC_X86_REG_RSP,UC_X86_REG_RIP] else sp+8 if r==UC_X86_REG_RSP else stop for r in nonvol]+[u.reg_read(xmm[i]).to_bytes(16,'little') for i in range(6,16)]
    pc=base+layout['exports'][name];boundaries=0
    while pc!=stop:
     row=next((r for r in rows if base+r[0]<=pc<base+r[1]),None);assert row is not None,hex(pc)
     assert unwind(u,base,pc,row)==expected,(name,owners,hex(pc))
     boundaries+=1;ins=next(md.disasm(bytes(u.mem_read(pc,15)),pc))
     if ins.mnemonic=='call':
      call_stop[0]=pc+ins.size
      try:u.emu_start(pc,0,count=100000)
      except Exception:
       print('Fixture call failure',name,owners,hex(pc),hex(u.reg_read(UC_X86_REG_RIP)),hex(u.reg_read(UC_X86_REG_RCX)),hex(u.reg_read(UC_X86_REG_RDX)))
       raise
      call_stop[0]=None
     else:u.emu_start(pc,0,count=1)
     if name=='BatchAdapter' and ins.mnemonic=='mov' and ins.op_str in ['rdi, r15','rsi, r15']:
      reg=UC_X86_REG_RDI if ins.op_str.startswith('rdi') else UC_X86_REG_RSI;expected[nonvol.index(reg)]=u.reg_read(UC_X86_REG_R15)
     pc=u.reg_read(UC_X86_REG_RIP)
    results.append(dict(base=hex(base),function=name,owners=owners,boundaries=boundaries))
 finally:k.VirtualFree(host,0,0x8000);k.VirtualFree(hs,0,0x8000)
receipt=dict(status='PASS',windowsRtlVirtualUnwind=True,bases=3,chainedUnwindExecuted=True,boundaries=sum(r['boundaries'] for r in results),cases=results,scope='Actual Windows unwinding at executed instruction boundaries, including early exits, loop and epilogs. All nonvolatile GPRs and XMM6-XMM15 checked.')
(W/'unwind-validation.json').write_text(json.dumps(receipt,indent=2));print('PASS Windows native unwind:',receipt['boundaries'],'boundaries at three bases.')
