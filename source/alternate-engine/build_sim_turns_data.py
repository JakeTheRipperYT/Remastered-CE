"""Compose a mode-only UI container from our complete current private data pack.

The normal container is never edited. The alternate has a non-.pack extension
so native movie-pack discovery cannot activate the lobby in normal mode.
"""
from pathlib import Path
import ctypes,hashlib,json,struct
from trace_sim_turns import ROOT,WORK,GAME

def digest(path):
 with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def index(path):
 with path.open('rb') as f:
  header=f.read(32);flags,_,deps,count,size=struct.unpack_from('<5I',header,4);f.seek(32+deps);raw=f.read(size)
 entries={};pos=0
 for i in range(count):
  start=pos
  if flags&32:offset,length,stored=struct.unpack_from('<QII',raw,pos);pos+=16
  else:offset,length=struct.unpack_from('<QI',raw,pos);stored=length;pos+=12
  if flags&64:pos+=8
  end=raw.index(0,pos);name=raw[pos:end].decode().replace('\\','/');pos=end+1
  entries[name]=dict(offset=offset,length=length,stored=stored,metadata=32+deps+start,record=raw[start:pos],compressed=bool(flags&32))
 assert pos==len(raw)
 return header,entries

def build():
 source=GAME/'RemasteredCE/data/data.pack'
 assert digest(source)=='b87fc4b18d8d960974579b2b743375a0de61270567b006db5190b383c42af705'
 supplied=Path(r'C:\Users\CT-MK2\Downloads\SimTurnsBeta8P 1.1\SimTurnsBeta8P 1.1\eight_player_lobby.pack')
 assert digest(supplied)=='77e135031ed9097a78e6a7c1c2e04d5dcacee73226d59766ea2529029434e0b7'
 library=WORK/'lz4.dll';resource=ROOT/'source/current-launcher/lz4'
 if not library.exists():library.write_bytes(resource.read_bytes())
 assert digest(library)==digest(resource)
 lz=ctypes.CDLL(str(library));lz.LZ4_compressBound.argtypes=[ctypes.c_int]
 lz.LZ4_compress_default.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_int]
 header,entries=index(source);_,mods=index(supplied)
 flags=struct.unpack_from('<I',header,4)[0]
 assert flags&32 and struct.unpack_from('<I',header,12)[0]==0
 record_prefix=16+(8 if flags&64 else 0)
 assets={}
 for name,entry in mods.items():
  assert not entry['compressed']
  with supplied.open('rb') as f:f.seek(entry['offset']);raw=f.read(entry['length'])
  target=ctypes.create_string_buffer(lz.LZ4_compressBound(len(raw)))
  size=lz.LZ4_compress_default(raw,target,len(raw),len(target));assert size>0
  assets[name]=dict(raw=raw,encoded=target.raw[:size])
 old_payload=min(e['offset'] for e in entries.values())
 # Preserve record order; add only the two missing gift-selection UI records.
 names=list(entries)+[name for name in assets if name not in entries]
 record_size=sum(len(entries[name]['record']) if name in entries else record_prefix+len(name.encode())+1 for name in names)
 new_payload=((32+record_size+63)//64)*64;shift=new_payload-old_payload
 assert shift>=0
 tail=source.stat().st_size+shift;new_index=bytearray();asset_rows=[]
 for name in names:
  if name in entries:
   record=bytearray(entries[name]['record']);struct.pack_into('<Q',record,0,entries[name]['offset']+shift)
  else:record=bytearray(record_prefix)+name.replace('/','\\').encode()+b'\0'
  if name in assets:
   asset=assets[name];encoded=asset['encoded'];struct.pack_into('<QII',record,0,tail,len(asset['raw']),len(encoded))
   asset_rows.append(dict(path=name,offset=tail,size=len(asset['raw']),stored=len(encoded),sha256=hashlib.sha256(asset['raw']).hexdigest(),encodedSha256=hashlib.sha256(encoded).hexdigest()))
   tail+=len(encoded)
  new_index.extend(record)
 assert len(new_index)==record_size
 new_header=bytearray(header);struct.pack_into('<I',new_header,16,len(names));struct.pack_into('<I',new_header,20,len(new_index))
 prefix=new_header+new_index+bytes(new_payload-32-len(new_index))
 output=WORK/'data.sim8'
 with output.open('wb') as target,source.open('rb') as stream:
  target.write(prefix);stream.seek(old_payload)
  while block:=stream.read(8*1024*1024):target.write(block)
  for row in asset_rows:assert target.tell()==row['offset'];target.write(assets[row['path']]['encoded'])
 assert output.stat().st_size==tail
 # Re-read every record, and compare the complete unchanged source payload.
 _,built=index(output)
 assert set(built)==set(entries)|set(assets)
 for name,entry in entries.items():
  if name not in assets:
   after=built[name];assert after['offset']==entry['offset']+shift and after['length']==entry['length'] and after['stored']==entry['stored']
 with source.open('rb') as a,output.open('rb') as b:
  a.seek(old_payload);b.seek(new_payload)
  while block:=a.read(8*1024*1024):assert b.read(len(block))==block
 report=dict(status='BUILT_VERIFIED_NOT_INSTALLED',sourceSha256=digest(source),sha256=digest(output),length=tail,
  sourcePayloadOffset=old_payload,outputPayloadOffset=new_payload,sourcePayloadByteIdentical=True,
  entriesPreserved=len(entries)-len(set(entries)&set(assets)),changedUI=asset_rows,normalDataPackModified=False)
 (WORK/'data-integration.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 print(json.dumps(report),flush=True)

if __name__=='__main__':build()
