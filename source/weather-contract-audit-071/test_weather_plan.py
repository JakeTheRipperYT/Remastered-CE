"""Execute the actual C++ forecast policy natively; no game process or writes."""
from pathlib import Path
import ctypes as C, subprocess, os, json, collections
W=Path(__file__).resolve().parent
vcroot=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC')
vc=sorted(vcroot.iterdir(),key=lambda p:tuple(map(int,p.name.split('.'))))[-1]/'bin/Hostx64/x64'
source='''#include "weather_plan.h"
#include "weather_catalog.h"
extern "C" __declspec(dllexport) unsigned mask(unsigned s,unsigned n,unsigned v) {
 unsigned m=0;for(unsigned i=0;i<weatherAssetCount;i++) {
 const WeatherAsset& a=weatherAssets[i];if(a.season==s&&a.night==n&&a.naval==v)m|=1u<<a.kind;
 }return m;
}
extern "C" __declspec(dllexport) bool make(const Weather::Input* i,Weather::Plan* p){return Weather::make(*i,*p);}
extern "C" __declspec(dllexport) unsigned phase(const Weather::Plan* p,float t){return Weather::phaseAt(*p,t);}
extern "C" __declspec(dllexport) float progress(const Weather::Plan* p,unsigned i,float t){return Weather::progress(*p,i,t);}
extern "C" __declspec(dllexport) void describe(const Weather::Plan* p,bool n,wchar_t* b,unsigned c){Weather::describe(*p,n,b,c);}
extern "C" int _fltused=0;
'''
(W/'plan_test_exports.cpp').write_text(source)
env=os.environ.copy();env['TEMP']=env['TMP']='F:/Codex/Temp'
subprocess.run([str(vc/'cl.exe'),'/nologo','/O1','/GS-','/GR-','/EHs-c-','/Zl','/LD',str(W/'plan_test_exports.cpp'),'/link','/noentry','/nodefaultlib',f'/out:{W/"plan_test.dll"}'],cwd=W,env=env,check=True)
class Input(C.Structure):_fields_=[(n,C.c_uint) for n in ['campaign','seed','waitRoll','season','night','naval','initial','available']]
class Phase(C.Structure):_fields_=[(n,C.c_uint) for n in ['kind','startSeconds','blendSeconds']]
class Plan(C.Structure):_fields_=[('count',C.c_uint),('phases',Phase*4)]
d=C.CDLL(str(W/'plan_test.dll'))
d.mask.argtypes=[C.c_uint]*3;d.mask.restype=C.c_uint
d.make.argtypes=[C.POINTER(Input),C.POINTER(Plan)];d.make.restype=C.c_bool
d.phase.argtypes=[C.POINTER(Plan),C.c_float];d.phase.restype=C.c_uint
d.progress.argtypes=[C.POINTER(Plan),C.c_uint,C.c_float];d.progress.restype=C.c_float
d.describe.argtypes=[C.POINTER(Plan),C.c_bool,C.POINTER(C.c_wchar),C.c_uint]
checked=0;sequences=set();counts=collections.Counter();samples=[]
for season in range(4):
 for night in range(2):
  for naval in range(2):
   mask=d.mask(season,night,naval)
   assert mask&1 and mask&8
   for initial in range(6):
    if not mask>>initial&1:continue
    for seed in range(512):
     for roll in range(4):
      i=Input(1,seed,roll,season,night,naval,initial,mask);before=bytes(i)
      p=Plan();assert d.make(C.byref(i),C.byref(p));assert bytes(i)==before
      p2=Plan();assert d.make(C.byref(i),C.byref(p2));assert bytes(p)==bytes(p2)
      assert 1<=p.count<=4 and p.phases[0].kind==initial and p.phases[0].startSeconds==0
      for j in range(p.count):
       x=p.phases[j];assert mask>>x.kind&1
       assert (x.kind not in (1,2)) if season==3 else (x.kind not in (4,5))
       if j:
        previous=p.phases[j-1];assert x.kind!=previous.kind
        assert x.startSeconds>=previous.startSeconds+120 and 30<=x.blendSeconds<=60
        assert previous.startSeconds+previous.blendSeconds<x.startSeconds
        assert d.phase(C.byref(p),x.startSeconds-.01)==j-1
        assert d.phase(C.byref(p),x.startSeconds)==j
        assert d.progress(C.byref(p),j,x.startSeconds)==0
        assert abs(d.progress(C.byref(p),j,x.startSeconds+x.blendSeconds/2)-.5)<.0001
        assert d.progress(C.byref(p),j,x.startSeconds+x.blendSeconds+10)==1
      # Reads at an unchanged battle time are stable, including paused time.
      assert d.phase(C.byref(p),200)==d.phase(C.byref(p),200)
      text=C.create_unicode_buffer(128);d.describe(C.byref(p),night,text,128)
      assert text.value and len(text.value)<100 and text.value[0].isupper()
      tiny=C.create_unicode_buffer(4);d.describe(C.byref(p),night,tiny,4);assert tiny[3]=='\0'
      if p.count>1:
       slot=p.phases[1].startSeconds;assert 180<=slot<=240
       assert all(p.phases[j].startSeconds==slot*j for j in range(p.count))
       assert len({p.phases[j].kind for j in range(p.count)})==p.count
       for step in (p.count,p.count+1,p.count*3+1,40):
        index=step%p.count;start=step*slot
        assert d.phase(C.byref(p),start-.01)==(index+p.count-1)%p.count
        assert d.phase(C.byref(p),start)==index
        assert d.progress(C.byref(p),index,start)==0
        assert abs(d.progress(C.byref(p),index,start+p.phases[index].blendSeconds/2)-.5)<.0001
       assert 'intermittent' in text.value.lower() and 'at first' not in text.value
      sequence=tuple(p.phases[j].kind for j in range(p.count));sequences.add(sequence);counts[p.count]+=1
      if len(samples)<12 and p.count>=2 and sequence not in [s['sequence'] for s in samples]:samples.append(dict(sequence=sequence,forecast=text.value))
      # A custom battle never receives a forecast, regardless of its seed.
      i.campaign=0;p.count=99;assert not d.make(C.byref(i),C.byref(p)) and p.count==0
      checked+=1
for change,value in [('season',4),('initial',6),('night',2),('naval',2),('available',0)]:
 i=Input(1,1,1,0,0,0,0,0xF);setattr(i,change,value);p=Plan()
 assert not d.make(C.byref(i),C.byref(p)) and p.count==0
assert all(counts[n] for n in range(1,5)) and len(sequences)>=20
report=dict(status='PASS_FORECAST_POLICY_ONLY_NOT_INSTALLED',allMultiStatePlansCycle=True,equalStateIntervals=True,wraparoundFadesChecked=True,inputs=checked,uniqueSequences=len(sequences),phaseCounts=dict(counts),examples=samples)
(W/'forecast-test-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
