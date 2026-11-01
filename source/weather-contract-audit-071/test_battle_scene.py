from pathlib import Path
import json,struct,sys
sys.path.insert(0,str(Path(__file__).parent));import test_controller_native as n
w=Path(__file__).parent;rows=[]
for base in [0x180000000,0x230000000,0x7ff600000000]:
 f=n.Fixture(base);climate=0x260000;context=0x270000;battle=0x271000;setup=0x272000;spec=0x273000;selected=[];assigned=[];missing=[False]
 f.wq(context,battle);f.wq(battle+8,setup);f.wq(setup+0x90,spec);f.wn(spec+0x10,1234567)
 def put_wide(at,value,data):
  f.u.mem_write(data,value.encode('utf-16-le')+b'\0\0');f.u.mem_write(at,struct.pack('<QQQ',len(value),len(value),data))
 def wide(at):return bytes(f.u.mem_read(f.q(at+16),(f.q(at)&65535)*2)).decode('utf-16-le')
 def original():
  put_wide(climate,'weather/original.environment',0x280000);f.ret(climate)
 def prefix():put_wide(f.reg(n.UC_X86_REG_RCX),'battleterrain/map_override',0x281000);f.ret(f.reg(n.UC_X86_REG_RCX))
 def select():
  rsp=f.reg(n.UC_X86_REG_RSP);visual=f.reg(n.UC_X86_REG_R9);seed=f.reg(n.UC_X86_REG_RCX);out=f.reg(n.UC_X86_REG_RDX);kind=f.reg(n.UC_X86_REG_R8)
  assert f.n(visual+0x44)==1
  assert bytes(f.u.mem_read(visual,0x44))==bytes(f.u.mem_read(climate+0x20,0x44))
  assert f.n(visual+0x48)==f.n(climate+0x68)
  assert seed!=spec+0x10 and f.n(seed)==1234567
  assert wide(f.q(rsp+0x28))=='battleterrain/map_override'
  f.wn(seed,987654321);selected.append((kind,f.n(visual+0x40),f.n(visual+0x48)))
  put_wide(out,'' if missing[0] else 'weather/japan/night.environment',0x282000);f.ret(out)
 def assign():
  assert f.reg(n.UC_X86_REG_RCX)==climate;value=wide(f.reg(n.UC_X86_REG_RDX));assigned.append(value);put_wide(climate,value,0x283000);f.ret(climate)
 f.handlers.update({0x56a565:original,0x199df0:prefix,0xf18320:select,0x19a990:assign})
 cases=0
 for enabled in [False,True]:
  f.flags['RCE_AlwaysNightCampaign']=1 if enabled else -1
  for naval in [0,1]:
   for season in range(4):
    for weather in range(4):
     for actual_night in [0,1]:
      f.u.mem_write(climate+0x18,bytes([0x5a])*0x58);f.wn(climate+0x60,season);f.wn(climate+0x64,actual_night);f.wn(climate+0x68,weather);f.u.mem_write(spec+0x48,bytes([naval]))
      before=bytes(f.u.mem_read(climate+0x18,0x58));count=len(selected)
      assert f.call('NightBattleClimate',climate,context)==climate
      assert bytes(f.u.mem_read(climate+0x18,0x58))==before
      assert f.n(spec+0x10)==1234567
      assert len(selected)-count==int(enabled)
      assert wide(climate)==('weather/japan/night.environment' if enabled else 'weather/original.environment')
      cases+=1
 missing[0]=True;f.flags['RCE_AlwaysNightCampaign']=1;f.call('NightBattleClimate',climate,context);assert wide(climate)=='weather/original.environment';cases+=1
 rows.append(dict(base=hex(base),cases=cases,nightAssetSelections=len(selected),gameplayMetadataUnchanged=True,battleSeedUnchanged=True))
result=dict(status='PASS',compiledBattleWrapperExecuted=True,engineAssetSelectorModeled=True,results=rows,totalCases=sum(x['cases'] for x in rows))
(w/'battle-scene-tests.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
