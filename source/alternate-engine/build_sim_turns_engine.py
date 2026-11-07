"""Guarded alternate CE engine, preserving the installed normal engine.

Relocates the supplied mod's reachable machine code and private data into new
sections of our accepted CE engine. No engine source compiler is invoked.
"""
from pathlib import Path
import base64,hashlib,json,re,struct
from trace_sim_turns import ROOT,WORK,GAME,SIM,PE,BASE

def sha(b):return hashlib.sha256(b).hexdigest()
def align(v,a=0x1000):return (v+a-1)&~(a-1)

def build():
 trace=json.loads((WORK/'trace.json').read_text())
 original=PE((GAME/'empire.retail.x64.dll').read_bytes());supplied=PE(SIM.read_bytes())
 ours=PE((GAME/'RemasteredCE/CE.dll').read_bytes());image=bytearray(ours.b)
 assert sha(image)=='a367b51faa8c47a96c063c657993f7111076d53c5b0d1ec0c7b5ad23fd571290'
 blocks=trace['blocks'];cursor=0
 for block in blocks:
  block['offset']=cursor;cursor=align(cursor+block['end']-block['start'])
 span=cursor
 start=align(max(s['rva']+max(s['vs'],s['size']) for s in ours.sections.values()))
 data_start=start+span
 code=bytearray(span);data=bytearray(span)
 for block in blocks:
  value=(supplied.read(block['start'],block['end']-block['start']) if block['name']!='turn_state' else bytes(block['end']-block['start']))
  code[block['offset']:block['offset']+len(value)]=value
  data[block['offset']:block['offset']+len(value)]=value
 instructions={i['rva']:i for i in trace['instructions']}
 code_bytes=set()
 for i in instructions.values():code_bytes.update(range(i['rva'],i['rva']+i['size']))
 def injected(rva):return any(b['start']<=rva<b['end'] for b in blocks)
 def mapped(rva,force_code=False):
  block=next((b for b in blocks if b['start']<=rva<b['end']),None)
  if not block:return rva
  return (start if force_code or rva in code_bytes else data_start)+block['offset']+rva-block['start']
 def local(rva):
  block=next(b for b in blocks if b['start']<=rva<b['end'])
  return block['offset']+rva-block['start']
 fixups=[]
 def instruction(i,moved):
  raw=bytearray.fromhex(i['raw']);old_pc=i['rva'];new_pc=mapped(old_pc,True) if moved else old_pc
  references=[]
  match=re.match(r'(call|j\w+)\s+([0-9A-Fa-f]{16})$',i['text'])
  if match:references.append((int(match[2],16)-BASE,'branch'))
  references += [(int(p,16)-BASE,'rip') for p in re.findall(r'\[([0-9A-Fa-f]{16})h\]',i['text'])]
  for old_target,kind in references:
   new_target=mapped(old_target,kind=='branch');old_delta=old_target-old_pc-i['size'];new_delta=new_target-new_pc-i['size']
   size=1 if kind=='branch' and len(raw)==2 else 4
   needle=old_delta.to_bytes(size,'little',signed=True)
   positions=([len(raw)-size] if kind=='branch' else [p for p in range(len(raw)-size+1) if raw[p:p+size]==needle])
   assert len(positions)==1,(hex(old_pc),i['text'],positions)
   assert raw[positions[0]:positions[0]+size]==needle
   at=positions[0];raw[at:at+size]=new_delta.to_bytes(size,'little',signed=True)
   fixups.append(dict(site=old_pc,newSite=new_pc,kind=kind,oldTarget=old_target,newTarget=new_target,field=at,size=size))
  return bytes(raw)
 for i in instructions.values():
  value=instruction(i,True);at=local(i['rva']);code[at:at+len(value)]=value
 # Absolute pointers in injected tables are rebased, and receive explicit DIR64
 # loader relocations in their new locations. No preferred-base assumption.
 relocations=[];pointers=[]
 for block in blocks:
  if block['name']=='turn_state':continue
  raw=supplied.read(block['start'],block['end']-block['start'])
  for at in range(len(raw)-7):
   old_value=struct.unpack_from('<Q',raw,at)[0]
   if BASE<=old_value<BASE+0x3750000:
    source=block['start']+at;target=old_value-BASE;new_value=BASE+mapped(target)
    # Image pointers cannot straddle a decoded instruction boundary.
    if any(p in code_bytes for p in range(source,source+8)):
     assert all(p in code_bytes for p in range(source,source+8)),hex(source)
    for dest,buffer in [(start,code),(data_start,data)]:
     pos=block['offset']+at;struct.pack_into('<Q',buffer,pos,new_value);relocations.append(dest+pos)
    pointers.append(dict(source=source,target=target,newTarget=mapped(target)))
 writes=[]
 def write(rva,value,note):
  at=ours.offset(rva);before=bytes(image[at:at+len(value)])
  image[at:at+len(value)]=value;writes.append(dict(rva=rva,offset=at,before=before.hex(),after=value.hex(),note=note))
 # First retain every small native edit outside the relocated blocks.
 for row in trace['nativePatches']:
  rva=row['start'];value=bytes.fromhex(row['sim']);old=bytes.fromhex(row['original']);live=ours.read(rva,len(value))
  assert all(v==o or v==n for v,o,n in zip(live,old,value)),f'Native patch conflict {rva:x}'
  write(rva,value,'supplied native patch')
 # Repair complete instructions containing relocated references. Guards cover the
 # whole native instruction, including bytes equal in the two source images.
 done=set()
 for row in trace['nativePatches']:
  for i in row.get('instructions',[]):
   if i['rva'] in done:continue
   done.add(i['rva']);value=instruction(i,False)
   before=original.read(i['rva'],i['size']);live=ours.read(i['rva'],i['size'])
   assert live==before or live==supplied.read(i['rva'],i['size']),f'Instruction conflict {i["rva"]:x}'
   write(i['rva'],value,'native instruction with relocated references')
  if 'pointerRva' in row:
   pointer=row['pointerRva'];value=struct.pack('<Q',BASE+mapped(row['pointerTarget'],True))
   write(pointer,value,'native vtable pointer; existing DIR64 relocation retained')
 # Only alternate output paths change: original filename matching stays intact.
 old='RemasteredCE\\data\\data.pack\0'.encode('utf-16le')
 new='RemasteredCE\\data\\data.sim8\0'.encode('utf-16le')
 positions=[m.start() for m in re.finditer(re.escape(old),image)];assert len(positions)==2
 for at in positions:
  image[at:at+len(new)]=new;writes.append(dict(offset=at,before=old.hex(),after=new.hex(),note='sim-only lobby UI container; normal pack remains unchanged'))
 # Keep the normal engine's relocation table verbatim; append only new pointers.
 rr,rs=struct.unpack_from('<II',ours.b,ours.op+112+5*8)
 old_reloc=ours.read(rr,rs);reloc_at=align(len(data),4);data.extend(bytes(reloc_at-len(data)));data.extend(old_reloc)
 pages={}
 for rva in sorted(set(relocations)):pages.setdefault(rva&~4095,[]).append(0xa000|(rva&4095))
 for page,entries in pages.items():
  if len(entries)%2:entries.append(0)
  data.extend(struct.pack('<II',page,8+len(entries)*2)+struct.pack('<'+'H'*len(entries),*entries))
 count=len(ours.sections);header=ours.table+count*40
 assert header+80<=min(s['off'] for s in ours.sections.values())
 raw_at=align(len(image),0x200)
 image.extend(bytes(raw_at-len(image)))
 for index,(name,rva,payload,flags) in enumerate([(b'.s8code',start,code,0x60000020),(b'.s8data',data_start,data,0xc0000040)]):
  pos=header+index*40;size=align(len(payload),0x200);off=len(image)
  image[pos:pos+40]=bytes(40);image[pos:pos+len(name)]=name
  struct.pack_into('<IIII',image,pos+8,len(payload),rva,size,off);struct.pack_into('<I',image,pos+36,flags)
  image.extend(payload);image.extend(bytes(size-len(payload)))
 struct.pack_into('<H',image,ours.nt+6,count+2)
 struct.pack_into('<I',image,ours.op+56,align(data_start+len(data)))
 struct.pack_into('<II',image,ours.op+112+5*8,data_start+reloc_at,len(data)-reloc_at)
 struct.pack_into('<I',image,ours.op+4,struct.unpack_from('<I',image,ours.op+4)[0]+align(len(code),0x200))
 struct.pack_into('<I',image,ours.op+8,struct.unpack_from('<I',image,ours.op+8)[0]+align(len(data),0x200))
 struct.pack_into('<I',image,ours.op+64,0)
 checksum=0
 for at in range(0,len(image),2):
  checksum+=int.from_bytes(image[at:at+2],'little');checksum=(checksum&65535)+(checksum>>16)
 checksum=(checksum&65535)+(checksum>>16);struct.pack_into('<I',image,ours.op+64,(checksum&65535)+len(image))
 output=WORK/'CE8.candidate.dll';output.write_bytes(image)
 report=dict(status='BUILT_NOT_INSTALLED_NOT_GAMEPLAY_TESTED',normalEngineSha256=sha(ours.b),suppliedSha256=sha(supplied.b),candidateSha256=sha(image),candidateSize=len(image),
  blocks=blocks,codeRva=start,dataRva=data_start,fixups=fixups,absolutePointers=pointers,addedBaseRelocations=len(set(relocations)),writes=writes,
  normalEngineModified=False,compilerInvoked=False,inheritedSimUnwindMetadataAbsent=True)
 (WORK/'engine-integration.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in report.items() if k not in ['writes','fixups','absolutePointers','blocks']}))

if __name__=='__main__':build()
