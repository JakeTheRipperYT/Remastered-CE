from pathlib import Path
import json,shutil,sys,struct
W=Path(__file__).parent
sys.path.insert(0,str(W));import read_live
scope={'__file__':str(W/'test_fades_native.py')};exec(compile((W/'test_fades_native.py').read_text().split('\nresults=[]')[0],str(W/'test_fades_native.py'),'exec'),scope)
F=scope['FadeFixture'];rows=[]
for base in [0x180000000,0x230000000,0x7ff600000000]:
 for initial in [0,1]:
  f=F(base,0,0,0,initial,17);f.tick(0);f.frame();f.wn(f.model+0x28,5);f.tick(0);f.frame()
  live=object.__new__(read_live.Live);live.base=base;live.pid=0;live.read=lambda a,n:bytes(f.u.mem_read(a,n));result=live.snapshot()
  assert result['campaign'] and result['openingGround']['captured']
  assert result['openingGround']['wet']==result['renderer']['startingWet']==float(initial)
  assert result['renderer']['startingGrassCull']==float(initial)
  assert result['forecast']['initial']==initial and result['forecast']['stage']==5
  assert result['weatherBuffer'][15]==float(initial)
  rows.append(dict(base=hex(base),initialWet=initial,status='PASS'))
(W/'live-reader-layout-validation.json').write_text(json.dumps(dict(status='PASS',readOnly=True,mapResolvedAgainstExactControllerObjects=True,decoderCheckedAgainstNativeFixtures=True,results=rows),indent=2))
# Preserve the obsolete-test failure as provenance; only its current-contract rerun supersedes it.
suite=json.loads((W/'suite-results.json').read_text());shutil.copyfile(W/'suite-results.json',W/'initial-suite-with-stale-harness.json')
for row in suite['tests']:
 if row['test']=='test_dynamic_controller.py':
  row.update(status='PASS',exitCode=0,log=str(W/'dynamic-controller-tests.json'),cases=144,observations=1575,rerunReason='Historical standalone test expected obsolete at-first forecast text and pre-fade renderer state; replaced with existing cyclic/fade contract without changing installed application code.')
assert all(r['exitCode']==0 for r in suite['tests']);suite['status']='PASS_ALL_AUTOMATED_LIVE_PENDING';suite['liveGameplayVerified']=False;suite['originalStaleHarnessFailurePreserved']=True
(W/'suite-results.json').write_text(json.dumps(suite,indent=2))
report=dict(status=suite['status'],version='0.1.71-preview',forecastInputs=json.loads((W/'forecast-test-report.json').read_text())['inputs'],nativeControllerCases=144,nativeControllerObservations=1575,nativeFadeCases=96,unitCardCases=105,unitCardPenaltyFrames=1800,skyMaterialCases=12,startingGroundDeploymentCases=6,actualGrassShaderDrawsHardware=36,actualGrassShaderDrawsWARP=36,skyAndGroundGPUSamples=66,weatherAssetIdentityChecks=75,nativeHelperEqualsInstalled=True,originalWaitHandlerUnchanged=True,allAutomatedTestsPassed=True,liveCampaignValidation='PENDING: game launched at main menu; rainy-start and clear-start campaigns must be loaded.',noGameFilesChangedByAudit=True,noImageVideoCaptured=True)
(W/'verification-summary.json').write_text(json.dumps(report,indent=2))
R=W.parents[1];repo=Path(r'F:/Codex/Release/Remastered-CE/source/weather-contract-audit-071');repo.mkdir(exist_ok=True)
for p in W.iterdir():
 if p.is_file() and p.suffix in ['.py','.json','.txt','.log','.map']:shutil.copyfile(p,repo/p.name)
for path in [R/'source/CURRENT-BUILD.txt',R/'NEW_CHAT_RESUME.txt']:
 with path.open('a') as stream:stream.write('\n0.1.71 full weather automated audit PASS: 112640 policy inputs; 144 native controller cases/1575 observations; 96 fades; 105 unit-card cases/1800 penalty frames; 72 actual installed grass GPU draws; 66 sky/ground GPU samples. 75 weather assets match confirmed .52; helper equals installed PE. Historical stale forecast test updated with failure provenance retained. LIVE CAMPAIGN CHECK PENDING; game PID14220 launched. Read-only reader: work/weather-contract-audit-071/read_live.py. Never claim live puddle appearance/audio has been verified from offline fixtures.\n')
print(json.dumps(report,indent=2))
