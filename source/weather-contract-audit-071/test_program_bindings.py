"""Exercise the added per-program path with CE's actual vector operations."""
from pathlib import Path
import json
W=Path(__file__).resolve().parent
scope={'__file__':str(W/'test_fades_native.py')}
exec(compile((W/'test_fades_native.py').read_text().split('\nresults=[]')[0],str(W/'test_fades_native.py'),'exec'),scope)
Fixture=scope['FadeFixture'];stock=scope['stock'];n=scope['n'];rows=[]
for base in [0x180000000,0x230000000,0x7ff600000000]:
 f=Fixture(base,0,0,0,0,1);program=0x3c0000
 assert f.n(f.registry['rce_weather_shared']+0x38)>0,'Disabled defaults must be marked for initial GPU upload'
 f.u.mem_write(base+0x132d60,stock.get_data(0x132d60,0x130))
 f.handlers[0x1aeb855]=lambda:f.ret()
 # Pre-existing camera/environment and texture references must survive.
 expectedBuffers=[0x3d0000,0x3d0100]
 for stage in range(6):
  at=program+0x190+stage*16;f.wn(at,2);f.wn(at+4,2);f.wq(at+8,0x3d1000+stage*0x20)
  for i,value in enumerate(expectedBuffers):f.wq(0x3d1000+stage*0x20+i*8,value)
 f.call('DynamicWeatherProgram',0,program)
 for stage in range(6):
  at=program+0x190+stage*16;values=[f.q(f.q(at+8)+i*8) for i in range(f.n(at+4))]
  assert values==expectedBuffers+[f.registry['rce_weather_shared']]
  at=program+0x250+stage*16;values=[f.q(f.q(at+8)+i*8) for i in range(f.n(at+4))]
  assert values==[f.registry['t_rce_weather_previous_sky'],f.registry['t_rce_weather_previous_sun']]
 before=bytes(f.u.mem_read(program+0x190,0x120));f.call('DynamicWeatherProgram',0,program)
 assert bytes(f.u.mem_read(program+0x190,0x120))==before
 rows.append(dict(base=hex(base),shaderStages=6,existingBindingsPreserved=True,repeatRegistrationDeduplicated=True))
report=dict(status='PASS',compiledProgramBindingHookExecuted=True,nativeVectorGrowAndAppendExecuted=True,results=rows)
(W/'program-binding-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
