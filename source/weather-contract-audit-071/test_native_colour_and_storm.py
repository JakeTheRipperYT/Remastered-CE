from pathlib import Path
import json,struct
W=Path(__file__).resolve().parent
scope={'__file__':str(W/'test_fades_native.py')}
exec(compile((W/'test_fades_native.py').read_text().split('\nresults=[]')[0],str(W/'test_fades_native.py'),'exec'),scope)
F=scope['FadeFixture'];n=scope['n'];stock=scope['stock'];rows=[]
for base in [0x180000000,0x230000000,0x7ff600000000]:
 f=F(base,0,0,0,0,1)
 f.u.mem_write(base+0x1a732d0,stock.get_data(0x1a732d0,0x2d0))
 f.u.mem_write(base+0x1b9dab0,stock.get_data(0x1b9dab0,0xc0))
 n.layout['exports']['NativeTonalBlend']=0x1a732d0;n.layout['exports']['NativeSheetEvent']=0x1b9dab0
 out=0x3d4000;target=0x3d5000;old=0x3d6000
 for offset in range(0x48,0x9c,4):f.wfloat(target+offset,1.7);f.wfloat(old+offset,.8)
 for progress in (0,.001,.25,.5,.75,.999,1):
  f.wr(n.UC_X86_REG_XMM3,struct.unpack('<I',struct.pack('<f',1-progress))[0]);f.call('NativeTonalBlend',out,target,old)
  for offset in range(0x48,0x9c,4):assert abs(f.floating(out+offset)-(.8+.9*progress))<.00001
 audio=0x3d7000;audioVt=0x3d7100;sky=f.node+0x348;position=0x3d7200;listener=0x3d7300;listenerVt=0x3d7400
 f.wq(sky+0x778,f.renderer);f.wq(sky+0x780,f.node);f.wq(sky+0x7e0,audio);f.wq(sky+0x7f0,0x12345678)
 f.wq(audio,audioVt);f.wq(audioVt+0xc0,base+0x3ff0900)
 f.wq(f.node+0x1780,0x3d7500);f.wq(f.node+0x1788,0x3d7540)
 f.wq(0x3d7508,0x3d7540);f.wq(0x3d7510,listener);f.wq(listener,listenerVt);f.wq(listenerVt+8,base+0x3ff0a00)
 sounds=[];effects=[]
 def audioEvent():
  sounds.append((f.reg(n.UC_X86_REG_R8),f.reg(n.UC_X86_REG_R9)));f.ret()
 def visualEvent():effects.append(f.reg(n.UC_X86_REG_RDX));f.ret()
 f.handlers[0x3ff0900]=audioEvent;f.handlers[0x3ff0a00]=visualEvent
 f.call('NativeSheetEvent',sky,position)
 assert sounds==[(0x12345678,position)] and effects==[position],(sounds,effects)
 rows.append(dict(base=hex(base),nativeTonalSamples=7,nativeLightningVisualAndSoundDispatch=True))
report=dict(status='PASS',actualNativeTonalInterpolationExecuted=True,actualNativeLightningSoundAndEffectDispatchExecuted=True,rows=rows,liveAudioVisualAcceptancePending=True)
(W/'native-colour-storm-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
