from pathlib import Path
import json,struct
W=Path(__file__).resolve().parent
scope={'__file__':str(W/'test_fades_native.py')}
exec(compile((W/'test_fades_native.py').read_text().split('\nresults=[]')[0],str(W/'test_fades_native.py'),'exec'),scope)
F=scope['FadeFixture'];n=scope['n'];catalog=scope['catalog'] if 'catalog' in scope else scope['Base'].__init__.__globals__['catalog'];rows=[]
fields=[0xe08,0xe0c,0xe14,0xe18,0xe1c,0xe20,0xe24,0xe28,0xe2c,0xe30,0xe34]
for base in [0x180000000,0x230000000,0x7ff600000000]:
 for initial in (0,1):
  f=F(base,0,0,0,initial,17);f.tick(0);f.frame()
  expectedWet=float(initial==1);definition=3 if initial==1 else f.n(f.node+0xe8)
  expected={offset:f.floating(f.node+offset+definition*0x168) for offset in fields}
  # Native startup is allowed to transiently use the opposite enum and reset
  # all ground material fields; that must not become the opening ground state.
  def resetNativeGround():
   f.wn(f.node+0xe8,0 if initial else 3)
   for kind in range(7):
    for offset in fields:f.wfloat(f.node+offset+kind*0x168,0)
   parent=f.registry['rce_weather_shared'];f.u.mem_write(f.q(parent+0x18),bytes(112));f.wn(parent+0x38,0)
  for stage,time in [(5,0),(5,.1),(6,1),(6,2)]:
   resetNativeGround();f.wn(f.model+0x28,stage);f.tick(time);f.frame()
   assert f.state()[0]==2 and f.state()[1]==expectedWet,(stage,initial,f.state())
   assert f.floating(f.renderer+0x1fc0)==expectedWet
   assert f.n(f.registry['rce_weather_shared']+0x38)>0,'Steady frame must re-upload after shader reset'
   for kind in range(7):
    for offset in fields:
     value=expected[offset]
     if offset==0xe08 and not expectedWet:value=1
     assert abs(f.floating(f.node+offset+kind*0x168)-value)<1e-6,(initial,stage,hex(offset),kind)
  # Starting combat may also replace the battle specification object.
  replacement=0x2b1800;f.u.mem_write(replacement,bytes(f.u.mem_read(f.spec,0xc4)));f.wq(f.setup+0x90,replacement)
  resetNativeGround();f.tick(2.1);f.frame();assert f.state()[1]==expectedWet
  # Destroy/recreate handoff must not lose the independently retained opening.
  f.call('DynamicSkyDestroy',f.node+0x348);resetNativeGround();f.frame();assert f.state()[1]==expectedWet
  rows.append(dict(base=hex(base),initial=initial,startBattleAndStageChangePreserveGround=True,completeNativeMaterialRestored=True,steadyGPUBufferReuploaded=True))
 # A deployment weather reroll must capture the newly selected dry opening,
 # rather than retaining the rain choice that the player just discarded.
 f=F(base,0,0,0,1,17);f.tick(0);f.frame()
 dry=next(r['path'].replace('/','\\') for r in catalog.values() if '/spring/day/dry/' in r['path'] and '/land/' in r['path'])
 f.wide(f.climate,dry,0x380000);f.wide(f.node+0xd48,dry,0x381000);f.setScene(dry)
 f.wn(f.setup+0xc8,0);f.wn(f.climate+0x68,0);f.wn(f.weather+0x18,2);f.tick(0);f.frame()
 f.wn(f.model+0x28,5);f.tick(0);f.frame();assert f.state()[1]==0
report=dict(status='PASS',deploymentStateSurvivesStartBattle=True,battleSpecificationReplacementPreservesGround=True,temporaryWeatherEnumResetIgnored=True,fullPuddleMaterialRangeAndMaskRestored=True,shaderResetRecoversInSteadyFrame=True,deploymentRerollRespected=True,cases=len(rows),rows=rows)
(W/'deployment-puddle-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
