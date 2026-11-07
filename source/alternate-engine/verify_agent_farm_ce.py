"""Execute actual handwritten adapter bytes against hostile native ABI stubs.

This is bounded instruction emulation, not a gameplay or full native-engine test.
Native stubs deliberately overwrite volatile registers, XMM state and shadow
space to detect argument, stack, preservation and return-path mistakes.
"""
import hashlib,itertools,json,struct
from trace_sim_turns import ROOT,GAME,PE,BASE
from build_agent_farm_ce import WORK,START,AGENT_HOOK,FARM_HOOK,TRANSFER,UNLOAD,COMPARE

MASK=(1<<64)-1
VOL=[0,1,2,8,9,10,11]

class Machine:
 def __init__(self,p,base,seed=1):
  self.p=p;self.base=base;self.reg=[((seed+3)*(i+7)*0x123456789abc)&MASK for i in range(16)]
  self.reg[4]=0x7000000008;self.xmm=[bytes([(seed+i)&255])*16 for i in range(16)]
  self.mem={};self.z=False;self.c=False;self.calls=[];self.steps=0;self.keys={};self.first_post=None;self.transfers=[]
  self.put(self.reg[4],0x6000000000,8)
 def read(self,addr,size):
  if self.base<=addr<self.base+0x4000000:
   return self.p.read(addr-self.base,size)
  return bytes(self.mem.get(addr+i,0) for i in range(size))
 def put(self,addr,value,size):
  raw=value.to_bytes(size,'little') if isinstance(value,int) else value
  assert len(raw)==size
  for i,b in enumerate(raw):self.mem[addr+i]=b
 def u(self,addr,size=8):return int.from_bytes(self.read(addr,size),'little')
 def clobber(self):
  k=len(self.calls)
  for r in VOL:self.reg[r]=(0xaabb000000000000+r*0x1234567+k*0x123456789)&MASK
  for r in range(6):self.xmm[r]=bytes([(r+97+k)&255])*16
  # A native callee owns all four home slots, not our saved context above them.
  for slot in range(4):self.put(self.reg[4]+8+slot*8,0xdead0000+slot,8)
 def native(self,target,ret):
  assert self.reg[4]%16==0,'unaligned CALL'
  rcx,rdx=self.reg[1],self.reg[2];self.reg[4]-=8;self.put(self.reg[4],ret,8)
  self.calls.append(target)
  if target==self.base+TRANSFER:
   self.transfers.append((rcx,rdx));a=self.u(rdx+0xd4,4);b=self.u(rcx+0xd4,4)
   self.put(rdx+0xd4,0,4);self.put(rcx+0xd4,a+b,4);result=None
  elif target==self.base+COMPARE:
   literal=[];pos=rdx
   while self.u(pos,1):literal.append(self.u(pos,1));pos+=1;assert len(literal)<100
   result=self.keys.get(rcx)==bytes(literal).decode()
  else:raise AssertionError(hex(target))
  self.clobber()
  if result is not None:self.reg[0]=(self.reg[0]&~255)|int(result)
  self.reg[4]+=8
  if len(self.calls)==1:self.first_post=(self.reg[:],self.xmm[:])
 def run(self,rva):
  pc=self.base+rva
  while True:
   self.steps+=1;assert self.steps<300
   b=self.read(pc,16);n=0
   if b[:3] in [b'\x48\x81\xec',b'\x48\x81\xc4']:
    v=int.from_bytes(b[3:7],'little');self.reg[4]+=(-v if b[2]==0xec else v);n=7
   elif b[0] in [0x48,0x4c] and b[1] in [0x89,0x8b] and b[3]==0x24 and b[2]&0xc7==0x84:
    reg=((b[2]>>3)&7)+(8 if b[0]==0x4c else 0);off=int.from_bytes(b[4:8],'little');addr=self.reg[4]+off
    if b[1]==0x89:self.put(addr,self.reg[reg],8)
    else:self.reg[reg]=self.u(addr)
    n=8
   elif b[:3] in [b'\xf3\x0f\x7f',b'\xf3\x0f\x6f']:
    reg=(b[3]>>3)&7;assert b[4]==0x24;off=int.from_bytes(b[5:9],'little');addr=self.reg[4]+off
    if b[2]==0x7f:self.put(addr,self.xmm[reg],16)
    else:self.xmm[reg]=self.read(addr,16)
    n=9
   elif b[:3]==bytes.fromhex('48 85 c9'):self.z=self.reg[1]==0;self.c=False;n=3
   elif b[:3]==bytes.fromhex('48 85 c0'):self.z=self.reg[0]==0;self.c=False;n=3
   elif b[:3]==bytes.fromhex('48 3b c1'):self.z=self.reg[0]==self.reg[1];self.c=self.reg[0]<self.reg[1];n=3
   elif b[:3]==bytes.fromhex('48 8b 81'):self.reg[0]=self.u(self.reg[1]+int.from_bytes(b[3:7],'little'));n=7
   elif b[:3]==bytes.fromhex('48 8b 00'):self.reg[0]=self.u(self.reg[0]);n=3
   elif b[:3]==bytes.fromhex('4c 8b d0'):self.reg[10]=self.reg[0];n=3
   elif b[:2]==bytes.fromhex('8b 81'):self.reg[0]=self.u(self.reg[1]+int.from_bytes(b[2:6],'little'),4);n=6
   elif b[:3]==bytes.fromhex('45 8b 9a'):self.reg[11]=self.u(self.reg[10]+int.from_bytes(b[3:7],'little'),4);n=7
   elif b[:3]==bytes.fromhex('83 f8 03'):v=self.reg[0]&0xffffffff;self.z=v==3;self.c=v<3;n=3
   elif b[:4]==bytes.fromhex('41 83 fb 03'):v=self.reg[11]&0xffffffff;self.z=v==3;self.c=v<3;n=4
   elif b[:3]==bytes.fromhex('44 01 d8'):self.reg[0]=(self.reg[0]+self.reg[11])&0xffffffff;n=3
   elif b[:3]==bytes.fromhex('48 8b d1'):self.reg[2]=self.reg[1];n=3
   elif b[:3]==bytes.fromhex('49 8b ca'):self.reg[1]=self.reg[10];n=3
   elif b[:3]==bytes.fromhex('48 8d 15'):self.reg[2]=pc+7+int.from_bytes(b[3:7],'little',signed=True);n=7
   elif b[:4]==bytes.fromhex('88 84 24 58'):self.put(self.reg[4]+int.from_bytes(b[3:7],'little'),self.reg[0]&255,1);n=7
   elif b[:2]==bytes.fromhex('84 c0'):self.z=(self.reg[0]&255)==0;self.c=False;n=2
   elif b[0]==0x0f and b[1] in [0x84,0x85,0x87]:
    taken={0x84:self.z,0x85:not self.z,0x87:not self.c and not self.z}[b[1]]
    pc=pc+6+(int.from_bytes(b[2:6],'little',signed=True) if taken else 0);continue
   elif b[0] in [0xe8,0xe9]:
    target=pc+5+int.from_bytes(b[1:5],'little',signed=True)
    if b[0]==0xe9:assert target==self.base+UNLOAD;return 'unload'
    self.native(target,pc+5);pc+=5;continue
   elif b[0]==0xc3:self.reg[4]+=8;return 'return'
   else:raise AssertionError((hex(pc),b.hex()))
   pc+=n

def verify():
 build=json.loads((WORK/'build.json').read_text());agent_cases=farm_cases=0
 for mode in build['modes']:
  name=mode['mode'];old=PE((GAME/'RemasteredCE'/('CE.dll' if name=='normal' else 'CE8.dll')).read_bytes());new=PE((WORK/(name+'.candidate.dll')).read_bytes())
  assert hashlib.sha256(new.b).hexdigest()==mode['sha256'] and len(old.b)==len(new.b)
  allowed=set()
  for w in mode['writes']:
   at=w['offset'];before=bytes.fromhex(w['before']);after=bytes.fromhex(w['after']);assert old.b[at:at+len(before)]==before and new.b[at:at+len(after)]==after;allowed.update(range(at,at+len(after)))
  for pos,size in [(old.op+64,4),(old.op+112+3*8+4,4),(old.sections['.rcedata']['header']+8,4)]:allowed.update(range(pos,pos+size))
  assert not any(i not in allowed for i,(a,b) in enumerate(zip(old.b,new.b)) if a!=b)
  for base,seed,source_count,dest_count,link in itertools.product([BASE,0x210000000,0x7ff600000000],[1,19],range(5),range(5),['valid','null','empty','self']):
   m=Machine(new,base,seed);fleet=0x80000000;army=0x81000000;handle=0x82000000
   m.reg[1]=fleet;m.put(fleet+0xd4,source_count,4);m.put(army+0xd4,dest_count,4)
   m.put(fleet+0x160,0 if link=='null' else handle,8);m.put(handle,0 if link=='empty' else fleet if link=='self' else army,8)
   initial=m.reg[:];xmm=m.xmm[:];assert m.run(START)=='unload'
   expected=link=='valid' and source_count<=3 and dest_count<=3 and source_count+dest_count<=3
   assert m.transfers==([(army,fleet)] if expected else []),(name,source_count,dest_count,link)
   assert m.reg==initial and m.xmm==xmm,'caller state changed before native unload'
   agent_cases+=1
  for base,seed,key in itertools.product([BASE,0x210000000,0x7ff600000000],[1,19],['gdp_farm','bos_gdp_farm','gdp_industry','gdp_port','gdp_mine','custom_effect','']):
   m=Machine(new,base,seed);m.reg[1]=0x80000000;m.keys[m.reg[1]]=key;m.reg[2]=0x90000000;m.put(m.reg[2],b'gdp_farm\0',9)
   initial=m.reg[:];xmm=m.xmm[:];assert m.run(build['farmAdapter'])=='return'
   expected=key in ['gdp_farm','bos_gdp_farm'];assert (m.reg[0]&255)==expected
   post,post_xmm=m.first_post
   for r in range(16):
    if r==4:assert m.reg[r]==initial[r]+8
    elif r==0:assert m.reg[r]==((post[r]&~255)|int(expected))
    else:assert m.reg[r]==post[r]
   assert m.xmm==post_xmm
   assert len(m.calls)==(1 if key=='gdp_farm' else 2)
   farm_cases+=1
  table,size=struct.unpack_from('<II',new.b,new.op+112+3*8);rows=[struct.unpack('<III',new.read(table+i,12)) for i in range(0,size,12)]
  assert [r[0] for r in rows]==sorted(r[0] for r in rows)
  for begin,end,info in rows[-2:]:assert new.read(info,8)==bytes([1,7,2,0,7,1,25,0]) and new.read(begin,7)==bytes.fromhex('48 81 ec c8 00 00 00')
 report=dict(status='PASS_NATIVE_CONTRACT_EMULATION',agentCases=agent_cases,farmCases=farm_cases,bothModes=True,aslrBases=3,stackAlignmentAndShadowSpace=True,volatileGprAndXmmPreserved=True,unwindEntriesVerified=True,fullImageDiffGuarded=True,gameplayTested=False)
 (WORK/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))

if __name__=='__main__':verify()
