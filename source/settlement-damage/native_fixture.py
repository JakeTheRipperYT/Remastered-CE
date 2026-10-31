"""Small offline x64 fixture. Requires pefile and Unicorn; never opens a process."""
import struct
import pefile,unicorn
from unicorn.x86_const import *

HEAP=0x600000000;STACK=0x710000000;SP=STACK+0x18000;STOP=0x700000000
GPRS=[UC_X86_REG_RAX,UC_X86_REG_RBX,UC_X86_REG_RCX,UC_X86_REG_RDX,UC_X86_REG_RSI,UC_X86_REG_RDI,UC_X86_REG_RBP,UC_X86_REG_R8,UC_X86_REG_R9,UC_X86_REG_R10,UC_X86_REG_R11,UC_X86_REG_R12,UC_X86_REG_R13,UC_X86_REG_R14,UC_X86_REG_R15]
NV=[UC_X86_REG_RBX,UC_X86_REG_RBP,UC_X86_REG_RSI,UC_X86_REG_RDI,UC_X86_REG_R12,UC_X86_REG_R13,UC_X86_REG_R14,UC_X86_REG_R15]
XMMS=[globals()['UC_X86_REG_XMM'+str(i)] for i in range(16)]

def mapped(path,base):
 p=pefile.PE(str(path),fast_load=True);p.parse_data_directories(directories=[5])
 b=bytearray(p.get_memory_mapped_image());delta=base-p.OPTIONAL_HEADER.ImageBase
 if delta:
  for block in p.DIRECTORY_ENTRY_BASERELOC:
   for e in block.entries:
    if not e.type:continue
    assert e.type==10
    struct.pack_into('<Q',b,e.rva,(struct.unpack_from('<Q',b,e.rva)[0]+delta)&0xffffffffffffffff)
 u=unicorn.Uc(unicorn.UC_ARCH_X86,unicorn.UC_MODE_64)
 u.mem_map(base,(p.OPTIONAL_HEADER.SizeOfImage+4095)&~4095);u.mem_write(base,bytes(b))
 u.mem_map(HEAP,0x1000000);u.mem_map(STACK,0x40000);u.mem_map(STOP,4096)
 return u

def q(u,a,*v):u.mem_write(a,struct.pack('<'+'Q'*len(v),*v))
def d(u,a,*v):u.mem_write(a,struct.pack('<'+'I'*len(v),*(x&0xffffffff for x in v)))
def rq(u,a):return struct.unpack('<Q',u.mem_read(a,8))[0]
def rd(u,a):return struct.unpack('<I',u.mem_read(a,4))[0]
def floatbits(x):return struct.unpack('<I',struct.pack('<f',x))[0]
def seed(u):
 for i,r in enumerate(GPRS):u.reg_write(r,0x44000000+i*0x101)
 for i,r in enumerate(XMMS):u.reg_write(r,0x112233445566778899aabbccddeeff00+i)
 u.reg_write(UC_X86_REG_RSP,SP+8);q(u,SP+8,STOP)
 u.reg_write(UC_X86_REG_EFLAGS,0x202);u.reg_write(UC_X86_REG_MXCSR,0x1f80)
def preserved(u):return [u.reg_read(r) for r in NV+XMMS[6:]]
def ret(u,value=None):
 if value is not None:u.reg_write(UC_X86_REG_RAX,value)
 sp=u.reg_read(UC_X86_REG_RSP);target=rq(u,sp)
 u.reg_write(UC_X86_REG_RSP,sp+8);u.reg_write(UC_X86_REG_RIP,target)
def run(u,base,rva,count=2000000):
 u.emu_start(base+rva,STOP,count=count)
 assert u.reg_read(UC_X86_REG_RIP)==STOP,hex(u.reg_read(UC_X86_REG_RIP))
