"""Read-only native campaign/ground snapshot. No screenshots, input or writes to game memory."""
from pathlib import Path
import ctypes as C,struct,json,sys,re,subprocess,time
W=Path(__file__).parent;K=C.WinDLL('kernel32',use_last_error=True);P=C.WinDLL('psapi',use_last_error=True)
K.OpenProcess.argtypes=[C.c_uint,C.c_int,C.c_uint];K.OpenProcess.restype=C.c_void_p
K.ReadProcessMemory.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)];K.ReadProcessMemory.restype=C.c_int
K.CloseHandle.argtypes=[C.c_void_p]
P.EnumProcessModulesEx.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.POINTER(C.c_uint),C.c_uint];P.EnumProcessModulesEx.restype=C.c_int
P.GetModuleFileNameExW.argtypes=[C.c_void_p,C.c_void_p,C.c_wchar_p,C.c_uint];P.GetModuleFileNameExW.restype=C.c_uint
class Live:
 def __init__(self,pid):
  self.pid=pid;self.handle=K.OpenProcess(0x410,False,pid)
  if not self.handle:raise OSError(C.get_last_error(),'Cannot read game')
  mods=(C.c_void_p*2048)();n=C.c_uint();assert P.EnumProcessModulesEx(self.handle,mods,C.sizeof(mods),C.byref(n),3)
  self.base=0
  for mod in mods[:n.value//C.sizeof(C.c_void_p)]:
   path=C.create_unicode_buffer(1024);P.GetModuleFileNameExW(self.handle,mod,path,1024)
   if path.value.replace('\\','/').lower().endswith('/remasteredce/ce.dll'):self.base=mod;break
  assert self.base,'Patched CE module not loaded'
 def read(self,address,size):
  if address<0x10000:raise ValueError('Null pointer')
  buffer=C.create_string_buffer(size);done=C.c_size_t()
  if not K.ReadProcessMemory(self.handle,address,buffer,size,C.byref(done)) or done.value!=size:raise OSError(C.get_last_error(),hex(address))
  return buffer.raw
 def q(self,a):return struct.unpack('<Q',self.read(a,8))[0]
 def u(self,a):return struct.unpack('<I',self.read(a,4))[0]
 def f(self,a):return struct.unpack('<f',self.read(a,4))[0]
 def snapshot(self):
  B=self.base;H=B+0x3744000;ui=self.q(B+0x3372c28);battle=self.q(ui+0x2b0) if ui else 0
  out=dict(pid=self.pid,engineBase=hex(B),battle=hex(battle),campaign=False)
  if not battle:return out
  out['campaign']=bool(self.read(battle+0x283c9,1)[0])
  if not out['campaign']:return out
  setup=self.q(battle+8);model=self.q(setup+0x110);out.update(stage=self.u(model+0x28),simulationSeconds=self.f(model+0x38),currentPrecipitation=self.u(setup+0xc8))
  a=H+0x1b460;ground=self.read(a,96);b,s,o,asset,definition=struct.unpack_from('<QQQII',ground)
  out['openingGround']=dict(battle=hex(b),specification=hex(s),owner=hex(o),asset=asset,definition=definition,captured=bool(ground[32]),shape=struct.unpack_from('<4f',ground,36),material=struct.unpack_from('<4f',ground,52),range=struct.unpack_from('<4f',ground,68),wet=struct.unpack_from('<f',ground,84)[0],grassCull=struct.unpack_from('<f',ground,88)[0])
  a=H+0x1b4c0;render=self.read(a,768);r_battle,node,manager=struct.unpack_from('<QQQ',render)
  out['renderer']=dict(battle=hex(r_battle),node=hex(node),manager=hex(manager),generation=struct.unpack_from('<I',render,40)[0],step=struct.unpack_from('<I',render,48)[0],blending=bool(render[92]),densityProgress=struct.unpack_from('<f',render,80)[0],surfaceProgress=struct.unpack_from('<f',render,84)[0],startingWet=struct.unpack_from('<f',render,520)[0],startingGrassCull=struct.unpack_from('<f',render,524)[0])
  if node:
   owner=self.q(node+0x50);out['renderer']['nativeSurfaceWater']=self.f(owner+0x1fc0) if owner else None
  a=H+0x1b3d0;forecast=self.read(a,136);out['forecast']=dict(battle=hex(struct.unpack_from('<Q',forecast)[0]),initial=struct.unpack_from('<I',forecast,40)[0],count=struct.unpack_from('<I',forecast,48)[0],phases=[dict(zip(['kind','startSeconds','blendSeconds'],struct.unpack_from('<III',forecast,52+i*12))) for i in range(min(4,struct.unpack_from('<I',forecast,48)[0]))],generation=struct.unpack_from('<I',forecast,120)[0],elapsed=struct.unpack_from('<f',forecast,124)[0],active=bool(struct.unpack_from('<I',forecast,128)[0]),stage=struct.unpack_from('<I',forecast,132)[0])
  parent=H+0x1b070;data=self.q(parent+0x18)
  if data:out['weatherBuffer']=list(struct.unpack('<28f',self.read(data,112)))
  return out
 def close(self):K.CloseHandle(self.handle)
if __name__=='__main__':
 if len(sys.argv)>1:pid=int(sys.argv[1])
 else:
  s=subprocess.check_output(['powershell.exe','-NoProfile','-Command','Get-Process -Name shogun2_complete_edition -ErrorAction Stop | Select-Object -First 1 -ExpandProperty Id'],text=True);pid=int(s.strip())
 live=Live(pid)
 try:
  result=live.snapshot();(W/'live-latest.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
 finally:live.close()
