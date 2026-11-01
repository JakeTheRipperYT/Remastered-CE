from pathlib import Path
import sys,ctypes as C,json,struct
sys.dont_write_bytecode=True

import pefile,capstone,unicorn
from unicorn.x86_const import *
if len(sys.argv)!=3:raise SystemExit('Usage: test_refresh_unwind.py CE58.dll OUTPUT_DIRECTORY')
W=Path(sys.argv[2]);W.mkdir(parents=True,exist_ok=True)
p=pefile.PE(sys.argv[1],fast_load=True);image=p.get_memory_mapped_image();layout=json.loads(Path(__file__).with_name('refresh-layout.json').read_text())
k=C.WinDLL('kernel32',use_last_error=True);nt=C.WinDLL('ntdll');k.VirtualAlloc.argtypes=[C.c_void_p,C.c_size_t,C.c_ulong,C.c_ulong];k.VirtualAlloc.restype=C.c_void_p;k.VirtualFree.argtypes=[C.c_void_p,C.c_size_t,C.c_ulong]
nt.RtlVirtualUnwind.argtypes=[C.c_ulong,C.c_ulonglong,C.c_ulonglong,C.c_void_p,C.c_void_p,C.POINTER(C.c_void_p),C.POINTER(C.c_ulonglong),C.c_void_p];nt.RtlVirtualUnwind.restype=C.c_void_p
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);stack=0x710000000;ssize=0x20000;sp=stack+0x10000-8;stop=0x700000000
gprs=[UC_X86_REG_RAX,UC_X86_REG_RCX,UC_X86_REG_RDX,UC_X86_REG_RBX,UC_X86_REG_RSP,UC_X86_REG_RBP,UC_X86_REG_RSI,UC_X86_REG_RDI,UC_X86_REG_R8,UC_X86_REG_R9,UC_X86_REG_R10,UC_X86_REG_R11,UC_X86_REG_R12,UC_X86_REG_R13,UC_X86_REG_R14,UC_X86_REG_R15]
offsets={r:0x78+i*8 for i,r in enumerate(gprs)};offsets[UC_X86_REG_RIP]=0xf8
nonvol=[UC_X86_REG_RBX,UC_X86_REG_RSP,UC_X86_REG_RBP,UC_X86_REG_RSI,UC_X86_REG_RDI,UC_X86_REG_R12,UC_X86_REG_R13,UC_X86_REG_R14,UC_X86_REG_R15,UC_X86_REG_RIP]
xmm=[globals()['UC_X86_REG_XMM'+str(i)] for i in range(16)];checks=0;cases=0
def context(u,pc):
 buf=C.create_string_buffer(0x4e0);addr=(C.addressof(buf)+15)&~15;C.memset(addr,0,0x4d0)
 C.c_uint32.from_address(addr+0x30).value=0x10000b
 for r,o in offsets.items():C.c_uint64.from_address(addr+o).value=(pc if r==UC_X86_REG_RIP else u.reg_read(r))
 for i,r in enumerate(xmm):C.memmove(addr+0x1a0+i*16,u.reg_read(r).to_bytes(16,'little'),16)
 return buf,addr
def unwind(u,base,pc,row):
 global checks
 buf,ctx=context(u,pc);rf=(C.c_uint32*3)(*row);hd=C.c_void_p();frame=C.c_ulonglong()
 C.memmove(stack,bytes(u.mem_read(stack,ssize)),ssize)
 nt.RtlVirtualUnwind(0,base,pc,C.byref(rf),ctx,C.byref(hd),C.byref(frame),None)
 values=[C.c_uint64.from_address(ctx+offsets[r]).value for r in nonvol]+[C.string_at(ctx+0x1a0+i*16,16) for i in range(6,16)]
 checks+=1;return values
def seed(u):
 u.mem_write(stack,bytes.fromhex('3322119900000000')*(ssize//8));u.mem_write(sp,struct.pack('<Q',stop))
 for i,r in enumerate(gprs):u.reg_write(r,0x88770000+i*0x100)
 u.reg_write(UC_X86_REG_RSP,sp);u.reg_write(UC_X86_REG_RBP,stack+0x14000)
 for i,r in enumerate(xmm):u.reg_write(r,0x123456789abcdef0123456789abcdef0+i)

row=layout['runtime'];cases=[]
for base in [0x180000000,0x230000000,0x7ff600000000]:
 host=k.VirtualAlloc(base,0x4000000,0x3000,4);hs=k.VirtualAlloc(stack,ssize,0x3000,4);assert host==base and hs==stack
 try:
  C.memmove(base,image,len(image));u=unicorn.Uc(unicorn.UC_ARCH_X86,unicorn.UC_MODE_64);u.mem_map(base,0x4000000);u.mem_write(base,image);u.mem_map(stack,ssize);seed(u)
  expected=[u.reg_read(r) if r not in [UC_X86_REG_RSP,UC_X86_REG_RIP] else sp+8 if r==UC_X86_REG_RSP else stop for r in nonvol]+[u.reg_read(xmm[i]).to_bytes(16,'little') for i in range(6,16)]
  pc=base+row[0];count=0
  while base+row[0]<=pc<base+row[1]:
   assert unwind(u,base,pc,row)==expected,hex(pc);count+=1
   ins=next(md.disasm(bytes(u.mem_read(pc,15)),pc))
   if ins.mnemonic=='call':pc+=ins.size;u.reg_write(UC_X86_REG_RIP,pc)
   else:u.emu_start(pc,0,count=1);pc=u.reg_read(UC_X86_REG_RIP)
  cases.append(dict(base=hex(base),boundaries=count))
 finally:k.VirtualFree(host,0,0x8000);k.VirtualFree(hs,0,0x8000)
(W/'unwind-validation.json').write_text(json.dumps(dict(status='PASS',windowsRtlVirtualUnwind=True,cases=cases,boundaries=sum(r['boundaries'] for r in cases)),indent=2));print('PASS native Windows unwind for refresh wrapper at',sum(r['boundaries'] for r in cases),'instruction boundaries.')
