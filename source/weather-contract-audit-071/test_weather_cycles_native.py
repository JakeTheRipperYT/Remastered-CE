from pathlib import Path
import json,struct,collections
W=Path(__file__).resolve().parent
scope={'__file__':str(W/'test_fades_native.py')}
exec(compile((W/'test_fades_native.py').read_text().split('\nresults=[]')[0],str(W/'test_fades_native.py'),'exec'),scope)
F=scope['FadeFixture'];n=scope['n'];policy=scope['policy'];Input=scope['Input'];Plan=scope['Plan'];C=scope['C']
policy.phase.argtypes=[C.POINTER(Plan),C.c_float];policy.phase.restype=C.c_uint
rows=[]
for base in [0x180000000,0x230000000,0x7ff600000000]:
 for initial in (0,1):
  mask=policy.mask(0,0,0)&policy.mask(0,1,0);seed=0
  while True:
   i=Input(1,seed,1,0,0,0,initial,mask);p=Plan();assert policy.make(C.byref(i),C.byref(p))
   if p.count==3:break
   seed+=1
  f=F(base,0,0,0,initial,seed);f.tick(0);f.wn(f.model+0x28,5);f.tick(0);f.frame();f.call('DynamicForecastUI',f.ui)
  assert 'intermittent' in f.text[-1].lower()
  slot=p.phases[1].startSeconds;originalSpec=bytes(f.u.mem_read(f.spec,0xc4));ground=f.state()[1]
  for step in range(1,p.count*4+1):
   index=step%p.count;phase=p.phases[index];previous=p.phases[(index+p.count-1)%p.count]
   for progress in (0,.25,.5,.75,1):
    t=step*slot+phase.blendSeconds*progress;f.tick(t);f.frame()
    assert f.state()[0]==(2 if progress==1 else 1),(step,progress,f.state())
    assert f.state()[1]==ground
    expectedKind=previous.kind if progress<.5 else phase.kind
    expectedPrecip=1 if expectedKind in (1,2) else 2 if expectedKind in (4,5) else 3 if expectedKind==3 else 0
    assert f.n(f.setup+0xc8)==expectedPrecip,(step,index,progress,expectedPrecip,f.n(f.setup+0xc8))
    if progress<1:assert abs(f.state()[3]-progress)<.00001
    if progress==1:assert len(f.jobs)==len(f.freed)
    before=list(f.scenes);f.tick(t);f.frame();assert f.scenes==before
   assert len(f.scenes)==step,(step,len(f.scenes))
  assert bytes(f.u.mem_read(f.spec,0xc4))==originalSpec
  # One-hour policy coverage: equal complete slots, only the final partial slot
  # can give a state extra time. No terminal phase absorbs the rest of a battle.
  totals=collections.Counter()
  for t in range(3600):totals[policy.phase(C.byref(p),t)]+=1
  assert len(totals)==p.count and max(totals.values())-min(totals.values())<=slot
  f.call('DynamicSkyDestroy',f.node+0x348);assert f.state()[0]==0 and len(f.jobs)==len(f.freed)
  rows.append(dict(base=hex(base),initial=initial,loops=4,transitions=p.count*4,slotSeconds=slot,oneHourSeconds=dict(totals),allTextureJobsFreed=True))
report=dict(status='PASS',nativeGameplayAndRenderWraparound=True,openingTerrainRetained=True,pauseStable=True,balancedOneHourCoverage=True,cases=len(rows),rows=rows)
(W/'weather-cycle-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
