"""Handwritten CE x64 agent landing and FOTS farm-card adapters.

The original 32-bit fixes are behavioral references only. Addresses, layouts,
native contracts and unwind metadata are verified against this CE binary.
No compiler is used for engine code. Both installed modes receive the delta.
"""
from pathlib import Path
import base64,hashlib,io,json,struct,zipfile
from trace_sim_turns import ROOT,GAME,PE,BASE

WORK=ROOT/'work/agent-farm-ce'
START=0x3776980
AGENT_HOOK=0xaed407
FARM_HOOK=0x7443a8
TRANSFER=0x7997a0
UNLOAD=0x788c30
COMPARE=0x19b6d0

class Emit:
 def __init__(self,start):self.start=start;self.code=bytearray();self.labels={};self.fixups=[]
 def raw(self,value):self.code.extend(bytes.fromhex(value))
 def mark(self,name):self.labels[name]=self.start+len(self.code)
 def target(self,opcode,target):
  self.raw(opcode);self.fixups.append((len(self.code),target));self.code.extend(bytes(4))
 def save(self,reg,off,load=False):
  high=reg>=8;self.raw(('4c' if high else '48')+('8b' if load else '89'))
  self.code.extend(bytes([0x84+((reg&7)<<3),0x24])+struct.pack('<I',off))
 def xmm(self,reg,off,load=False):
  self.raw('f3 0f '+('6f' if load else '7f'));self.code.extend(bytes([0x84+(reg<<3),0x24])+struct.pack('<I',off))
 def finish(self):
  for pos,target in self.fixups:
   value=self.labels[target] if isinstance(target,str) else target
   struct.pack_into('<i',self.code,pos,value-(self.start+pos+4))
  return bytes(self.code)

def agent(start):
 e=Emit(start);e.raw('48 81 ec c8 00 00 00')
 regs=[1,2,8,9,10,11,0]
 for i,r in enumerate(regs):e.save(r,0x20+8*i)
 for r in range(6):e.xmm(r,0x60+16*r)
 e.raw('48 85 c9');e.target('0f 84','restore')
 e.raw('48 8b 81 60 01 00 00 48 85 c0');e.target('0f 84','restore')
 e.raw('48 8b 00 48 85 c0');e.target('0f 84','restore')
 e.raw('48 3b c1');e.target('0f 84','restore')
 e.raw('4c 8b d0 8b 81 d4 00 00 00 45 8b 9a d4 00 00 00')
 e.raw('83 f8 03');e.target('0f 87','restore')
 e.raw('41 83 fb 03');e.target('0f 87','restore')
 e.raw('44 01 d8 83 f8 03');e.target('0f 87','restore')
 e.raw('48 8b d1 49 8b ca');e.target('e8',TRANSFER)
 e.mark('restore')
 for r in range(6):e.xmm(r,0x60+16*r,True)
 for i,r in enumerate(regs):e.save(r,0x20+8*i,True)
 e.raw('48 81 c4 c8 00 00 00');e.target('e9',UNLOAD)
 return e.finish()

def farm(start):
 e=Emit(start);e.raw('48 81 ec c8 00 00 00');e.save(1,0x20)
 e.target('e8',COMPARE);e.raw('84 c0');e.target('0f 85','return')
 # Preserve the first native comparison's complete volatile output context.
 regs=[1,2,8,9,10,11,0]
 for i,r in enumerate(regs):e.save(r,0x28+8*i)
 for r in range(6):e.xmm(r,0x60+16*r)
 e.save(1,0x20,True);e.target('48 8d 15','key');e.target('e8',COMPARE)
 e.raw('88 84 24 58 00 00 00')
 for r in range(6):e.xmm(r,0x60+16*r,True)
 for i,r in enumerate(regs):e.save(r,0x28+8*i,True)
 e.mark('return');e.raw('48 81 c4 c8 00 00 00 c3')
 function_size=len(e.code);e.mark('key');e.code.extend(b'bos_gdp_farm\0')
 return e.finish(),function_size

def sha(b):return hashlib.sha256(b).hexdigest()

def delta(old,new):
 writes=[];i=0
 while i<min(len(old),len(new)):
  if old[i]==new[i]:i+=1;continue
  start=i;last=i+1;gap=0
  while i<len(old) and i<len(new) and gap<=16:
   if old[i]!=new[i]:last=i+1;gap=0
   else:gap+=1
   i+=1
  writes.append(dict(offset=start,before=base64.b64encode(old[start:last]).decode(),data=base64.b64encode(new[start:last]).decode()));i=last
 return writes

def build():
 WORK.mkdir(exist_ok=True)
 normal=(GAME/'RemasteredCE/CE.dll').read_bytes();sim=(GAME/'RemasteredCE/CE8.dll').read_bytes()
 assert sha(normal)=='a367b51faa8c47a96c063c657993f7111076d53c5b0d1ec0c7b5ad23fd571290'
 assert sha(sim)=='52d24185176d680fd4281ffe5080c3745add31240dda706294dbfb777ae3fb8b'
 a=agent(START);farm_start=(START+len(a)+15)&~15;f,fsize=farm(farm_start)
 code=a+bytes(farm_start-START-len(a))+f
 rows=[];images={};metadata=[]
 for name,source in [('normal',normal),('sim8',sim)]:
  p=PE(source);image=bytearray(source);writes=[]
  def patch(rva,before,after,note):
   off=p.offset(rva);assert len(before)==len(after) and image[off:off+len(before)]==before,(name,hex(rva))
   image[off:off+len(after)]=after;writes.append(dict(rva=rva,offset=off,before=before.hex(),after=after.hex(),note=note))
  assert p.sections['.cepath']['rva']<=START and START+len(code)<=p.sections['.cepath']['rva']+p.sections['.cepath']['vs']
  patch(START,bytes(len(code)),code,'new adapters in existing verified zero RX padding')
  patch(AGENT_HOOK,bytes.fromhex('e8 24 b8 c9 ff'),b'\xe8'+struct.pack('<i',START-AGENT_HOOK-5),'native bulk-disembark call')
  patch(FARM_HOOK,bytes.fromhex('e8 23 73 a5 ff'),b'\xe8'+struct.pack('<i',farm_start-FARM_HOOK-5),'UI-only farm classification comparison')
  table,size=struct.unpack_from('<II',image,p.op+112+3*8);end=table+size;data=p.sections['.rcedata']
  assert p.offset(end)==data['off']+data['vs']
  old_rows=[struct.unpack_from('<III',image,p.offset(table)+i) for i in range(0,size,12)]
  assert [x[0] for x in old_rows]==sorted(x[0] for x in old_rows)
  assert old_rows[-1][1]<=START
  unwind=end+24
  # UWOP_ALLOC_LARGE(0), stack=200, 7-byte SUB RSP prologue; no saved nonvolatiles.
  info=bytes([1,7,2,0,7,1,25,0])
  addition=struct.pack('<III',START,START+len(a),unwind)+struct.pack('<III',farm_start,farm_start+fsize,unwind+8)+info+info
  assert p.offset(end)+len(addition)<=data['off']+data['size']
  patch(end,bytes(len(addition)),addition,'two sorted native x64 unwind entries and stack-allocation records')
  struct.pack_into('<I',image,p.op+112+3*8+4,size+24)
  struct.pack_into('<I',image,data['header']+8,data['vs']+len(addition))
  struct.pack_into('<I',image,p.op+64,0)
  checksum=0
  for at in range(0,len(image),2):checksum+=int.from_bytes(image[at:at+2],'little');checksum=(checksum&65535)+(checksum>>16)
  checksum=(checksum&65535)+(checksum>>16);struct.pack_into('<I',image,p.op+64,(checksum&65535)+len(image))
  images[name]=bytes(image);(WORK/(name+'.candidate.dll')).write_bytes(image)
  metadata.append(dict(mode=name,sourceSha256=sha(source),sha256=sha(image),writes=writes,exceptionTable=table,oldExceptionSize=size,newExceptionSize=size+24,unwindRva=unwind))
 normal_recipe=dict(beforeFinalSha256=sha(normal),afterFinalSha256=sha(images['normal']),patches=delta(normal,images['normal']))
 (WORK/'engine-post-update.json').write_text(json.dumps(normal_recipe,indent=2))
 package=(GAME/'RemasteredCE/release.rce').read_bytes();sig=struct.unpack_from('<I',package,8)[0]
 z=zipfile.ZipFile(io.BytesIO(package[12+sig:]));recipe=json.loads(z.read('sim-turns.json'))
 recipe['engine'].update(sourceSha256=sha(images['normal']),sha256=sha(images['sim8']),length=len(images['sim8']),writes=delta(images['normal'],images['sim8']),append=base64.b64encode(images['sim8'][len(images['normal']):]).decode())
 recipe['record'].update(normalEngineSha256=sha(images['normal']),engineSha256=sha(images['sim8']),build='sim8-integrated-local-r2-agent-farm')
 (WORK/'sim-turns-recipe.json').write_text(json.dumps(recipe,separators=(',',':')),encoding='utf-8')
 report=dict(status='BUILT_NOT_INSTALLED',agentHook=AGENT_HOOK,farmHook=FARM_HOOK,agentAdapter=START,agentBytes=len(a),farmAdapter=farm_start,farmFunctionBytes=fsize,codeBytes=len(code),stackBytes=200,modes=metadata,gameplayTested=False,engineCompiled=False)
 (WORK/'build.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='modes'}));print(json.dumps([{k:v for k,v in m.items() if k!='writes'} for m in metadata]))

if __name__=='__main__':build()
