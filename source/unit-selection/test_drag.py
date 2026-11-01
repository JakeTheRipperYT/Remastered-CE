"""Execute real OG/CE drag predicates and the complete CE release handler offline."""
from pathlib import Path
import sys,struct,json,random
sys.dont_write_bytecode=True

import pefile,unicorn,capstone
from unicorn.x86_const import *
if len(sys.argv)!=5:raise SystemExit('Usage: test_drag.py OG.dll CE56.dll CE57.dll OUTPUT_DIRECTORY')
W=Path(sys.argv[4]);W.mkdir(parents=True,exist_ok=True)
paths=dict(zip(['og','ce56','ce57'],sys.argv[1:4]))
H=0x60000000;S=0x70000000;SP=S+0x8000;STOP=S+0xf000;O=H+0x1000;M=H+0x5000;V=H+0x6000
images={};predictions={};release_results=[]
def f32(x):return struct.unpack('<f',struct.pack('<f',x))[0]
def d(u,a,v):u.mem_write(a,struct.pack('<I',v))
def q(u,a,v):u.mem_write(a,struct.pack('<Q',v))
def coords(u,o,ce,dx,dy):
 u.mem_write(o+(0x78 if ce else 0x30),struct.pack('<ff',f32(.5+dx/2),f32(.5-dy/2)))
 u.mem_write(o+(0xac if ce else 0x60),bytes(8));u.mem_write(o+(0xa4 if ce else 0x58),b'\1')
random.seed(57)
grid=[(a,b) for a in [-.1,-.031,-.03,-.029,-.001,0,.001,.029,.03,.031,.1] for b in [-.1,-.031,-.03,-.029,-.001,0,.001,.029,.03,.031,.1]]
grid += [(random.uniform(-.08,.08),random.uniform(-.08,.08)) for _ in range(3000)]
for name,path in paths.items():
 ce=name!='og';p=pefile.PE(path,fast_load=True);base=p.OPTIONAL_HEADER.ImageBase;images[name]=(p,base)
 u=unicorn.Uc(unicorn.UC_ARCH_X86,unicorn.UC_MODE_64 if ce else unicorn.UC_MODE_32)
 u.mem_map(base,(p.OPTIONAL_HEADER.SizeOfImage+4095)&~4095);u.mem_write(base,p.get_memory_mapped_image());u.mem_map(H,0x100000);u.mem_map(S,0x10000)
 values=[]
 for dx,dy in grid:
  coords(u,O,ce,dx,dy);u.reg_write(UC_X86_REG_RCX if ce else UC_X86_REG_ECX,O)
  u.reg_write(UC_X86_REG_RSP if ce else UC_X86_REG_ESP,SP)
  u.mem_write(SP,struct.pack('<Q' if ce else '<I',STOP));u.emu_start(base+(0x400400 if ce else 0x2e98f0),STOP,count=1000)
  values.append(u.reg_read(UC_X86_REG_RAX if ce else UC_X86_REG_EAX)&255)
 predictions[name]=values
assert predictions['ce57']==predictions['og'],'Candidate must match real OG predicate for every displacement'
assert predictions['ce56']!=predictions['og']
for name in ['ce56','ce57']:
 p,base=images[name];u=unicorn.Uc(unicorn.UC_ARCH_X86,unicorn.UC_MODE_64)
 u.mem_map(base,(p.OPTIONAL_HEADER.SizeOfImage+4095)&~4095);u.mem_write(base,p.get_memory_mapped_image());u.mem_map(H,0x100000);u.mem_map(S,0x10000)
 # TLS initialization is fixture state; no OS or live process is accessed.
 u.reg_write(UC_X86_REG_GS_BASE,H+0x80000);q(u,H+0x80058,H+0x81000);q(u,H+0x81000,H+0x82000);d(u,H+0x82068,0x7fffffff)
 md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);md.detail=True
 state={}
 def ret(value=0):
  sp=u.reg_read(UC_X86_REG_RSP);pc=struct.unpack('<Q',u.mem_read(sp,8))[0];u.reg_write(UC_X86_REG_RAX,value);u.reg_write(UC_X86_REG_RSP,sp+8);u.reg_write(UC_X86_REG_RIP,pc)
 def hook(u,a,n,_):
  if a==base+0x1648660:state['selected']=0;state['directClear']+=1;ret();return
  i=next(md.disasm(bytes(u.mem_read(a,n)),a))
  if i.mnemonic!='call':return
  if i.operands[0].type!=capstone.x86.X86_OP_IMM:
   state['selected']=0;state['boxReplace']+=1;u.reg_write(UC_X86_REG_RIP,a+n);return
  t=i.operands[0].imm-base
  if t in [0x400400,0x21d5c0,0x23f320]:return
  # GuardGroundClear is real candidate56 code, retained unchanged in57.
  if t==0x2159b68:return
  stubs={0x5bc6f0:0,0x403420:1,0x3f9d40:0,0x147a4e0:0,0x5d7d80:1,0x16585c0:0,0x12a860:0}
  assert t in stubs,(name,hex(a),hex(t))
  if t==0x16585c0:state['collectBox']+=1
  u.reg_write(UC_X86_REG_RAX,stubs[t]);u.reg_write(UC_X86_REG_RIP,a+n)
 u.hook_add(unicorn.UC_HOOK_CODE,hook)
 layout=json.loads(Path(__file__).with_name('fix-layout.json').read_text())
 for dx,dy,label in [(0,0,'stationary'),(.001,.001,'tiny diagonal'),(.02,.02,'below OG threshold'),(.04,.04,'deliberate box'),(.1,0,'horizontal only'),(0,.1,'vertical only')]:
  state.clear();state.update(selected=1,directClear=0,boxReplace=0,collectBox=0)
  u.mem_write(O,bytes(0x2000));q(u,O+0xbe0,M);q(u,M,V);q(u,V+0xa8,H+0xf000);q(u,O+0x2d8,H+0x9000)
  q(u,O+0x15e0,H+0xa000);q(u,H+0xa000,H+0xb000)
  coords(u,O+0x2a8,True,dx,dy);q(u,base+layout['stateRva'],O)
  d(u,base+0x3373e0c,0);q(u,base+0x3373e10,0)
  u.reg_write(UC_X86_REG_RCX,O);u.reg_write(UC_X86_REG_RDX,0);u.reg_write(UC_X86_REG_RSP,SP);q(u,SP,STOP)
  u.emu_start(base+0x1655290,STOP,count=10000)
  expected_box=dx!=0 and dy!=0 and (name=='ce56' or abs(dx)>.03 and abs(dy)>.03)
  assert state['boxReplace']==int(expected_box),(name,label,state)
  assert state['selected']==int(not expected_box),(name,label,state)
  release_results.append(dict(edition=name,case=label,**state))
receipt=dict(status='PASS',realPredicateCasesPerEngine=len(grid),realPredicateEngines=3,ce57MatchesOGExactly=True,ce56DiffersFromOG=True,completeNativeReleaseCases=release_results,scope='Actual native predicate and complete release handler. Only picking/UI/selection collection dependencies are fixtures; fixture rectangle contains no units. No live process access.')
(W/'drag-validation.json').write_text(json.dumps(receipt,indent=2))
print('PASS:',len(grid),'predicate cases per engine match OG; complete release reproduces56 failure and57 retention for small diagonal motion.')
