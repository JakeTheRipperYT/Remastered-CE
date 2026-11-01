"""Offline execution of native click handlers; UI/picking dependencies are fixtures."""
import sys,pathlib,struct,json,hashlib,itertools
sys.dont_write_bytecode=True

import pefile,capstone,unicorn
from unicorn.x86_const import *
if len(sys.argv)!=6:raise SystemExit('Usage: test_native_selection.py VANILLA_CE.dll CUMULATIVE55.dll OG.dll CANDIDATE56.dll OUTPUT_DIRECTORY')
W=pathlib.Path(sys.argv[5]);W.mkdir(parents=True,exist_ok=True)
PATHS=dict(zip(['vanilla_ce','patched_ce_055','og','candidate'],sys.argv[1:5]))
results=[];identities={};regions={}
for edition,path in PATHS.items():
 raw=pathlib.Path(path).read_bytes();p=pefile.PE(data=raw,fast_load=True);base=p.OPTIONAL_HEADER.ImageBase
 ce=edition!='og';bits=64 if ce else 32;word=8 if ce else 4;fmt='<Q' if ce else '<I'
 identities[edition]={'path':path,'sha256':hashlib.sha256(raw).hexdigest()}
 down=base+(0x1654f60 if ce else 0x10f81e0);up=base+(0x1655290 if ce else 0x10f83e0)
 regions[edition]={'pressSha256':hashlib.sha256(p.get_data(down-base,0x330 if ce else 0x1f7)).hexdigest(),
 'releaseDecisionSha256':hashlib.sha256(p.get_data(up-base,0x1f1 if ce else 0x147)).hexdigest()}
 scenarios=[(a,b,c,0,0,0) for a,b,c in itertools.product([False,True],repeat=3)] if ce else [(True,False,0,0,0,0),(True,True,0,0,0,0),(False,False,1,0,0,0)]
 if ce:
  scenarios += [(a,b,c,mod,0,0) for a,b,c in itertools.product([False,True],repeat=3) for mod in [0xba6,0xba7,0xba8]]
  scenarios += [(a,b,c,0,block,cancel) for a,b,c in itertools.product([False,True],repeat=3) for block,cancel in [(1,0),(0,1)]]
 for press_unit,release_unit,initial,modifier,ui_block,cancel in scenarios:
  u=unicorn.Uc(unicorn.UC_ARCH_X86,unicorn.UC_MODE_64 if ce else unicorn.UC_MODE_32)
  u.mem_map(base,(p.OPTIONAL_HEADER.SizeOfImage+4095)&~4095);u.mem_write(base,p.get_memory_mapped_image())
  H=0x60000000;S=0x70000000;O=H+0x1000;M=H+0x5000;V=H+0x8000;P=H+0xa000;UI=H+0xc000
  u.mem_map(H,0x100000);u.mem_map(S,0x10000)
  def put(a,v):u.mem_write(a,struct.pack(fmt,v))
  def byte(a,v):u.mem_write(a,bytes([v]))
  put(M,V);put(V+(0x98 if ce else 0x4c),H+0xf000)
  put(O+(0xbe0 if ce else 0x5b4),M);put(O+(0x2d8 if ce else 0x130),P)
  put(O+(0x15e0 if ce else 0xd0c),UI);put(UI,UI+0x100)
  u.mem_write(O+(0x1670 if ce else 0xd4c),struct.pack('<I',5))
  if modifier:byte(O+modifier,1)
  state={'phase':'press','owned':press_unit,'selected':int(initial),'selectCalls':0,'deselectCalls':0}
  m=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64 if ce else capstone.CS_MODE_32);m.detail=True
  queries={
   base+(0x5bc6f0 if ce else 0x4622f0):(ui_block,0 if ce else 4),
   base+(0x403420 if ce else 0x2ec400):(1,0),
   base+(0x3f9d40 if ce else 0x2e4ed0):('owned',0 if ce else 4),
   base+(0x43a200 if ce else 0x319000):(42,0),
   base+(0x5b08e0 if ce else 0x0):('selected',0),
   base+(0x147a4e0 if ce else 0xf90dd0):(0,0 if ce else 4),
   base+(0x5d7d80 if ce else 0x47d020):('selected',0),
   base+(0x5d7d40 if ce else 0x47cff0):(0,0),
   base+(0x12ef60 if ce else 0x955f0):(0,0),
   base+(0x1648660 if ce else 0x10eef50):('clear',0),
   base+0x3a90a0:(H+0xe000,0),base+0x4d6cb0:(H+0xe000,0)}
  def hook(u,a,n,_):
   if state['phase']=='release' and a==base+(0x1655481 if ce else 0x10f8527):u.emu_stop();return
   i=next(m.disasm(bytes(u.mem_read(a,n)),a))
   if i.mnemonic.startswith('ret') and down<=a<up:u.emu_stop();return
   if edition=='candidate' and a==base+0x1648660:
    state['selected']=0;state['deselectCalls']+=1
    sp=u.reg_read(UC_X86_REG_RSP);target=struct.unpack('<Q',u.mem_read(sp,8))[0]
    u.reg_write(UC_X86_REG_RSP,sp+8);u.reg_write(UC_X86_REG_RIP,target);return
   if i.mnemonic!='call':return
   if i.operands[0].type==capstone.x86.X86_OP_IMM:
    target=i.operands[0].imm
    if edition=='candidate' and target not in queries:return
    assert target in queries,(edition,hex(a),hex(target))
    value,cleanup=queries[target]
    if value=='owned':value=int(state['owned'])
    elif value=='selected':value=state['selected']
    elif value=='clear':state['selected']=0;state['deselectCalls']+=1;value=0
   else:
    assert ce or a in [base+0x10f83b2,base+0x10f8455],(edition,hex(a))
    state['selected']=1;state['selectCalls']+=1;value=0;cleanup=0 if ce else 8
   u.reg_write(UC_X86_REG_RAX if ce else UC_X86_REG_EAX,value)
   if cleanup:u.reg_write(UC_X86_REG_ESP,u.reg_read(UC_X86_REG_ESP)+cleanup)
   u.reg_write(UC_X86_REG_RIP if ce else UC_X86_REG_EIP,a+n)
  u.hook_add(unicorn.UC_HOOK_CODE,hook)
  def run(addr):
   u.reg_write(UC_X86_REG_RCX if ce else UC_X86_REG_ECX,O)
   u.reg_write(UC_X86_REG_RDX if ce else UC_X86_REG_EDX,cancel if state['phase']=='release' else 0)
   sp=S+0x8000;u.reg_write(UC_X86_REG_RSP if ce else UC_X86_REG_ESP,sp)
   u.mem_write(sp,bytes(64));u.emu_start(addr,base+p.OPTIONAL_HEADER.SizeOfImage,count=10000)
  run(down);after_press=state['selected'];latch=bytes(u.mem_read(O+(0x351 if ce else 0xca4),1))[0]
  state['phase']='release';state['owned']=release_unit;run(up)
  if not modifier and not ui_block and not cancel:
   expected=int(release_unit or (press_unit and (not ce or edition=='candidate')))
   assert state['selected']==expected,(edition,state)
  row=dict(edition=edition,pressOnUnit=press_unit,releaseOnUnit=release_unit,initialSelected=initial,modifier=modifier,uiBlocked=ui_block,cancelled=cancel,afterPress=after_press,pressLatch=latch,afterRelease=state['selected'],deselectCalls=state['deselectCalls'])
  if edition=='candidate':
   original=next(r for r in results if r['edition']=='vanilla_ce' and all(r[k]==row[k] for k in ['pressOnUnit','releaseOnUnit','initialSelected','modifier','uiBlocked','cancelled']))
   intentional=press_unit and not release_unit and not modifier and not ui_block and not cancel
   assert row['afterPress']==original['afterPress'] and row['pressLatch']==original['pressLatch']
   if not intentional:assert row['afterRelease']==original['afterRelease'],(row,original)
   if not modifier and not ui_block and not cancel and press_unit:
    # A second release without a press cannot reuse the consumed latch.
    state['owned']=False;run(up);assert state['selected']==0
    row['secondReleaseCannotReuseClick']=True
  results.append(row)
assert regions['vanilla_ce']==regions['patched_ce_055']
receipt=dict(status='PASS',scope='Native handler branches executed offline. Picking, UI blocking and selection-manager calls are fixture inputs; no live mouse/game reproduction.',identities=identities,regions=regions,cases=results)
(W/'native-selection-results.json').write_text(json.dumps(receipt,indent=2))
print('PASS',len(results),'native handler cases; candidate differences limited to consumed ordinary unit clicks.')
