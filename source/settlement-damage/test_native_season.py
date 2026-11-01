"""Execute real CE season-selection and particle tick instructions offline."""
from pathlib import Path
import sys,json,struct,hashlib
sys.dont_write_bytecode=True
import native_fixture as f
import unicorn
from unicorn.x86_const import *
if len(sys.argv)!=4:raise SystemExit('Usage: test_native_season.py BASELINE.dll CANDIDATE.dll RECEIPT.json')
W=Path(sys.argv[3]).resolve().parent
BASELINE=Path(sys.argv[1])
CANDIDATE=Path(sys.argv[2])
results=[]
for base in [0x180000000,0x230000000,0x7ff600000000]:
 old=f.mapped(BASELINE,base);new=f.mapped(CANDIDATE,base)
 hooks=[]
 for u in (old,new):
  context=f.HEAP+0x1000;manager=f.HEAP+0x2000;renderer=f.HEAP+0x3000;vtable=f.HEAP+0x4000
  f.q(u,context+0x90,manager);f.d(u,manager+0x13c,0);f.q(u,manager+0x140,f.HEAP+0x8000)
  f.q(u,base+0x3457888,renderer);f.q(u,renderer,vtable);f.q(u,vtable+0x670,f.STOP+0x100)
  hooks.append((u,u.hook_add(unicorn.UC_HOOK_CODE,lambda u,*_:f.ret(u,0),begin=f.STOP+0x100,end=f.STOP+0x100)))
 for present,loaded in [(False,False),(True,False),(True,True)]:
  for battle_season in [0,1,2,3,467,0xcccccccc]:
   for campaign_season in [None,0,1,2,3]:
    values=[]
    for u in (old,new):
     battle=f.HEAP+0x10000;campaign=f.HEAP+0x20000;calendar=f.HEAP+0x30000;records=f.HEAP+0x40000
     f.q(u,base+0x3466658,battle if present else 0);u.mem_write(battle+0x100,bytes([loaded]));f.d(u,battle+0x17a4,battle_season)
     f.q(u,base+0x3466660,campaign if campaign_season is not None else 0)
     f.q(u,campaign+0xc0,calendar);f.q(u,calendar+0x168,records);f.d(u,calendar+0x170,2);f.d(u,records+2*0x50+0x30,campaign_season or 0)
     u.mem_write(base+0x3468c48,b'\1');u.mem_write(base+0x3466650,b'\1');f.d(u,base+0x3466654,0xdeadbeef)
     f.seed(u);u.reg_write(UC_X86_REG_RCX,context);u.reg_write(UC_X86_REG_XMM1,f.floatbits(5.0));before=f.preserved(u)
     f.run(u,base,0x1b9f130)
     assert f.preserved(u)==before
     assert u.reg_read(UC_X86_REG_RSP)==f.SP+16
     values.append(f.rd(u,base+0x3466654))
    expected_old=battle_season if present else campaign_season or 0
    expected_new=battle_season if present and loaded else campaign_season or 0
    assert values==[expected_old,expected_new],(present,loaded,battle_season,campaign_season,values)
    results.append(dict(base=hex(base),battlePresent=present,battleLoaded=loaded,battleSeason=battle_season,campaignSeason=campaign_season,baseline=values[0],candidate=values[1]))
 for u,h in hooks:u.hook_del(h)
 # Real backend tick + real loop update: invalid season freezes an empty
 # looped emitter; a valid campaign season clears pause and activates particles.
 u=new;backend=f.HEAP+0x50000;group=f.HEAP+0x60000;gvt=f.HEAP+0x61000;filters=f.HEAP+0x62000
 info=f.HEAP+0x63000;ivt=f.HEAP+0x64000;emission=f.HEAP+0x65000;render=f.HEAP+0x66000;particles=f.HEAP+0x67000
 f.q(u,group,gvt);f.q(u,gvt+0x98,f.STOP+0x200);u.mem_write(filters+0x68,b'\1\1\1\1')
 f.q(u,info,ivt);f.q(u,ivt+0x68,f.STOP+0x210);f.q(u,ivt+0x58,f.STOP+0x220);f.d(u,render+0x60,0);f.d(u,emission+0x64,f.floatbits(1.0))
 callbacks=[(f.STOP+0x200,lambda u,*_:f.ret(u,filters)),(f.STOP+0x210,lambda u,*_:f.ret(u,emission)),(f.STOP+0x220,lambda u,*_:f.ret(u,render)),(base+0x1ba0c00,lambda u,*_:f.ret(u))]
 hh=[u.hook_add(unicorn.UC_HOOK_CODE,fn,begin=a,end=a) for a,fn in callbacks]
 try:
  u.mem_write(backend,bytes(0xb0));f.q(u,backend+0x28,info);f.q(u,backend+0x38,group);f.q(u,backend+0x40,particles);f.q(u,backend+0x48,10);f.d(u,backend+0x68,f.floatbits(100.0));u.mem_write(backend+0x20,b'\1\1\0')
  for i in range(10):u.mem_write(particles+i*0x28,struct.pack('<ff',0.0,10.0)+bytes(32))
  counts=[]
  for season in [467,2]:
   f.d(u,base+0x3466654,season);f.seed(u);u.reg_write(UC_X86_REG_RCX,backend);u.reg_write(UC_X86_REG_XMM1,f.floatbits(5.0));u.reg_write(UC_X86_REG_R8,0);u.reg_write(UC_X86_REG_R9,0)
   before=f.preserved(u);f.run(u,base,0x1b9fe10);assert f.preserved(u)==before
   counts.append(dict(season=season,paused=bytes(u.mem_read(backend+0x21,1))[0],live=f.rd(u,backend+0x5c)))
  assert counts==[dict(season=467,paused=1,live=0),dict(season=2,paused=0,live=10)],counts
  print('native particle recovery',hex(base),counts)
 finally:
  for h in hh:u.hook_del(h)
receipt=dict(status='PASS',baselineSha256=hashlib.sha256(BASELINE.read_bytes()).hexdigest(),candidateSha256=hashlib.sha256(CANDIDATE.read_bytes()).hexdigest(),selectionCases=len(results),aslrBases=3,realBackendRecoveryAtEachBase=True,results=results,scope='Real native season selection, backend seasonal gate and loop activation; fixture renderer query/metadata getters/bounds update. No live process modification or game launch.')
Path(sys.argv[3]).write_text(json.dumps(receipt,indent=2));print('PASS',len(results),'selection cases + 3 native backend recovery cases')
