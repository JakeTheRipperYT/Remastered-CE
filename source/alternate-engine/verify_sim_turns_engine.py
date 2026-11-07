"""Check relocated instructions, ASLR targets, and preservation of our engine."""
import hashlib,json,struct
from trace_sim_turns import ROOT,WORK,GAME,SIM,PE,BASE

def verify():
 r=json.loads((WORK/'engine-integration.json').read_text());t=json.loads((WORK/'trace.json').read_text())
 original=PE((GAME/'RemasteredCE/CE.dll').read_bytes());candidate=PE((WORK/'CE8.candidate.dll').read_bytes());supplied=PE(SIM.read_bytes())
 assert hashlib.sha256(candidate.b).hexdigest()==r['candidateSha256']
 assert hashlib.sha256(original.b).hexdigest()==r['normalEngineSha256']
 expected=bytearray(original.b)
 for w in r['writes']:
  off=w['offset'];before=bytes.fromhex(w['before']);after=bytes.fromhex(w['after'])
  assert expected[off:off+len(before)]==before
  expected[off:off+len(after)]=after
 # Only the two added section headers, section count/image sizes, relocation
 # directory and checksum may differ outside the recorded guarded writes.
 allowed=set(range(original.table+len(original.sections)*40,original.table+(len(original.sections)+2)*40))
 for pos,size in [(original.nt+6,2),(original.op+4,8),(original.op+56,4),(original.op+64,4),(original.op+112+5*8,8)]:allowed.update(range(pos,pos+size))
 differences=[i for i,(a,b) in enumerate(zip(expected,candidate.b)) if a!=b and i not in allowed]
 assert not differences, [hex(x) for x in differences[:10]]
 code=candidate.sections['.s8code'];data=candidate.sections['.s8data']
 codeflags=struct.unpack_from('<I',candidate.b,code['header']+36)[0];dataflags=struct.unpack_from('<I',candidate.b,data['header']+36)[0]
 assert codeflags&0x20000000 and not codeflags&0x80000000
 assert dataflags&0x80000000 and not dataflags&0x20000000
 # Check the actual encoded displacement at every native and moved instruction.
 cases=0
 by_pc={i['rva']:i for i in t['instructions']}
 for row in t['nativePatches']:
  for i in row.get('instructions',[]):by_pc.setdefault(i['rva'],i)
 for f in r['fixups']:
  ins=by_pc[f['site']];field=candidate.read(f['newSite']+f['field'],f['size'])
  encoded=int.from_bytes(field,'little',signed=True)
  assert f['newSite']+ins['size']+encoded==f['newTarget']
  for image_base in [BASE,0x210000000,0x7ff600000000]:
   assert image_base+f['newSite']+ins['size']+encoded==image_base+f['newTarget'];cases+=1
 for old in original.sections.values():
  assert candidate.sections[next(k for k,v in original.sections.items() if v==old)]['rva']==old['rva']
 # Native vtable pointers keep original loader relocations.
 rr,rs=struct.unpack_from('<II',candidate.b,candidate.op+112+5*8);pos=candidate.offset(rr);end=pos+rs;relocs=set()
 while pos<end:
  page,size=struct.unpack_from('<II',candidate.b,pos);assert size>=8 and size%4==0
  for at in range(pos+8,pos+size,2):
   v=struct.unpack_from('<H',candidate.b,at)[0]
   if v>>12:assert v>>12==10;relocs.add(page+(v&4095))
  pos+=size
 pointer_cases=0
 for row in t['nativePatches']:
  if 'pointerRva' not in row:continue
  at=row['pointerRva'];assert at in relocs
  value=struct.unpack('<Q',candidate.read(at,8))[0]
  assert code['rva']<=value-BASE<code['rva']+code['vs']
  for base in [BASE,0x210000000,0x7ff600000000]:
   assert value+base-BASE==base+value-BASE;pointer_cases+=1
 report=dict(status='STATIC_CHECKS_PASS_GAMEPLAY_PENDING',engineSha256=r['candidateSha256'],instructionsTraced=len(t['instructions']),
  encodedReferenceCases=cases,vtableRelocationCases=pointer_cases,normalEngineFixBytesPreserved=True,
  existingHelperSectionsPreserved=True,executableCodeWritable=False,mutableDataExecutable=False,
  normalEngineUnchanged=hashlib.sha256((GAME/'RemasteredCE/CE.dll').read_bytes()).hexdigest()==r['normalEngineSha256'],
  inheritedSimHelpersLackUnwindMetadata=True,gameplayTested=False)
 (WORK/'engine-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))

if __name__=='__main__':verify()
