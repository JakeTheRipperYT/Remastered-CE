from pathlib import Path
W=Path(r'F:/Codex/Remastered-CE-Port/work/weather-contract-audit-071');p=W/'test_dynamic_controller.py';s=p.read_text();(W/'legacy_dynamic_controller_test.py.txt').write_text(s)
a=s.index('\ncases=[]')
s=s[:a]+'''
cases=[]
# The original standalone cases predate fade resources and cyclic forecasts.
# Execute their climate/UI/wait invariants through the current fade-aware fixture.
if __name__=='__main__':
 scope={'__file__':str(W/'test_fades_native.py')}
 exec(compile((W/'test_fades_native.py').read_text().split('\\nresults=[]')[0],str(W/'test_fades_native.py'),'exec'),scope)
 Current=scope['FadeFixture']
 for base in [0x180000000,0x230000000,0x7ff600000000]:
  for season in range(4):
   for night in range(2):
    for naval in range(2):
     mask=(policy.mask(season,0,naval)&policy.mask(season,1,naval))|(2 if (policy.mask(season,0,naval)|policy.mask(season,1,naval))&6 else 0)
     for initial in [0,4 if season==3 else 1,3]:
      seed=0;p=Plan()
      while True:
       i=Input(1,seed,1,season,night,naval,initial,mask);assert policy.make(C.byref(i),C.byref(p))
       if p.count>=3:break
       seed+=1
      f=Current(base,season,night,naval,initial,seed);f.tick(0);f.call('DynamicForecastUI',f.ui)
      assert f.text and 'intermittent' in f.text[-1].lower()
      assert 'at first' not in f.text[-1].lower()
      originalSpec=bytes(f.u.mem_read(f.spec,0xc4));f.wn(f.model+0x28,5);f.tick(0);f.frame();assert not f.scenes
      startingWet=float(initial in (1,2));observations=0
      for phase in list(p.phases)[1:p.count]:
       for progress in [0,.25,.5,.75,1]:
        time=phase.startSeconds+phase.blendSeconds*progress;f.tick(time);f.frame();assert f.scenes
        assert f.state()[1]==startingWet and f.floating(f.renderer+0x1fc0)==startingWet
        climatePrecip=f.n(f.climate+0x68);assert climatePrecip==f.n(f.setup+0xc8)
        assert f.q(f.climate+0x18)==0x352000+climatePrecip*0x100
        for layer in range(2):
         count=f.call('DynamicWeatherParticleCount',f.node+0x110+layer*0x120);assert count<=65536 and count%6 in (0,4)
        old=list(f.scenes);state=f.state();f.tick(time);f.frame();assert f.scenes==old and f.state()==state
        observations+=1
      assert bytes(f.u.mem_read(f.spec,0xc4))==originalSpec
      assert f.n(f.weather+0x14)==3 and f.n(f.weather+0x18)==1
      cases.append(dict(base=hex(base),season=season,night=night,naval=naval,initial=initial,observations=observations,nativeRebinds=len(f.rebinds)))
  f=Current(base,0,0,0,0,1,origin=0);f.wq(f.battle+8,0xdead00000000);f.tick(300);f.call('DynamicForecastUI',f.ui);f.frame();assert not f.text and not f.scenes and not f.rebinds
 report=dict(status='PASS_NATIVE_FIXTURE_NOT_LIVE_ACCEPTANCE',cases=len(cases),observations=sum(r['observations'] for r in cases),nativeClimateBindingExecuted=True,nativeParticleDrawCountExecuted=True,pausedSimulationStable=True,waitCountersAndSpecUnchanged=True,startingGroundHeld=True,cyclicForecastText=True,customBattleEarlyExclusion=True,legacyHarnessUpdatedForExistingCyclicAndFadeContract=True,results=cases)
 (W/'dynamic-controller-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='results'},indent=2))
'''
p.write_text(s)
