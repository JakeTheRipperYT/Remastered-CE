"""Real release, rectangle collector, plane hit tests and ID conversion; fixture world/camera."""
from pathlib import Path
import sys,struct,json,itertools
sys.dont_write_bytecode=True

import pefile,unicorn,capstone
from unicorn.x86_const import *
if len(sys.argv)!=4:raise SystemExit('Usage: test_refresh.py CE57.dll CE58.dll OUTPUT_DIRECTORY')
W=Path(sys.argv[3]);W.mkdir(parents=True,exist_ok=True)
H=0x60000000;S=0x70000000;SP=S+0x8000;STOP=S+0xf000;O=H+0x1000;C=O+0x2a8
B=H+0x10000;ARMY=H+0x40000;M=H+0x50000;V=H+0x51000;land=[H+0x60000+i*0x2000 for i in range(3)];ship=H+0x68000
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);md.detail=True
rows=[]
for edition,path in [('57',sys.argv[1]),('58',sys.argv[2])]:
 p=pefile.PE(path,fast_load=True);base=p.OPTIONAL_HEADER.ImageBase;u=unicorn.Uc(unicorn.UC_ARCH_X86,unicorn.UC_MODE_64)
 u.mem_map(base,(p.OPTIONAL_HEADER.SizeOfImage+4095)&~4095);u.mem_write(base,p.get_memory_mapped_image());u.mem_map(H,0x100000);u.mem_map(S,0x10000)
 def q(a,v):u.mem_write(a,struct.pack('<Q',v))
 def d(a,v):u.mem_write(a,struct.pack('<I',v))
 def rq(a):return struct.unpack('<Q',u.mem_read(a,8))[0]
 def rd(a):return struct.unpack('<I',u.mem_read(a,4))[0]
 def vec(a,v):u.mem_write(a,struct.pack('<'+'f'*len(v),*v))
 def xy(x,y):vec(C+0x78,[(x+1)/2,(1-y)/2])
 q(O+0x2b0,B);q(C+0xe0,ARMY);q(O+0xbe0,M);q(M,V);q(V+0xa8,H+0xf050)
 q(O+0x15e0,H+0x52000);q(H+0x52000,H+0x53000)
 q(B+0x28068,H+0x20000);q(H+0x20000,H+0x21000);q(H+0x21000,H+0x22000);q(H+0x22000+0x100,H+0xf040)
 d(ARMY+0x220,3);q(ARMY+0x228,H+0x43000)
 for i,obj in enumerate(land):
  q(H+0x43000+i*8,obj);q(obj+0x20,H+0x44000);q(H+0x44000,H+0xf020);q(H+0x44010,H+0xf010)
  group=obj+0x1400;point=obj+0x1600;q(obj+0x1128,group);d(group+0x28,1);q(group+0x30,group+0x100);q(group+0x100,point)
  vec(point+0x78,[(.1,.1,1),(.8,.8,1),(-.1,-.1,1)][i])
 d(ARMY+0x248,1);q(ARMY+0x250,H+0x43100);q(H+0x43100,ship)
 q(ship,H+0x45000);q(H+0x45000,H+0xf030);q(ship+0x248,H+0x46000);q(H+0x46000,H+0xf020);q(H+0x46010,H+0xf010);vec(ship+0x100,[.15,-.1,1])
 d(C+0xb8,8);q(C+0xc0,H+0x47000);d(C+0xc8,8);q(C+0xd0,H+0x48000)
 d(base+0x3373e08,8);q(base+0x3373e10,H+0x49000)
 u.reg_write(UC_X86_REG_GS_BASE,H+0x80000);q(H+0x80058,H+0x81000);q(H+0x81000,H+0x82000);d(H+0x82068,0x7fffffff)
 state={};layout=json.loads(Path(__file__).with_name('refresh-layout.json').read_text())
 def reg(name):return u.reg_read(globals()['UC_X86_REG_'+name.upper()]) if name else 0
 def target(i):
  o=i.operands[0]
  if o.type==capstone.x86.X86_OP_IMM:return o.imm
  if o.type==capstone.x86.X86_OP_REG:return reg(md.reg_name(o.reg))
  return rq(reg(md.reg_name(o.mem.base))+reg(md.reg_name(o.mem.index))*o.mem.scale+o.mem.disp)
 def hook(u,a,n,_):
  i=next(md.disasm(bytes(u.mem_read(a,n)),a))
  if i.mnemonic!='call':return
  t=target(i);rcx=reg('rcx');rdx=reg('rdx');value=0
  actual=[0x400400,0x404700,0x21d5c0,0x23f320,0x45e3f0,0x403470,0x132d60,0x19adbf0,0x2d64a0,0x16585c0,layout['startRva']]
  if t-base in actual:
   if t-base==0x45e3f0:state['refreshes']+=1
   return
  if t==H+0xf010:
   uid=101+land.index(rcx-0x20) if rcx-0x20 in land else 201
   value=int(uid in state['eligible'])
  elif t==H+0xf020:value=101+land.index(rcx-0x20) if rcx-0x20 in land else 201
  elif t==H+0xf030:value=ship+0x100
  elif t==H+0xf040:value=H+0x23000
  elif t==H+0xf050:
   count=rd(rdx+4);state['selected']=list(struct.unpack('<'+'I'*count,u.mem_read(rq(rdx+8),count*4))) if count else []
  elif t-base==0x1993940:
   # Camera fixture: identity orthographic view. Native hit testing remains real.
   fl=lambda r:struct.unpack('<f',struct.pack('<I',reg(r)&0xffffffff))[0]
   x=fl('xmm2');y=fl('xmm3');sx,sy=struct.unpack('<ff',u.mem_read(reg('rsp')+0x20,4)+u.mem_read(reg('rsp')+0x28,4))
   lo,hi=sorted([x,sx]);bottom,top=sorted([y,sy])
   planes=[1,0,0,-lo,-1,0,0,hi,0,1,0,-bottom,0,-1,0,top,0,0,1,0,0,0,-1,10]
   u.mem_write(rdx,bytes(448));vec(rdx,planes);value=rdx
  elif t-base==0x19fe50:value=H+0x54000
  elif t-base in [0x147a4e0,0x12a860,0x19fe10]:value=0
  else:raise AssertionError((edition,hex(a),hex(t)))
  u.reg_write(UC_X86_REG_RAX,value);u.reg_write(UC_X86_REG_RIP,a+n)
 u.hook_add(unicorn.UC_HOOK_CODE,hook)
 def run(address):
  u.reg_write(UC_X86_REG_RCX,C if address==0x45e3f0 else O);u.reg_write(UC_X86_REG_RDX,0);u.reg_write(UC_X86_REG_RSP,SP);q(SP,STOP)
  u.emu_start(base+address,STOP,count=100000);assert reg('rip')==STOP
 for preview,reverse,kind in itertools.product(['none','empty old rectangle','different old rectangle','correct rectangle'],range(4),['mixed','land','ships','none']):
  eligible={'mixed':[101,102,103,201],'land':[101,102,103],'ships':[201],'none':[]}[kind]
  state.clear();state.update(refreshes=0,selected=[],eligible=eligible);d(C+0xbc,0);d(C+0xcc,0);d(base+0x3373e0c,0)
  u.mem_write(C+0xa4,b'\1');vec(C+0xac,[-.3,.3]);xy(.3,-.3)
  if preview!='none':
   if preview=='empty old rectangle':vec(C+0xac,[-.9,-.9]);xy(-.7,-.7)
   elif preview=='different old rectangle':vec(C+0xac,[.7,.9]);xy(.9,.7)
   run(0x45e3f0)
  ax,ex=(-.3,.3) if reverse&1==0 else (.3,-.3)
  ay,ey=(.3,-.3) if reverse&2==0 else (-.3,.3)
  vec(C+0xac,[ax,ay]);xy(ex,ey);u.mem_write(C+0xa4,b'\1');q(O+0x2d8,0)
  cached=[rd(C+0xbc),rd(C+0xcc)];before=state['refreshes'];run(0x1655290)
  expected=[i for i in [101,103,201] if i in eligible]
  if edition=='58':assert state['selected']==expected,(preview,state)
  elif preview=='correct rectangle':assert state['selected']==expected
  elif expected:assert state['selected']!=expected,(preview,state)
  if edition=='58':assert state['refreshes']-before==1
  rows.append(dict(edition=edition,preview=preview,direction=reverse,eligibleKind=kind,cachedCounts=cached,selected=state['selected'],releaseRefreshes=state['refreshes']-before))
 for active,dx,dy,group in [(True,0,0,False),(True,.02,.02,False),(False,.6,.6,False),(True,.6,.6,True)]:
  state.clear();state.update(refreshes=0,selected=[999],eligible=[101,102,103,201]);d(base+0x3373e0c,0)
  vec(C+0xac,[0,0]);xy(dx,dy);u.mem_write(C+0xa4,bytes([active]));u.mem_write(O+0x31c,bytes([group]));q(O+0x2d8,0)
  run(0x1655290);assert state['selected']==[999] and state['refreshes']==0
  u.mem_write(O+0x31c,b'\0')
  rows.append(dict(edition=edition,case='click/small/cancel/group exclusion',active=active,dx=dx,dy=dy,group=group,selected=state['selected']))
receipt=dict(status='PASS',cases=rows,scope='Complete native release, native rectangle scan, actual native plane-bound tests, native vector append and ID conversion. Only camera/frustum generation, world ownership, allocation and final selection consumer are fixtures. Mixed land/ship IDs inside final box must match with zero, stale or current previews.')
(W/'refresh-validation.json').write_text(json.dumps(receipt,indent=2));print('PASS: native57 reproduces empty/stale fast-box results;58 selects actual contained land/ship IDs for all preview timings.')
