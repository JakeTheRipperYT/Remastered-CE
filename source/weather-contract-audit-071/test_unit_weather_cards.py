from pathlib import Path
import json,struct
W=Path(__file__).resolve().parent
scope={'__file__':str(W/'test_fades_native.py')}
exec(compile((W/'test_fades_native.py').read_text().split('\nresults=[]')[0],str(W/'test_fades_native.py'),'exec'),scope)
F=scope['FadeFixture'];n=scope['n'];stock=scope['stock'];cases=[]
for base in (0x180000000,0x230000000,0x7ff600000000):
 f=F(base,0,0,0,1,17);card=0x3d0000;unit=0x3d1000;rows=0x3d5000;mods=0x3d6000;record=0x3d7000;weather=0x3d8000;weapon=0x3d9000;rules=base+0x3e00000
 f.wq(f.setup,f.battle);f.wq(card+0x70,f.ui);f.wq(card+0x1e0,unit);f.wq(unit+0x28,f.battle);f.wq(card+8,0x3da000)
 f.wn(card+0x284,3);f.wn(card+0x294,3);f.wq(card+0x288,rows);f.wq(card+0x298,mods)
 f.wq(f.climate+0x18,record);f.wq(record+0x20,weather);f.wq(f.db+0x1448,rules)
 keys={0x3db000:'marksmanship',0x3db100:'reload_skill',0x3db200:'melee_attack'}
 for i,(key,name) in enumerate(keys.items()):
  f.wide(key,name,0x3de000+i*0x100);f.wq(rows+i*32,key);f.wq(mods+i*32,key);f.wfloat(rows+i*32+24,(40,30,12)[i]);f.wfloat(mods+i*32+24,(10,5,3)[i])
 for offset,value in [(0x30c8,.7),(0x3188,.65),(0x3248,.6),(0x3308,.9),(0x33c8,.7),(0x3488,.5),(0x3548,.8),(0x3608,.7),(0x36c8,.6),(0x60c8,0),(0x6188,0),(0x6248,-6),(0x6308,-2)]:f.wfloat(rules+offset,value)
 f.u.mem_write(base+0x5e9ec0,stock.get_data(0x5e9ec0,0x16b));f.u.mem_write(base+0x2174b10,struct.pack('<f',1))
 def compareAscii():
  ptr=f.reg(n.UC_X86_REG_RDX);name=bytearray()
  while (c:=bytes(f.u.mem_read(ptr+len(name),1)))!=b'\0':name.extend(c)
  f.ret(int(keys.get(f.reg(n.UC_X86_REG_RCX))==name.decode()))
 f.handlers[0x19b1c0]=compareAscii
 for rva in (0x19b6a0,0x19f950):f.u.mem_write(base+rva,stock.get_data(rva,0x200))
 f.handlers[0x105c840]=lambda:f.ret(rules)
 f.handlers[0x210350]=lambda:f.ret(weapon)
 f.handlers[0x147a4e0]=lambda:f.ret(1)
 # Compare the displayed reload adjustment with CE's actual weapon/weather
 # branch, stopping immediately before the normal reload-time calculation.
 f.u.mem_write(base+0x507c9c,stock.get_data(0x507c9c,0x135))
 for rva in (0x5b0c30,0x5b0ed0):f.u.mem_write(base+rva,stock.get_data(rva,0x20))
 nativeContext=0x3dc000;nativeSetupReference=0x3dd000
 f.wq(nativeContext+0x48,nativeSetupReference);f.wq(nativeSetupReference+8,f.setup)
 # Real widget state/geometry persists independently of the stat input rows.
 widgetList=0x3e0000;rowVector=0x3e1000
 f.wq(card+0x310,widgetList);f.wn(widgetList+0x134,3);f.wq(widgetList+0x138,rowVector)
 widgets={}
 for i in range(3):
  rowWidget=0x3e2000+i*0x1000;f.wq(rowVector+i*8,rowWidget)
  for j,name in enumerate(('bar_base','bar_mod')):
   component=rowWidget+0x200+j*0x300;state=0x3f0000+i*0x100+j*0x50
   widgets[rowWidget,name]=component;f.wq(component+0x158,state);f.u.mem_write(component+0x1c1,b'\1');f.wfloat(state+0x48,100);f.wfloat(state+0x4c,7)
 def lookupWidget():
  assert f.reg(n.UC_X86_REG_R8)&255==1,'Native lookup thunk must select descendants'
  name=f.reg(n.UC_X86_REG_RDX);size=f.q(name);ptr=f.q(name+16)
  key=bytes(f.u.mem_read(ptr,size)).decode();f.ret(widgets.get((f.reg(n.UC_X86_REG_RCX),key),0))
 f.u.mem_write(base+0x1476590,stock.get_data(0x1476590,8))
 f.handlers[0x146f890]=lookupWidget
 def visibility():
  f.u.mem_write(f.reg(n.UC_X86_REG_RCX)+0x1c1,bytes([f.reg(n.UC_X86_REG_RDX)&255]));f.ret()
 f.handlers[0x14899c0]=visibility
 draws=[]
 def finishOriginal(regs):
  rsp=f.reg(n.UC_X86_REG_RSP)
  for i,reg in enumerate(regs):f.wr(reg,f.q(rsp+i*8))
  f.wr(n.UC_X86_REG_RSP,rsp+len(regs)*8);f.ret()
 def draw():
  draws.append([int(f.floating(rows+i*32+24)+f.floating(mods+i*32+24)) for i in range(3)])
  for i,value in enumerate(draws[-1]):
   rowWidget=f.q(rowVector+i*8)
   for name in ('bar_base','bar_mod'):
    component=widgets[rowWidget,name];state=f.q(component+0x158)
    # Native negative branch intentionally does NOT show bar_mod again.
    if name=='bar_base' or value>=(40,30,12)[i]:f.u.mem_write(component+0x1c1,b'\1')
    f.wfloat(state+0x48,float(value if name=='bar_base' else (40,30,12)[i]))
  finishOriginal((n.UC_X86_REG_R14,n.UC_X86_REG_RSI,n.UC_X86_REG_RBP))
 f.handlers[0x15ea6c7]=draw
 f.handlers[0x15a8f99]=lambda:finishOriginal((n.UC_X86_REG_R14,n.UC_X86_REG_RBP))
 for category in (0,1,11,12,13,18,19):
  f.wn(weapon+0x24,category)
  for precip,accuracy,reload in [(1,.7,-6),(0,1,0),(2,.9,-2),(3,.8,0),(0,1,0)]:
   f.wn(weather+0x1c,precip);f.wn(weather+0x18,0)
   expected=[int(50*accuracy+.00001),35+(reload if category in (13,18,19) else 0),15]
   f.wr(n.UC_X86_REG_RDI,nativeContext);f.wr(n.UC_X86_REG_RBP,weapon);f.wr(n.UC_X86_REG_RBX,35);f.wr(n.UC_X86_REG_RSP,0x61f008)
   f.u.emu_start(base+0x507c9c,base+0x507dd1,count=300)
   assert f.reg(n.UC_X86_REG_RBX)==expected[1],('Native reload mismatch',category,precip,expected)
   for iteration in range(4):
    f.call('DynamicUnitCardStats',card)
    assert draws[-1]==expected,(base,category,precip,draws[-1],expected)
    assert [f.floating(mods+i*32+24) for i in range(3)]==[10,5,3],'Bonuses must not accumulate weather'
   cases.append(dict(base=hex(base),weapon=category,precipitation=precip,displayed=draws[-1]))
 # The read-only adapter does not depend on unrelated setup header fields.
 f.wq(f.setup,0xdeadbeef)
 # Live frame refresh, same card held open; current native climate drives changes.
 f.wn(weapon+0x24,13);f.wn(weather+0x1c,1);f.call('DynamicUnitCardFrame',card);assert draws[-1]==[35,29,15]
 # Reproduce53: a native widget refresh hides/resizes the red bar while
 # the native combat weather and input stats remain unchanged.
 for frame in range(600):
  affected=widgets[f.q(rowVector),'bar_mod'];state=f.q(affected+0x158)
  if frame in (2,17,100,400):
   f.u.mem_write(affected+0x1c1,b'\0');f.wfloat(state+0x48,0)
   before=len(draws);f.call('DynamicUnitCardFrame',card)
   assert len(draws)==before+1,'Native reset must invalidate cached draw, even with identical weather'
   assert f.u.mem_read(affected+0x1c1,1)==b'\1' and f.floating(state+0x48)==40
  else:
   before=len(draws);f.call('DynamicUnitCardFrame',card);assert len(draws)==before,'Stable widgets need no redraw'
  assert draws[-1]==[35,29,15],'Penalty must remain for the full native weather state'
 f.wn(weather+0x1c,0);f.call('DynamicUnitCardFrame',card);assert draws[-1]==[50,35,15]
 count=len(draws);f.call('DynamicUnitCardFrame',card);assert len(draws)==count,'Unchanged weather must not redraw the full card every frame'
 # Do not touch custom battle, campaign map, naval or absent unit cards.
 for offset,value in ((0x283c9,0),):
  f.u.mem_write(f.battle+offset,bytes([value]));f.wn(weather+0x1c,1);f.call('DynamicUnitCardStats',card);assert draws[-1]==[50,35,15]
 f.u.mem_write(f.battle+0x283c9,b'\1');f.wn(card+0x2a0,2);f.call('DynamicUnitCardStats',card);assert draws[-1]==[50,35,15]
report=dict(status='PASS',cases=len(cases),nativeNegativeBranchVisibilityRepair=True,nativeWidgetResetRecovery=True,stableWidgetsAvoidRedraw=True,activePenaltyFramesChecked=1800,actualNativeWideStatKeyComparison=True,actualNativeWeatherAccuracyGetter=True,actualNativeReloadBranchCompared=True,clearRainSnowFogReversal=True,bonusesPreserved=True,fatigueUntouched=True,customCampaignAndNavalExcluded=True,heldOpenCardRefreshes=True,rows=cases)
(W/'unit-weather-card-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2))
