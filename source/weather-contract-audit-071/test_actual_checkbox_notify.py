from pathlib import Path
import sys,struct,json
sys.path.insert(0,str(Path(__file__).parent))
import test_controller_native as n
import pefile,capstone
w=Path(__file__).parent
p=pefile.PE(str(w/'candidate-engine-edited.bin'),fast_load=True)
results=[]
for base in [0x180000000,0x230000000,0x7ff600000000]:
 f=n.Fixture(base);f.load();comp=0x220000;checkbox=0x230000;state=0x240000;event_values=[]
 f.narrow(comp+0x110,'rce_campaign_always_night',0x246000);f.wq(checkbox+8,comp);f.wq(comp+0x158,state)
 code=p.get_data(0x15a4940,0x1d0);f.u.mem_write(base+0x15a4940,code)
 md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);md.detail=True
 for ins in md.disasm(code,0x15a4940):
  for op in ins.operands:
   if op.type==capstone.x86.X86_OP_MEM and op.mem.base==capstone.x86.X86_REG_RIP:
    r=ins.address+ins.size+op.mem.disp;f.u.mem_write(base+r,p.get_data(r,160))
 scratch=[0x290000]
 def wide(a):return bytes(f.u.mem_read(f.q(a+16),f.q(a)*2)).decode('utf-16-le')
 def wide_write(a,s):
  at=scratch[0];scratch[0]+=0x1000;f.u.mem_write(at,s.encode('utf-16-le')+b'\0\0');f.u.mem_write(a,struct.pack('<QQQ',len(s),len(s),at))
 def native_state():f.ret(f.q(f.reg(n.UC_X86_REG_RCX)+0x158)+0x20)
 def narrow_ctor():
  out=f.reg(n.UC_X86_REG_RCX);data=f.reg(n.UC_X86_REG_RDX);size=f.reg(n.UC_X86_REG_R8)&65535
  f.u.mem_write(out,struct.pack('<QQQ',size,size,data));f.ret(out)
 def wide_from_narrow():
  out=f.reg(n.UC_X86_REG_RCX);wide_write(out,f.narrow_value(f.reg(n.UC_X86_REG_RDX)));f.ret(out)
 def wide_from_literal():
  out=f.reg(n.UC_X86_REG_RCX);data=f.reg(n.UC_X86_REG_RDX);raw=bytes(f.u.mem_read(data,100)).split(b'\0')[0];wide_write(out,raw.decode());f.ret(out)
 def find():f.ret(wide(f.reg(n.UC_X86_REG_RCX)).find(wide(f.reg(n.UC_X86_REG_RDX))))
 def signal():
  at=f.reg(n.UC_X86_REG_RDX);event_values.append(bytes(f.u.mem_read(at+8,1))[0]);f.ret()
 f.handlers.update({0x14708a0:native_state,0x199820:narrow_ctor,0x199d50:wide_from_narrow,0x199e70:wide_from_literal,0x1a3640:find,0x19a360:f.string_dtor,0x138d640:signal})
 n.layout['exports']['NativeCheckboxNotify']=0x15a4940
 for state_name,expected in [('down',1),('selected_down_off',0),('down',1),('selected_down',0)]:
  f.narrow(state+0x20,state_name,0x247000);f.call('NativeCheckboxNotify',checkbox)
  assert event_values[-1]==expected,(state_name,event_values)
  assert f.flags['RCE_AlwaysNightCampaign']==(1 if expected else -1),(state_name,f.flags)
 results.append(dict(base=hex(base),nativeNotificationCases=len(event_values),values=event_values))
result=dict(status='PASS',actualCECheckboxNotifyMachineCodeExecuted=True,bothPatchedNativeCallsitesExecuted=True,results=results)
(w/'actual-checkbox-notify-tests.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
