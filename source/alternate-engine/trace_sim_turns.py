"""Read-only native trace for the supplied Sim Turns build; no engine compiler.

Uses the installed Visual Studio disassembler, not another project's libraries.
All generated analysis stays within the established CE project.
"""
from pathlib import Path
import hashlib,json,re,struct,subprocess

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'work/sim-turns-integration'
GAME=Path(r'D:\SteamLibrary\steamapps\common\Shogun 2 Complete Edition')
SIM=Path(r'C:\Users\CT-MK2\Downloads\SimTurnsBeta8P 1.1\SimTurnsBeta8P 1.1\empire.retail.x64.dll')
DUMP=Path(r'C:\Program Files\Microsoft Visual Studio\18\Community\VC\Tools\MSVC\14.51.36231\bin\Hostx64\x64\dumpbin.exe')
BASE=0x180000000

class PE:
 def __init__(self,data):
  self.b=data;self.nt=struct.unpack_from('<I',data,60)[0];self.op=self.nt+24
  self.table=self.op+struct.unpack_from('<H',data,self.nt+20)[0];self.sections={}
  for i in range(struct.unpack_from('<H',data,self.nt+6)[0]):
   at=self.table+40*i;vs,rva,size,off=struct.unpack_from('<4I',data,at+8)
   self.sections[data[at:at+8].rstrip(b'\0').decode()]=dict(rva=rva,vs=vs,size=size,off=off,header=at)
 def offset(self,rva):
  for s in self.sections.values():
   if s['rva']<=rva<s['rva']+s['size']:return s['off']+rva-s['rva']
  raise ValueError(hex(rva))
 def read(self,rva,size):return self.b[self.offset(rva):self.offset(rva)+size]

def disassemble(start,end):
 path=WORK/f'decode-{start:x}-{end:x}.txt'
 if not path.exists():
  subprocess.run([str(DUMP),'/NOLOGO','/NOPDB','/ERRORREPORT:NONE','/DISASM:BYTES',f'/RANGE:0x{BASE+start:x},0x{BASE+end:x}',f'/OUT:{path}',str(SIM)],check=True,capture_output=True)
 result={};current=None
 for line in path.read_text(errors='replace').splitlines():
  match=re.match(r'\s*([0-9A-F]{16}): ((?:[0-9A-F]{2} )+)(.*)',line)
  if match:
   current=int(match[1],16)-BASE;raw=bytes.fromhex(match[2]);text=match[3].strip()
   result[current]=dict(rva=current,raw=raw.hex(),text=text,size=len(raw))
  elif current is not None and re.fullmatch(r'\s+(?:[0-9A-F]{2} ?)+',line):
   result[current]['raw']+=bytes.fromhex(line).hex();result[current]['size']=len(bytes.fromhex(result[current]['raw']))
 return result

def groups(points,gap=0):
 rows=[]
 for p in points:
  if rows and p-rows[-1][1]<=gap:rows[-1][1]=p+1
  else:rows.append([p,p+1])
 return rows

def trace():
 WORK.mkdir(exist_ok=True)
 original=PE((GAME/'empire.retail.x64.dll').read_bytes());sim=PE(SIM.read_bytes());ours=PE((GAME/'RemasteredCE/CE.dll').read_bytes())
 assert hashlib.sha256(original.b).hexdigest()=='f1b609dffb95c1fa6b155264fdea0fc73e74c235dfc4e00b0d7e66076937b64e'
 assert hashlib.sha256(sim.b).hexdigest()=='018594c54ecae0924ccec26398007549a93d4b3c698c5ddc09f3f5a4fe7d42c8'
 assert hashlib.sha256(ours.b).hexdigest()=='a367b51faa8c47a96c063c657993f7111076d53c5b0d1ec0c7b5ad23fd571290'
 text=original.sections['.text'];reloc=original.sections['.reloc'];data=original.sections['.data']
 blocks=[dict(name='lobby_helper',start=(text['rva']+text['vs']+15)&~15,end=sim.sections['.text']['rva']+sim.sections['.text']['vs']),
         dict(name='turn_helpers',start=(reloc['rva']+reloc['vs']+15)&~15,end=sim.sections['.reloc']['rva']+sim.sections['.reloc']['vs']),
         dict(name='turn_state',start=data['rva']+data['vs'],end=sim.sections['.data']['rva']+sim.sections['.data']['vs'])]
 def injected(rva):return any(b['start']<=rva<b['end'] for b in blocks)
 # Decode patches from original function entrypoints supplied by the PE runtime
 # function table. This avoids guessing instruction boundaries at operand edits.
 prva,psize=struct.unpack_from('<II',sim.b,sim.op+112+3*8)
 functions=[struct.unpack_from('<III',sim.b,sim.offset(prva)+i) for i in range(0,psize,12)]
 seeds=set();native=[]
 for name,s in original.sections.items():
  if name not in ['.text','.rdata','.data']:continue
  old=original.read(s['rva'],s['size']);new=sim.read(s['rva'],s['size'])
  points=[s['rva']+i for i,(a,b) in enumerate(zip(old,new)) if a!=b and not injected(s['rva']+i)]
  for begin,end in groups(points,8):
   row=dict(section=name,start=begin,end=end,original=original.read(begin,end-begin).hex(),sim=sim.read(begin,end-begin).hex())
   native.append(row)
   if name=='.text':
    f=next((f for f in functions if f[0]<=begin<f[1]),None)
    if f:
     decoded=disassemble(f[0],min(f[1],end+32))
    elif sim.read(begin,1) in [b'\xe9',b'\xeb',b'\xc3']:
     decoded=disassemble(begin,end+32)
    elif sim.read(begin-1,1)==b'\xe9' and end-begin<=4:
     decoded=disassemble(begin-1,end+32)
    else:
     row['requiresManualBoundary']=True
     continue
    for at,ins in decoded.items():
     if at+ins['size']<=begin or at>=end:continue
     raw=bytes.fromhex(ins['raw'])
     match=re.match(r'(call|j\w+)\s+([0-9A-Fa-f]{16})$',ins['text'])
     if match:
      target=int(match[2],16)-BASE
      if injected(target):seeds.add(target)
     row.setdefault('instructions',[]).append(ins)
 # Native vtables also enter injected functions through existing DIR64 pointers.
 for row in native:
  if row['section']=='.rdata':
   pointer=row['start']&~7
   value=struct.unpack('<Q',sim.read(pointer,8))[0]-BASE
   if injected(value):
    seeds.add(value);row['pointerRva']=pointer;row['pointerTarget']=value
 # Starting from every native detour, follow branch/call reachability rather
 # than decoding embedded text and pointer tables as instructions.
 decoded={};queue=list(seeds);entries=set(seeds)
 while queue:
  entry=queue.pop()
  if entry in decoded:continue
  block=next(b for b in blocks if b['start']<=entry<b['end'])
  local=disassemble(entry,min(block['end'],entry+0x1800));pc=entry
  while pc not in decoded:
   assert pc in local, f'Decode unavailable at {pc:x}'
   ins=local[pc];decoded[pc]=ins;text=ins['text'];match=re.match(r'(call|j\w+)\s+([0-9A-Fa-f]{16})$',text)
   if match:
    target=int(match[2],16)-BASE;ins['branchTarget']=target
    if injected(target):
     queue.append(target)
     if match[1]=='call':entries.add(target)
    if match[1]=='jmp':break
   if re.match(r'(ret|int\s+3|ud2)\b',text):break
   if text.startswith('jmp '):break
   pc+=ins['size']
   if not injected(pc):break
  assert len(decoded)<10000
 result=dict(blocks=blocks,nativePatches=native,seeds=sorted(seeds),entries=sorted(entries),instructions=[decoded[k] for k in sorted(decoded)])
 (WORK/'trace.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
 print(json.dumps(dict(blocks=blocks,nativePatchGroups=len(native),seeds=len(seeds),decodedInstructions=len(decoded),entries=len(entries))))

if __name__=='__main__':trace()
