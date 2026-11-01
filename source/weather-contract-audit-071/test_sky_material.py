"""Execute CE sky material, environment direction conversion and GPU uniform writes.
Only platform sin/cos and sqrt are supplied by Python; rendering remains in-game acceptance.
"""
from pathlib import Path
import struct,math,json
W=Path(__file__).resolve().parent
scope={'__file__':str(W/'test_fades_native.py')}
exec(compile((W/'test_fades_native.py').read_text().split('\nresults=[]')[0],str(W/'test_fades_native.py'),'exec'),scope)
Fixture=scope['FadeFixture'];n=scope['n'];stock=scope['stock'];policy=scope['policy'];Input=scope['Input'];Plan=scope['Plan'];C=scope['C']
class SkyFixture(Fixture):
 def __init__(self,base,season,night,naval,initial,seed):
  super().__init__(base,season,night,naval,initial,seed)
  for section in stock.sections:
   if section.Name.startswith(b'.rdata'):self.u.mem_write(base+section.VirtualAddress,section.get_data())
  for rva,size in [(0x1b96e50,0x500),(0x1b69650,0x180),(0x1990b80,0x200)]:self.u.mem_write(base+rva,stock.get_data(rva,size))
  self.handlers[0x21d710]=self.sincos;self.handlers[0x21d760]=self.squareRoot
  self.wq(self.node+0x348+0x778,self.renderer);self.skyMaterial=0x3d2000
  self.wq(self.skyMaterial+0xd8,self.node+0x348)
  self.wq(0x3923b8,0x3d1000);self.wq(0x3923a8,self.registry['rce_weather_shared'])
  n.layout['exports']['NativeSkyMaterial']=0x1b96e50
 def scalar(self,reg):return struct.unpack('<f',struct.pack('<I',self.reg(reg)&0xffffffff))[0]
 def sincos(self):
  angle=self.scalar(n.UC_X86_REG_XMM0)
  self.wfloat(self.reg(n.UC_X86_REG_RDX),math.sin(angle));self.wfloat(self.reg(n.UC_X86_REG_R8),math.cos(angle));self.ret()
 def squareRoot(self):
  v=math.sqrt(max(0,self.scalar(n.UC_X86_REG_XMM0)));self.wr(n.UC_X86_REG_XMM0,struct.unpack('<I',struct.pack('<f',v))[0]);self.ret()
 def uniform(self):
  try:self.call('DynamicSkyMaterial',self.skyMaterial)
  except Exception:
   print('RIP',hex(self.reg(n.UC_X86_REG_RIP)),'RCX',hex(self.reg(n.UC_X86_REG_RCX)),'RAX',hex(self.reg(n.UC_X86_REG_RAX)));raise
  return struct.unpack('<3f',self.u.mem_read(0x3d1000,12))
rows=[]
for base in [0x180000000,0x230000000,0x7ff600000000]:
 for season,night,naval in [(0,0,0),(1,1,0),(2,0,1),(3,1,1)]:
  day=policy.mask(season,0,naval);nightMask=policy.mask(season,1,naval);mask=(day&nightMask)|(2 if (day|nightMask)&6 else 0);seed=0
  while True:
   i=Input(1,seed,1,season,night,naval,0,mask);p=Plan();assert policy.make(C.byref(i),C.byref(p))
   if p.count>=3:break
   seed+=1
  f=SkyFixture(base,season,night,naval,0,seed);f.tick(0);f.wn(f.model+0x28,5);f.tick(0);f.frame();expected=f.uniform()
  samples=0
  for phaseIndex,phase in enumerate(list(p.phases)[1:p.count],1):
   duration=phase.blendSeconds
   for progress in [0,.001,.25,.5,.75,.999,1]:
    f.tick(phase.startSeconds+duration*progress);f.frame();value=f.uniform()
    assert max(abs(a-z) for a,z in zip(value,expected))<1e-5,(progress,expected,value)
    f.u.mem_write(f.node+0x390,b'\0');samples+=1
   f.frame();assert max(abs(a-z) for a,z in zip(f.uniform(),expected))<1e-5
  # Control: the old implementation's changed environment angle moves the
  # actual shader uniform even while SkyDome's extra rotation is unchanged.
  f.wfloat(f.manager+0x80+0x130,2.6);f.call('OriginalSkyMaterial',f.skyMaterial);changed=struct.unpack('<3f',f.u.mem_read(0x3d1000,12))
  assert max(abs(a-z) for a,z in zip(changed,expected))>.1
  assert max(abs(a-z) for a,z in zip(f.uniform(),expected))<1e-5
  rows.append(dict(base=hex(base),season=season,night=night,naval=naval,samples=samples,oldBugDetectedByControl=True))
report=dict(status='PASS',nativeLightningSunDirectionCannotRotateSky=True,nativeSkyMaterialAndSunDirectionConversionExecuted=True,uniformStableThroughFadeAndCompletion=True,platformMathOnlyModeled=True,cases=len(rows),rows=rows)
(W/'sky-material-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
