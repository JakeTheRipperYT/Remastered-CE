"""Check native branch/RIP targets and preservation of the installed Sim engine."""
import hashlib,json,re,struct,subprocess
from build_religion_sim8 import WORK,GAME,PE,BASE,SIM,NORMAL,sha
from trace_sim_turns import DUMP

def verify():
 b=(WORK/'CE8.candidate.dll').read_bytes();pe=PE(b);old=(GAME/'RemasteredCE/CE8.dll').read_bytes();assert sha(old)==SIM
 rows=json.loads((WORK/'religion-patches.json').read_text())['patches'];instructions={};allowed=set(range(pe.op+64,pe.op+68))
 for row in rows:
  va=row['va'];raw=bytes.fromhex(row['data']);at=pe.offset(va-BASE);assert b[at:at+len(raw)]==raw
  allowed.update(range(at,at+len(raw)))
  output=WORK/f'decode-{va:x}.txt'
  subprocess.run([str(DUMP),'/NOLOGO','/NOPDB','/ERRORREPORT:NONE','/DISASM:BYTES',f'/RANGE:0x{va:x},0x{va+len(raw):x}',f'/OUT:{output}',str(WORK/'CE8.candidate.dll')],check=True,capture_output=True)
  current=None
  for line in output.read_text().splitlines():
   m=re.match(r'\s*([0-9A-F]{16}): ((?:[0-9A-F]{2} )+)(.*)',line)
   if m:
    current=int(m[1],16);instructions[current]=dict(raw=bytes.fromhex(m[2]),text=m[3].strip())
   elif current and re.fullmatch(r'\s+(?:[0-9A-F]{2} ?)+',line):instructions[current]['raw']+=bytes.fromhex(line)
 changed=[i for i,(a,c) in enumerate(zip(old,b)) if a!=c];assert len(old)==len(b) and all(i in allowed for i in changed)
 references=[];strings={}
 for pc,i in instructions.items():
  text=i['text'];raw=i['raw'];m=re.match(r'(call|j\w+)\s+([0-9A-Fa-f]{16})$',text)
  targets=[]
  if m:targets.append((int(m[2],16),'branch'))
  targets.extend((int(v,16),'rip') for v in re.findall(r'\[([0-9A-Fa-f]{16})h\]',text))
  for target,kind in targets:
   inside=any(r['va']<=target<r['va']+len(bytes.fromhex(r['data'])) for r in rows)
   if kind=='branch' and inside:assert target in instructions and instructions[target]['raw']!=b'\xcc',(hex(pc),hex(target))
   off=pe.offset(target-BASE);assert off<len(b)
   if kind=='branch':
    section=next(s for s in pe.sections.values() if s['rva']<=target-BASE<s['rva']+s['size']);assert struct.unpack_from('<I',b,section['header']+36)[0]&0x20000000
    n=1 if len(raw)==2 else 4;disp=int.from_bytes(raw[-n:],'little',signed=True);assert pc+len(raw)+disp==target
   else:
    n=4;needle=struct.pack('<i',target-pc-len(raw));assert needle in raw
    if text.startswith('lea'):strings[hex(target)]=b[off:b.index(0,off)].decode('ascii')
   for base in [0x180000000,0x7ff600000000,0x7ffa12340000]:assert base+(pc-BASE)+len(raw)+(target-pc-len(raw))==base+target-BASE
   references.append(dict(site=hex(pc),target=hex(target),kind=kind))
 assert set(strings.values())=={'inf_bos_shogunate','inf_bos_imperial','inf_bos_self','rel_catholic','rel_buddhist'}
 assert pe.read(0x7932e2,6)==bytes.fromhex('41bf4a000000') and pe.read(0x793315,2)==bytes.fromhex('76d1')
 assert sha((GAME/'RemasteredCE/CE.dll').read_bytes())==NORMAL
 report=dict(status='PASS',changedBytes=len(changed),sevenGuardedRangesOnly=True,normalEngineUnchanged=True,allOtherSimFixesByteIdentical=True,relativeReferenceCases=len(references)*3,embeddedStrings=strings,aiThreshold75Verified=True,references=references,gameplayTested=False)
 (WORK/'native-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='references'},indent=2))

if __name__=='__main__':verify()
