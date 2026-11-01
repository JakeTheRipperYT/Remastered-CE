"""Execute compiled controller exports with bounded engine/registry stand-ins."""
from pathlib import Path
import sys,json,base64,struct
sys.dont_write_bytecode=True
sys.path[:0]=[r'F:/Codex/Temp/unit-selection-runtime',r'F:/Codex/Shogun2-CE/work/disasm_runtime',r'F:/Codex/Shogun-2-Original-Upgrade-Patch/research/x64/tool-build/audit-runtime']
import pefile
from unicorn import Uc,UC_ARCH_X86,UC_MODE_64,UC_HOOK_CODE
from unicorn.x86_const import *
W=Path(__file__).resolve().parent
layout=json.loads((W/'controller-layout.json').read_text());helper=json.loads((W/'candidate-helper.json').read_text())
class Fixture:
 def __init__(self,base):
  self.base=base;self.u=Uc(UC_ARCH_X86,UC_MODE_64);self.u.mem_map(base,0x4000000)
  self.u.mem_write(base+helper['rva'],base64.b64decode(helper['payload']))
  self.u.mem_map(0x100000,0x300000);self.u.mem_map(0x600000,0x20000);self.u.mem_map(0x7fff0000,4096)
  self.flags={};self.counts={};self.selected=[];self.copied=[];self.loads=[];self.missing=False;self.allow=True
  self.terrain=0x100000;self.records=0x110000;self.renderer=0x120000;self.pref=0x130000;self.prefvt=0x131000;self.pending=0x140000;self.context=0x150000;self.game=0x160000;self.alliance=0x170000
  self.day=[0x180000+i*0x1000 for i in range(4)];self.night=[0x190000+i*0x1000 for i in range(4)]
  self.setup_terrain(self.terrain,'campaign_maps/sho_japan/display'+chr(92))
  self.wq(self.pending+0x60,self.context);self.wq(self.context+8,self.game);self.wq(self.pending+0xa0,self.alliance);self.u.mem_write(self.alliance+0xa0,b'\x01')
  self.wq(self.pref,self.prefvt)
  self.wq(base+0x215a010,base+0x3ff0100);self.wq(base+0x215a020,base+0x3ff0200);self.wq(self.prefvt+0x68,base+0x3ff0300)
  self.handlers={0x1b8bce7:self.original_load,0x1b94e75:self.original_select,0x1b736b5:self.original_frame,
   0xe7fc50:self.preferences,0x185b290:self.open_key,0x19a070:self.string_ctor,0x19a3f0:self.string_dtor,
   0x1a75030:self.load_environment,0x1a6e5f0:self.current_environment,0x1a87bd0:self.copy_previous,0x1a4b990:self.copy_snapshot,
   0x1486015:self.original_checkbox_init,0x138d640:self.original_checkbox_signal,0x1489540:self.component_state,
   0x3ff0100:self.query,0x3ff0200:self.write,0x3ff0300:self.preference_path}
  self.handlers[json.loads((W.parents[1]/'work/night/layout.json').read_text())['exports']['NightSet']]=self.parent_night_set
  self.u.hook_add(UC_HOOK_CODE,self.hook)
 def reg(self,r):return self.u.reg_read(r)
 def wr(self,r,v):self.u.reg_write(r,v)
 def q(self,a):return struct.unpack('<Q',self.u.mem_read(a,8))[0]
 def n(self,a):return struct.unpack('<I',self.u.mem_read(a,4))[0]
 def wq(self,a,v):self.u.mem_write(a,struct.pack('<Q',v))
 def wn(self,a,v):self.u.mem_write(a,struct.pack('<I',v&0xffffffff))
 def ws(self,a,s,data=0x1f0000):
  b=s.encode('utf-16-le');self.u.mem_write(data,b+b'\0\0');self.u.mem_write(a,struct.pack('<QQQQ',len(s),len(s),0xdeadbeef,data))
 def string(self,a):return bytes(self.u.mem_read(self.q(a+24),(self.q(a)&65535)*2)).decode('utf-16-le')
 def zstr(self,a):
  b=bytearray()
  for i in range(300):
   c=bytes(self.u.mem_read(a+i*2,2))
   if c==b'\0\0':break
   b.extend(c)
  return b.decode('utf-16-le')
 def setup_terrain(self,t,path):
  self.wq(t+0x40,self.renderer);self.ws(t+0x60,path,t+0x900);self.wq(t+0x168,self.records);self.wn(t+0x164,4)
  for i,p in enumerate(self.day):self.wq(self.records+i*0x50,p)
 def ret(self,value=0):
  rsp=self.reg(UC_X86_REG_RSP);target=self.q(rsp);self.wr(UC_X86_REG_RAX,value&0xffffffffffffffff);self.wr(UC_X86_REG_RSP,rsp+8);self.wr(UC_X86_REG_RIP,target)
 def hook(self,u,address,size,data):
  if address==0x7fff0000:u.emu_stop();return
  handler=self.handlers.get(address-self.base)
  if handler:
   self.counts[handler.__name__]=self.counts.get(handler.__name__,0)+1;handler()
 def preferences(self):self.ret(self.pref)
 def preference_path(self):self.ws(self.reg(UC_X86_REG_RDX),'Software/Test/CE',0x1e0000);self.ret(self.reg(UC_X86_REG_RDX))
 def open_key(self):self.wq(self.reg(UC_X86_REG_RCX),0x111);self.ret(self.reg(UC_X86_REG_RCX))
 def query(self):
  name=self.zstr(self.reg(UC_X86_REG_RDX));rsp=self.reg(UC_X86_REG_RSP)
  if name not in self.flags:self.ret(2);return
  self.wn(self.q(rsp+0x28),self.flags[name]);self.wn(self.q(rsp+0x30),4);self.ret(0)
 def write(self):
  name=self.zstr(self.reg(UC_X86_REG_RDX));self.flags[name]=struct.unpack('<i',self.u.mem_read(self.q(self.reg(UC_X86_REG_RSP)+0x28),4))[0];self.ret(0)
 def string_ctor(self):
  out=self.reg(UC_X86_REG_RCX);source=self.reg(UC_X86_REG_RDX);s=self.zstr(source)
  self.u.mem_write(out,struct.pack('<QQQQ',len(s),len(s),0xdeadbeef,source));self.ret(out)
 def string_dtor(self):self.ret()
 def original_load(self):self.ret(self.reg(UC_X86_REG_R9))
 def load_environment(self):
  path=self.string(self.reg(UC_X86_REG_RDX));assert path.startswith('campaign_maps/sho_japan/display'+chr(92)+'environment'+chr(92)),path;self.loads.append(path)
  season=next(i for i,s in enumerate(['spring','summer','autumn','winter']) if 'rce_night_'+s+'.lighting' in path)
  self.ret(0 if self.missing else 0x1a0000 if self.loads.count(path)>1 else self.night[season])
 def narrow(self,a,s,data):
  self.u.mem_write(data,s.encode()+b'\0');self.u.mem_write(a,struct.pack('<QQQ',len(s),len(s),data))
 def narrow_value(self,a):
  return bytes(self.u.mem_read(self.q(a+16),self.q(a)&65535)).decode()
 def original_checkbox_init(self):
  component=self.reg(UC_X86_REG_RCX);self.wq(0x230000+8,component)
  # Actual initialization assigns the default state after the earlier factory.
  self.wq(component+0x158,0x241000);self.ret()
 def original_checkbox_signal(self):self.ret()
 def component_state(self):
  component=self.reg(UC_X86_REG_RCX);value=self.narrow_value(self.reg(UC_X86_REG_RDX));assert value in ['normal','selected']
  self.wq(component+0x158,0x240000 if value=='selected' else 0x241000);self.ret(1)
 def current_environment(self):self.ret(self.reg(UC_X86_REG_RCX)+0xfa0)
 def copy_snapshot(self):
  assert self.reg(UC_X86_REG_RCX)==0x1a0000
  assert self.reg(UC_X86_REG_RDX)==self.renderer+0xf88+0xfa0
  self.ret()
 def copy_previous(self):self.copied.append((self.reg(UC_X86_REG_RCX),self.reg(UC_X86_REG_RDX)));self.ret()
 def original_select(self):
  t=self.reg(UC_X86_REG_RCX);index=self.reg(UC_X86_REG_RDX)&0xffffffff;fade=self.reg(UC_X86_REG_R8)&255
  target=self.q(self.records+index*0x50) if index<4 else None
  self.selected.append(dict(terrain=t,index=index,fade=fade,target=target))
  if index<4:self.wn(t+0x170,index);self.wq(t+0x198,target)
  self.ret()
 def original_frame(self):
  # The adapter already executed the first three native pushes.
  rsp=self.reg(UC_X86_REG_RSP)
  for i,r in enumerate([UC_X86_REG_R13,UC_X86_REG_RSI,UC_X86_REG_RBP]):self.wr(r,self.q(rsp+i*8))
  self.wr(UC_X86_REG_RSP,rsp+24);self.ret()
 def parent_night_set(self):
  if self.allow:self.u.mem_write(self.reg(UC_X86_REG_RCX)+0x198,bytes([self.reg(UC_X86_REG_R8)&255]))
  self.ret()
 def call(self,name,*args):
  for r,v in zip([UC_X86_REG_RCX,UC_X86_REG_RDX,UC_X86_REG_R8,UC_X86_REG_R9],args):self.wr(r,v)
  sentinel={r:0xabc000+i*0x100 for i,r in enumerate([UC_X86_REG_RBX,UC_X86_REG_RBP,UC_X86_REG_RSI,UC_X86_REG_RDI,UC_X86_REG_R12,UC_X86_REG_R13,UC_X86_REG_R14,UC_X86_REG_R15])}
  for r,v in sentinel.items():self.wr(r,v)
  rsp=0x61f008;self.wq(rsp,0x7fff0000);self.wr(UC_X86_REG_RSP,rsp)
  self.u.emu_start(self.base+layout['exports'][name],0,count=250000)
  assert self.reg(UC_X86_REG_RIP)==0x7fff0000,(name,hex(self.reg(UC_X86_REG_RIP)))
  assert self.reg(UC_X86_REG_RSP)==rsp+8,name
  assert all(self.reg(r)==v for r,v in sentinel.items()),name
  return self.reg(UC_X86_REG_RAX)
 def load(self):
  for i in range(4):assert self.call('NightMapLoad',self.terrain,0,0,i)==i
 def frame(self):self.call('NightMapFrame',self.terrain,0)
 def toggle(self,value):self.call('NightMapBattleSet',self.pending,0,int(value))

def scenario(base):
 f=Fixture(base);f.load();assert len(f.loads)==5;assert f.flags['RCE_NightBattlePreview']==-1
 f.call('NightMapSelect',f.terrain,0,1);assert f.selected[-1]['target']==f.day[0] and f.selected[-1]['fade']==0
 f.toggle(True);f.frame();assert f.selected[-1]['target']==f.night[0] and f.selected[-1]['fade']==1
 assert f.q(f.records)==f.day[0] and len(f.copied)==1
 f.toggle(False);f.frame();assert f.selected[-1]['target']==f.day[0] and len(f.copied)==2
 f.flags['RCE_AlwaysNightCampaign']=1;f.frame();assert f.selected[-1]['target']==f.night[0]
 count=len(f.selected);f.toggle(False);f.frame();assert len(f.selected)==count
 f.flags['RCE_AlwaysNightCampaign']=-1;f.frame();assert f.selected[-1]['target']==f.day[0]
 f.toggle(True);f.frame();f.flags['RCE_NightBattlePreview']=-1;f.frame();assert f.selected[-1]['target']==f.day[0]
 f.toggle(True);f.frame();f.call('NightMapSelect',f.terrain,3,1);assert f.selected[-1]['target']==f.night[3]
 assert f.q(f.records+3*0x50)==f.day[3]
 f.flags['RCE_NightBattlePreview']=-1;f.frame();assert f.selected[-1]['target']==f.day[3]
 f.allow=False;f.u.mem_write(f.pending+0x198,b'\0');f.toggle(True);f.frame();assert f.selected[-1]['target']==f.day[3]
 f.allow=True;f.u.mem_write(f.game+0x25e0,b'\x01');old=f.flags['RCE_NightBattlePreview'];f.toggle(True);assert f.flags['RCE_NightBattlePreview']==old
 f.u.mem_write(f.game+0x25e0,b'\0');f.u.mem_write(f.alliance+0xa0,b'\0');f.toggle(True);f.frame();assert f.selected[-1]['target']==f.night[3]
 other=0x200000;f.setup_terrain(other,'campaign_maps/gem_japan/display');before=len(f.loads)
 f.call('NightMapLoad',other,0,0,0);assert len(f.loads)==before
 f.call('NightMapSelect',other,0,1);assert f.selected[-1]['target']==f.day[0]
 f.missing=True;f.load();f.flags['RCE_AlwaysNightCampaign']=1;f.call('NightMapSelect',f.terrain,1,1);assert f.selected[-1]['target']==f.day[1]
 assert f.counts['parent_night_set']>=7 and f.counts['open_key']==1
 # Real UI strings differ from native wide path strings: 24-byte narrow vs32-byte wide.
 component=0x220000;checkbox=0x230000
 f.narrow(component+0x110,'rce_campaign_always_night',0x246000)
 f.narrow(0x240020,'selected',0x247000);f.narrow(0x241020,'normal',0x248000)
 f.wq(component+0x158,0x241000)
 f.wq(component+0x158,0);f.call('NightCheckboxInit',component,0)
 assert f.q(component+0x158)==0x240000 # existing always-on flag restored
 f.wq(component+0x158,0x241000);f.wq(0x250000,component);f.u.mem_write(0x250008,b'\x00');f.call('NightCheckboxCommit',0,0x250000)
 assert f.flags['RCE_AlwaysNightCampaign']==-1
 f.call('NightCheckboxInit',component,0);assert f.q(component+0x158)==0x241000
 f.wq(component+0x158,0x240000);f.wq(0x250000,component);f.u.mem_write(0x250008,b'\x01');f.call('NightCheckboxCommit',0,0x250000)
 assert f.flags['RCE_AlwaysNightCampaign']==1
 f.call('NightCheckboxInit',component,0);assert f.q(component+0x158)==0x240000
 f.narrow(component+0x110,'checkbox_v_sync',0x246000);f.wq(component+0x158,0x241000)
 f.wq(0x250000,component);f.u.mem_write(0x250008,b'\x00');f.call('NightCheckboxCommit',0,0x250000);assert f.flags['RCE_AlwaysNightCampaign']==1
 f.call('NightCheckboxInit',component,0);assert f.q(component+0x158)==0x241000
 return dict(base=hex(base),checks=27,nativeCalls=sum(f.counts.values()),status='PASS')
if __name__=='__main__':
 rows=[scenario(base) for base in [0x180000000,0x230000000,0x7ff600000000]]
 result=dict(status='PASS',compiledControllerExecuted=True,engineAndRegistryCallsModeled=True,results=rows,totalChecks=sum(r['checks'] for r in rows))
 (W/'native-controller-tests.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
