"""Execute CE's actual chunk draw dispatcher against an interleaved bucket fixture."""
import sys,struct,json,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
sys.path[:0]=[r'F:/Codex/Temp/unit-selection-runtime',r'F:/Codex/Shogun2-CE/work/disasm_runtime']
import pefile,unicorn
from unicorn.x86_const import *
w=Path(__file__).resolve().parent
path=Path(r'D:/SteamLibrary/steamapps/common/Shogun 2 Complete Edition/empire.retail.x64.dll')
p=pefile.PE(str(path));base=p.OPTIONAL_HEADER.ImageBase
u=unicorn.Uc(unicorn.UC_ARCH_X86,unicorn.UC_MODE_64)
u.mem_map(base,(p.OPTIONAL_HEADER.SizeOfImage+4095)&~4095);u.mem_write(base,p.get_memory_mapped_image())
H=0x60000000;S=0x70000000
u.mem_map(H,0x100000);u.mem_map(S,0x10000)
def q(a,v):u.mem_write(a,struct.pack('<Q',v))
def d(a,v):u.mem_write(a,struct.pack('<I',v))
source=H+0x1000;mesh=H+0x2000;group=H+0x3000;sv=H+0x4000;gv=H+0x5000;mv=H+0x6000;rv=H+0x7000;callback=H+0x8000
names=['C','B','G','A','D','E','F'];actual_order=['C','G','B','A','D','E','F']
effects={n:H+0x10000+i*0x1000 for i,n in enumerate(names)}
for n,e in effects.items():
 r=e+0x200;q(e+0x38,r);q(r,rv);q(r+0x28,H+0xa000);d(r+0x5c,int(n!='G'))
q(rv+0x40,base+0x1b6d140);q(mesh,mv);q(mv+0x158,callback);u.mem_write(callback,b'\xc3')
d(source+0x54,len(names));q(source+0x58,sv);d(source+0x48,0)
for i,n in enumerate(names):q(sv+i*8,effects[n])
d(group+0xc,len(names));q(group+0x10,gv)
for i,n in enumerate(actual_order):q(gv+i*8,effects[n])
seen=[]
def hook(uc,addr,size,user):
 if addr==callback:
  i=uc.reg_read(UC_X86_REG_RDX)&0xffffffff;seen.append(dict(index=i,draws=names[i]))
u.hook_add(unicorn.UC_HOOK_CODE,hook)
stop=H+0x9000;sp=S+0x8008;q(sp,stop)
u.reg_write(UC_X86_REG_RSP,sp);u.reg_write(UC_X86_REG_RCX,source);u.reg_write(UC_X86_REG_RDX,mesh);u.reg_write(UC_X86_REG_R8,group)
u.emu_start(base+0x1a9df80,stop,count=10000)
expected=[n for n in actual_order if n!='G']
receipt=dict(status='REPRODUCED',nativeFunction='0x181a9df80',sourceOrder=names,bucketOrder=actual_order,invisibleEmitter='G',expectedDraws=expected,actualDraws=seen,missing=list(set(expected)-{x['draws'] for x in seen}),incorrectlyDrawn=[x['draws'] for x in seen if x['draws']=='G'],scope='Offline execution of original native dispatcher. Synthetic bucket ordering and visibility, not an in-game capture.')
assert receipt['missing']==['B'] and receipt['incorrectlyDrawn']==['G'],receipt
(w/'native-draw-mapping-reproduction.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
