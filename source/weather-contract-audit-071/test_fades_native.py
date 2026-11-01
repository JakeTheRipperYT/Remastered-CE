"""Native registry, field initialization, texture lifetime and fade integration."""
from pathlib import Path
import json,struct,itertools
W=Path(__file__).resolve().parent
scope={'__file__':str(W/'test_dynamic_controller.py')}
exec(compile((W/'test_dynamic_controller.py').read_text().split('\ncases=[]')[0],str(W/'test_dynamic_controller.py'),'exec'),scope)
Base=scope['WeatherFixture'];n=scope['n'];stock=scope['stock'];policy=scope['policy'];Input=scope['Input'];Plan=scope['Plan'];C=scope['C']
class FadeFixture(Base):
 def __init__(self,base,season,night,naval,initial,seed,origin=1):
  super().__init__(base,season,night,naval,initial,seed,origin)
  self.allocCursor=0x360000;self.jobs=[];self.freed=[];self.boundProfiles=[];self.environment=0x3b0000;self.ambientCalls=[];self.ready=True
  self.wq(base+0x3450da0,0x340000);self.wq(base+0x3450da8,0);self.wq(base+0x3450db0,128)
  self.wq(base+0x3457888,0x370000);self.wq(0x370030,0x390000-0x26c8)
  self.wq(0x392ae8,0x393000);self.wq(0x392ad8,0x394000)
  for rva,length in [(0x19cd060,0x160),(0x19d1d30,0x160),(0x19e9540,0xc0),(0x1aeed70,0x20),(0x1ab6470,0x160),(0x19f80d0,0x20),(0x1a89940,0x50),(0x187f660,0x20),(0x12ef70,0x10),(0x12e8c0,0x10)]:self.u.mem_write(base+rva,stock.get_data(rva,length))
  for i in range(4):self.wq(base+0x23b52e8+i*8,struct.unpack('<Q',stock.get_data(0x23b52e8+i*8,8))[0]-0x180000000+base)
  self.handlers.update({0x1a31e15:self.originalParameters,0x18abb0:self.allocate,0x19fe50:self.allocate,0x19fe10:lambda:self.ret(),
   0x19bd00:self.expandInterned,0x19ad60:self.appendWide,0x19cb160:self.newJob,0x19dbcd0:lambda:self.ret(int(self.ready)),
   0x741ea0:lambda:self.ret(self.reg(n.UC_X86_REG_RCX)+0x2000),0x3ff0600:self.freeJob,0x3ff0700:lambda:self.ret(0x80),
   0x199b70:self.copyInterned,0x19a3a0:lambda:self.ret(),0x1b4db80:self.ambientFrame,0x1ba0bd6:lambda:self.ret(),0x1b96975:self.particleMaterial,0x1b65c45:lambda:self.ret()})
  n.layout['exports']['AmbientCallSite']=0x1ba0bd1
  self.handlers[0x1a75030]=self.loadEnvironmentScratch
  self.handlers[0x1a73fd0]=self.blendTargetEnvironment
  self.handlers[0x3ff0800]=self.worldTime
  self.wq(0x310000+0x1c8,base+0x3ff0800)
  self.call('DynamicWeatherParameters',self.environment)
  self.registry={}
  for i in range(self.q(base+0x3450da8)):
   parameter=self.q(0x340000+i*8);isBuffer=self.n(parameter+8)==1
   namePointer=self.q(parameter+(0x40 if isBuffer else 0x28));name=self.ascii(namePointer)
   self.registry[name]=parameter
  assert set(self.registry)=={'rce_weather_shared','t_rce_weather_previous_sky','t_rce_weather_previous_sun'}
  parent=self.registry['rce_weather_shared'];assert self.n(parent+0x10)==112 and self.n(parent+0x24)==7,(self.n(parent+0x10),self.n(parent+0x24))
  self.fields={}
  for i in range(7):
   field=self.q(self.q(parent+0x28)+i*8);self.fields[self.ascii(self.q(field+0x10))]=field
   assert self.q(field+0x18)==parent and self.q(parent+0x18)+i*16==self.q(field+0x28)
  assert len(self.fields)==7
 def ascii(self,ptr):
  data=bytearray()
  for i in range(100):
   value=bytes(self.u.mem_read(ptr+i,1))
   if value==b'\0':return data.decode()
   data+=value
  raise AssertionError('Unterminated name')
 def originalParameters(self):
  out=self.reg(n.UC_X86_REG_RCX);self.wq(out,self.base+0x23b5310);self.wq(out+0x90,self.base+0x23b52e8)
  self.wq(out+0x3a8,self.base+0x23aa860);self.wq(out+0x3a8+0x30,out+0x528);self.ret(out)
 def allocate(self):
  out=self.allocCursor;self.allocCursor+=(self.reg(n.UC_X86_REG_RCX)+15)&~15;assert self.allocCursor<0x378000
  self.ret(out)
 def expandInterned(self):
  source=self.reg(n.UC_X86_REG_RCX);out=self.reg(n.UC_X86_REG_RDX)
  value='sun.dds' if source==self.node+0x348+0x268+0x140 else 'skyboxes/previous.dds'
  address=self.allocCursor;self.allocCursor+=256;self.wide(out,value,address);self.ret(out)
 def appendWide(self):
  out=self.reg(n.UC_X86_REG_RCX);text=self.readWide(out)+self.readWide(self.reg(n.UC_X86_REG_RDX))
  address=self.allocCursor;self.allocCursor+=256;self.wide(out,text,address);self.ret(out)
 def newJob(self):
  out=self.reg(n.UC_X86_REG_RCX);kind=self.reg(n.UC_X86_REG_RDX);path=self.readWide(self.reg(n.UC_X86_REG_R8))
  self.jobs.append((out,kind,path));self.wq(out,0x3f0000);self.wq(0x3f0000,self.base+0x3ff0600);self.wq(0x3f00f0,self.base+0x3ff0700);self.ret(out)
 def freeJob(self):
  job=self.reg(n.UC_X86_REG_RCX);assert job not in self.freed
  for name in ['t_rce_weather_previous_sky','t_rce_weather_previous_sun']:assert self.q(self.registry[name]+0x10)!=job
  self.freed.append(job);self.ret()
 def copyInterned(self):
  out=self.reg(n.UC_X86_REG_RCX);self.u.mem_write(out,bytes(self.u.mem_read(self.reg(n.UC_X86_REG_RDX),16)));self.ret(out)
 def particleMaterial(self):
  material=self.reg(n.UC_X86_REG_RCX);layer=self.n(material+0xe8);kind=self.n(self.node+0xe8)
  self.boundProfiles.append(struct.unpack('<8f',self.u.mem_read(self.node+0xe84+kind*0x168+layer*0x68,32)));self.ret(1)
 def ambientFrame(self):
  dt=struct.unpack('<f',struct.pack('<I',self.reg(n.UC_X86_REG_XMM2)&0xffffffff))[0]
  ambient=self.reg(n.UC_X86_REG_RCX);self.ambientCalls.append((dt,bytes(self.u.mem_read(ambient+0xc0,64))));self.ret()
 def checkAmbient(self,progress,active):
  names=bytes(self.u.mem_read(self.node+0xc30+0xc0,64));start=len(self.ambientCalls)
  self.wr(n.UC_X86_REG_XMM1,struct.unpack('<I',struct.pack('<f',100))[0]);self.wr(n.UC_X86_REG_XMM2,struct.unpack('<I',struct.pack('<f',.1))[0])
  self.call('AmbientCallSite',self.node+0xc30,0,0,0);calls=self.ambientCalls[start:]
  expected=[.1*(1-progress),.1*progress] if active else [.1]
  assert len(calls)==len(expected) and all(abs(c[0]-v)<.000001 for c,v in zip(calls,expected))
  assert bytes(self.u.mem_read(self.node+0xc30+0xc0,64))==names
 def seedDefinitions(self):
  super().seedDefinitions()
  for definition in range(7):
   self.wfloat(self.node+0xe08+definition*0x168,.6)
   self.wfloat(self.node+0xe14+definition*0x168,.15)
   self.wfloat(self.node+0xe18+definition*0x168,.15)
   self.wfloat(self.node+0xe2c+definition*0x168,128 if definition in (3,4) else 0)
   self.wfloat(self.node+0xe30+definition*0x168,1024 if definition in (3,4) else 0)
   self.wfloat(self.node+0xe34+definition*0x168,.1)
   self.wfloat(self.node+0xe0c+definition*0x168,4.0+definition)
   self.wfloat(self.node+0xe1c+definition*0x168,.6+definition*.01)
   self.wfloat(self.node+0xe20+definition*0x168,.05)
   self.wfloat(self.node+0xe24+definition*0x168,float(definition in (3,4)))
   self.wfloat(self.node+0xe28+definition*0x168,.1 if definition in (3,4) else 0)
 def setScene(self,path):
  super().setScene(path)
  # Deliberately different headings on each scene load expose any sky movement.
  self.wfloat(self.node+0x348+0x8c8,.25+len(self.scenes)*1.3)
  for i,v in enumerate((.3+len(self.scenes)*1.2,.7,0)):
   self.wfloat(self.manager+0x80+0x130+i*4,v)
  self.u.mem_write(self.node+0x390,b"\1")
  self.wfloat(self.manager+0x80+0x318,1+len(self.scenes)*.2)
 def blendEnvironment(self,returning=True):
  super().blendEnvironment(returning)
  # Interpolation inputs have equal retained directions in the corrected controller.
  self.u.mem_write(self.manager+0xfa0+0x130,bytes(self.u.mem_read(self.manager+0x80+0x130,12)))
  self.wfloat(self.manager+0xfa0+0x318,self.floating(self.manager+0x80+0x318))
 def worldTime(self):
  self.wr(n.UC_X86_REG_XMM0,struct.unpack('<I',struct.pack('<f',self.clock))[0]);self.ret()
 def loadEnvironmentScratch(self):
  path=self.readWide(self.reg(n.UC_X86_REG_RDX));self.ret(0x334000 if '_summer.lighting' in path else self.scratch)
 def blendTargetEnvironment(self):
  out=self.reg(n.UC_X86_REG_RCX);target=self.reg(n.UC_X86_REG_RDX);old=self.reg(n.UC_X86_REG_R8)
  p=struct.unpack('<f',struct.pack('<I',self.reg(n.UC_X86_REG_XMM3)&0xffffffff))[0]
  self.u.mem_write(out,bytes(self.u.mem_read(target,0x790)))
  for offset in [0x130,0x134,0x138,0x248,0x2d0+0x48]:
   a=self.floating(target+offset);z=self.floating(old+offset);self.wfloat(out+offset,a+(z-a)*p)
  self.ret()
 def state(self):return struct.unpack('<4f',self.u.mem_read(self.q(self.fields['g_rce_weather_surface']+0x28),16))
results=[]
for base in [0x180000000,0x230000000,0x7ff600000000]:
 for season,night,naval in itertools.product(range(4),range(2),range(2)):
  for initial in [0,4 if season==3 else 1]:
   dayMask=policy.mask(season,0,naval);nightMask=policy.mask(season,1,naval);mask=(dayMask&nightMask)|(2 if (dayMask|nightMask)&6 else 0);seed=0
   while True:
    i=Input(1,seed,1,season,night,naval,initial,mask);p=Plan();assert policy.make(C.byref(i),C.byref(p))
    if p.count>=3:break
    seed+=1
   f=FadeFixture(base,season,night,naval,initial,seed);f.tick(0);f.wn(f.model+0x28,5);f.tick(0);f.frame()
   heading=f.floating(f.node+0x348+0x8c8)
   startingWet=float(f.n(f.node+0xe8) in (3,4))
   groundFields={name:bytes(f.u.mem_read(f.q(f.fields[name]+0x28),16)) for name in ["g_rce_weather_old_shape","g_rce_weather_new_shape","g_rce_weather_old_material","g_rce_weather_new_material"]}
   sunAngles=bytes(f.u.mem_read(f.manager+0x80+0x130,12))
   for phaseIndex,phase in enumerate(list(p.phases)[1:p.count],1):
    duration=phase.blendSeconds
    for progress in [0,.001,.25,.5,.75,.999,1]:
     f.tick(phase.startSeconds+duration*progress);f.frame()
     assert bytes(f.u.mem_read(f.manager+0x80+0x130,12))==sunAngles, "Environment rotates sky"
     if progress>0:assert bytes(f.u.mem_read(f.node+0x390,1))==b"\0", "Fade rebuilt sky texture job"
     f.u.mem_write(f.node+0x390,b"\0")
     assert f.floating(f.node+0x348+0x8c8)==heading, "Weather fade rotated sky"
     state=f.state();assert state[0]==(2 if progress==1 else 1),(progress,state)
     rainProgress=progress
     f.checkAmbient(rainProgress,progress<1)
     if progress<1:assert abs(state[3]-min(duration*progress/phase.blendSeconds,1))<.00001
     expectedColour=1+.2*(phaseIndex-1)+.2*progress
     assert abs(f.floating(f.manager+0x80+0x318)-expectedColour)<.0001
     assert abs(f.floating(f.manager+0xfa0+0x318)-expectedColour)<.0001
     strength=(0 if phase.kind not in (1,2) else (.65 if phase.kind==1 else 1))
     if progress==1:
      assert (f.floating(f.node+0xd4)>0)==bool(strength), (phase.kind,f.floating(f.node+0xd4))
      assert (f.floating(f.node+0xd0)>0)==bool(strength)
     assert state[1]==startingWet and f.floating(f.renderer+0x1fc0)==startingWet
     for name,data in groundFields.items():assert bytes(f.u.mem_read(f.q(f.fields[name]+0x28),16))==data,(phase.kind,name)
     assert f.floating(f.q(f.fields['g_rce_weather_new_range']+0x28)+12)==float(initial in (1,2))
     for definition in range(7):assert f.floating(f.node+0xe24+definition*0x168)==float(initial in (1,2))
     fixedShape=struct.unpack('<4f',groundFields['g_rce_weather_old_shape'])
     for definition in range(7):
      for offset,value in zip((0xe0c,0xe1c,0xe20,0xe28),fixedShape):assert f.floating(f.node+offset+definition*0x168)==value
     for layer in range(2):
      before=bytes(f.u.mem_read(f.node+0xd68,0x9d8));f.call('DynamicParticleMaterial',f.node+0x110+layer*0x120)
      assert bytes(f.u.mem_read(f.node+0xd68,0x9d8))==before
    f.frame();assert f.floating(f.node+0x348+0x8c8)==heading, "Completion snapped sky heading"
    assert len(f.freed)==len(f.jobs)
    # The exact completion frame and a subsequent steady frame must continue
    # drawing the incoming rain/snow, rather than handing off to a dry count.
    for layer in range(2):
     target=f.n(f.node+0xe8);expected=min(f.n(f.node+0xe80+target*0x168+layer*0x68)*6,65536)
     assert f.call('DynamicWeatherParticleCount',f.node+0x110+layer*0x120)==expected
    f.tick(phase.startSeconds+duration+.1);f.frame()
    for layer in range(2):
     target=f.n(f.node+0xe8);expected=min(f.n(f.node+0xe80+target*0x168+layer*0x68)*6,65536)
     assert f.call('DynamicWeatherParticleCount',f.node+0x110+layer*0x120)==expected
   # Mid-transition destruction releases the retained sky and sun exactly once.
   if len(f.jobs):
    phase=p.phases[1];f.tick(phase.startSeconds+phase.blendSeconds*.25);f.frame()
    f.call('DynamicSkyDestroy',f.node+0x348);assert len(f.jobs)==len(f.freed) and f.state()[0]==0
   results.append(dict(base=hex(base),season=season,night=night,naval=naval,initial=initial,retainedTextures=len(f.jobs),freedExactlyOnce=len(f.freed)))
 f=FadeFixture(base,0,0,0,0,1,origin=0);f.wq(f.battle+8,0xdead00000000);f.tick(300);f.frame();assert f.state()[0]==0 and not f.jobs
 # Cold outgoing references do not replace the scene or allocate repeatedly.
 mask=policy.mask(0,0,0)&policy.mask(0,1,0);seed=0
 while True:
  i=Input(1,seed,1,0,0,0,0,mask);p=Plan();assert policy.make(C.byref(i),C.byref(p))
  if p.count>1:break
  seed+=1
 f=FadeFixture(base,0,0,0,0,seed);f.tick(0);f.wn(f.model+0x28,5);f.tick(0);f.frame();start=p.phases[1].startSeconds;duration=p.phases[1].blendSeconds
 f.ready=False;f.tick(start);f.frame();assert len(f.jobs)==2 and not f.scenes and f.state()[0]==2
 f.tick(start+1);f.frame();assert len(f.jobs)==2 and not f.scenes
 f.ready=True;f.tick(start+2);f.frame();assert f.scenes and f.state()[3]==0
 f.tick(start+2+duration*.5);f.frame();assert abs(f.state()[3]-.5)<.00001
 f.call('DynamicSkyDestroy',f.node+0x348);assert len(f.jobs)==len(f.freed)
 # An incoming cache miss holds all visual channels at zero progress; it does
 # not jump ahead to the wall-clock position once the texture becomes ready.
 f=FadeFixture(base,0,0,0,0,seed);f.tick(0);f.wn(f.model+0x28,5);f.tick(0);f.frame()
 f.handlers[0x19dbcd0]=lambda:f.ret(0 if len(f.jobs)>2 and f.reg(n.UC_X86_REG_RCX)==f.jobs[2][0] else 1)
 f.tick(start);f.frame();f.tick(start+5);f.frame();assert len(f.jobs)==3 and f.state()[3]==0
 f.handlers[0x19dbcd0]=lambda:f.ret(1)
 f.tick(start+6);f.frame();assert f.state()[3]==0
 f.tick(start+6+duration*.5);f.frame();assert abs(f.state()[3]-.5)<.00001
 f.call('DynamicSkyDestroy',f.node+0x348);assert len(f.jobs)==len(f.freed)
report=dict(status='PASS',colourTargetAndOutputContinuousOnWeatherClock=True,rainEnablesNativeLightningAndThunderIntervals=True,precipitationPersistsAfterCompletion=True,grassCullDefinitionsStayAtOpeningValues=True,rainAndSkyShareExactClock=True,startingPuddlesHeldAcrossEveryLaterPhaseAndCompletion=True,environmentSunAnglesFixedAcrossAllPhases=True,noRepeatedSkyJobRebuilds=True,fixedSkyOrientationAcrossAllPhases=True,nativeRegistryAndBufferInitializationExecuted=True,nativeDirtyAndTextureBindingExecuted=True,actualAmbientCallsiteExecuted=True,ambientOutgoingAndIncomingRatesFade=True,cases=len(results),customWeatherExclusion=True,coldTextureGuardsTestedAtThreeBases=True,results=results)
(W/'fade-native-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='results'},indent=2))
