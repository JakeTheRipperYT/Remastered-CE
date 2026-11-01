from pathlib import Path
import json,struct
W=Path(__file__).resolve().parent
scope={'__file__':str(W/'test_fades_native.py')}
exec(compile((W/'test_fades_native.py').read_text().split('\nresults=[]')[0],str(W/'test_fades_native.py'),'exec'),scope)
F=scope['FadeFixture'];n=scope['n'];stock=scope['stock'];rows=[]
for base in (0x180000000,0x230000000,0x7ff600000000):
 for initial in (0,1):
  f=F(base,0,0,0,initial,17);f.tick(0);f.frame()
  definition=3 if initial else f.n(f.node+0xe8)
  raw=f.floating(f.node+0xe34+definition*0x168)
  # Execute CE's actual terrain range upload block, including native constants.
  address=base+0x1b49c6c
  f.u.mem_write(address,stock.get_data(0x1b49c6c,0x64))
  for rva in (0x2174b10,0x217c6b8):f.u.mem_write(base+rva,stock.get_data(rva,4))
  root=base+0x3e00000;definitionData=0x320000;output=0x321000
  f.wq(root+0x8a140,output)
  for offset,value in ((0x84,128),(0x88,1024),(0x8c,raw)):f.wfloat(definitionData+offset,value)
  old=f.handlers.get(0x1aeed70);f.handlers[0x1aeed70]=lambda:f.ret()
  f.wr(n.UC_X86_REG_RDI,root);f.wr(n.UC_X86_REG_RBX,definitionData);f.wr(n.UC_X86_REG_RSP,0x610000)
  f.u.emu_start(address,base+0x1b49cd0,count=100)
  if old:f.handlers[0x1aeed70]=old
  else:del f.handlers[0x1aeed70]
  expected=f.floating(output+8)
  for stage,time in ((5,0),(6,2),(6,200),(6,240),(6,300),(6,600)):
   f.wn(f.model+0x28,stage);f.tick(time);f.frame()
   for name in ('g_rce_weather_old_range','g_rce_weather_new_range'):
    actual=f.floating(f.q(f.fields[name]+0x28)+8)
    assert actual==expected,(initial,stage,time,name,raw,actual,expected)
   for kind in range(7):assert f.floating(f.node+0xe34+kind*0x168)==raw,'Definition burn must stay raw'
  rows.append(dict(base=hex(base),initial=initial,rawBurn=raw,nativeShaderMultiplier=expected))
report=dict(status='PASS',actualNativeTerrainUploadExecuted=True,rawDefinitionPreserved=True,deploymentCombatAndTransitionsMatchNative=True,cases=rows)
(W/'puddle-material-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
