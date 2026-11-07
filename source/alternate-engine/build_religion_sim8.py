"""Guarded religion_swap integration into the existing alternate engine recipe.

No supplied installer is executed and no engine source is compiled. The normal
engine, normal packs, saves and user.script.txt are never written here.
"""
from pathlib import Path
import base64,ctypes,hashlib,json,re,struct,sys
sys.dont_write_bytecode=True
from trace_sim_turns import ROOT,GAME,PE,BASE
from build_sim_turns_data import index,digest

WORK=ROOT/'work/religion-sim8'
SUPPLIED=Path(r'C:\Users\CT-MK2\Downloads\religion_swap\religion_swap')
NORMAL='071249e2fa79f21646e0da6d8070ff89f26bc3c85906798a6af09d650633c044'
SIM='5dd028577255ece4acb2e666960b111aba8f791749ffcd83723665292a38762d'
DATA='8be89f8eb7904c1bb6c14081ae7e80f1479f2114184a12a54905e813719772a1'
PACK='277f4edba47c53c97b302f9fa948c18b61406953c6fdd416a9aded01a0e7fbba'
def sha(b):return hashlib.sha256(b).hexdigest()
def b64(b):return base64.b64encode(b).decode()
def checksum(b,op):
 struct.pack_into('<I',b,op+64,0);s=0
 for at in range(0,len(b),2):
  s+=int.from_bytes(b[at:at+2],'little');s=(s&65535)+(s>>16)
 s=(s&65535)+(s>>16);struct.pack_into('<I',b,op+64,(s&65535)+len(b))

def capture():
 WORK.mkdir(exist_ok=True)
 recipe=WORK/'religion-patches.json'
 if recipe.exists():return
 raw=(SUPPLIED/'religion_swap_dll.ps1').read_bytes()
 text=raw.decode('utf-8-sig').split('# older religion_swap versions:')[0]
 rows=re.findall(r"Va = (0x[0-9A-Fa-f]+); Off = (0x[0-9A-Fa-f]+); Old = '([0-9a-f]+)'; New = '([0-9a-f]+)'",text)
 assert len(rows)==7
 data=dict(source='User supplied religion_swap DLL patch v5; private integration, AI change explicitly authorized.',scriptSha256=sha(raw),patches=[dict(va=int(va,16),originalOffset=int(off,16),before=old,data=new) for va,off,old,new in rows])
 recipe.write_text(json.dumps(data,indent=2),encoding='utf-8')
 pack=(SUPPLIED/'religion_swap.pack').read_bytes();assert sha(pack)==PACK
 (WORK/'religion_swap.pack').write_bytes(pack)

def build():
 capture();normal=(GAME/'RemasteredCE/CE.dll').read_bytes();old=(GAME/'RemasteredCE/CE8.dll').read_bytes()
 assert sha(normal)==NORMAL and sha(old)==SIM
 original=PE((GAME/'empire.retail.x64.dll').read_bytes());pe=PE(old);new=bytearray(old)
 patches=json.loads((WORK/'religion-patches.json').read_text())['patches'];changed=set();guard_rows=[]
 for row in patches:
  rva=row['va']-BASE;at=pe.offset(rva);before=bytes.fromhex(row['before']);after=bytes.fromhex(row['data'])
  assert len(before)==len(after) and original.offset(rva)==row['originalOffset']
  assert original.read(rva,len(before))==before and pe.read(rva,len(before))==before, f'Patch conflict at RVA {rva:x}'
  new[at:at+len(after)]=after;changed.update(range(at,at+len(after)))
  guard_rows.append(dict(rva=rva,offset=at,length=len(after),beforeSha256=sha(before),afterSha256=sha(after)))
 checksum(new,pe.op);changed.update(range(pe.op+64,pe.op+68))
 assert all(a==b or i in changed for i,(a,b) in enumerate(zip(old,new))) and len(old)==len(new)
 (WORK/'CE8.candidate.dll').write_bytes(new)
 recipe=json.loads((ROOT/'work/agent-farm-ce/sim-turns-recipe.json').read_text())
 assert recipe['record']['engineSha256']==SIM and recipe['record']['dataSha256']==DATA
 # Rebuild the complete normal-to-alternate recipe; retain all earlier edits.
 writes=[];i=0
 while i<len(normal):
  if normal[i]==new[i]:i+=1;continue
  start=i;last=i+1;gap=0
  while i<len(normal) and gap<=16:
   if normal[i]!=new[i]:last=i+1;gap=0
   else:gap+=1
   i+=1
  writes.append(dict(offset=start,before=b64(normal[start:last]),data=b64(new[start:last])));i=last
 recipe['engine']=dict(sourceSha256=NORMAL,sha256=sha(new),length=len(new),writes=writes,append=b64(new[len(normal):]))
 rebuilt=bytearray(normal)
 for w in writes:
  at=w['offset'];before=base64.b64decode(w['before']);after=base64.b64decode(w['data']);assert rebuilt[at:at+len(before)]==before;rebuilt[at:at+len(after)]=after
 rebuilt.extend(base64.b64decode(recipe['engine']['append']));assert rebuilt==new
 data_source=GAME/'RemasteredCE/data/data.sim8';assert digest(data_source)==DATA
 header,entries=index(data_source);pack=WORK/'religion_swap.pack';assert digest(pack)==PACK
 _,mods=index(pack);assert len(mods)==4 and not (entries.keys()&mods.keys())
 flags=struct.unpack_from('<I',header,4)[0];assert flags&32 and struct.unpack_from('<I',header,12)[0]==0
 library=ROOT/'work/sim-turns-integration/lz4.dll';assert digest(library)==digest(ROOT/'source/current-launcher/lz4')
 lz=ctypes.CDLL(str(library));lz.LZ4_compressBound.argtypes=[ctypes.c_int];lz.LZ4_compress_default.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_int]
 lz.LZ4_decompress_safe.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_int]
 assets={}
 with pack.open('rb') as f:
  for name,entry in mods.items():
   assert not entry['compressed'];f.seek(entry['offset']);raw=f.read(entry['length']);target=ctypes.create_string_buffer(lz.LZ4_compressBound(len(raw)));n=lz.LZ4_compress_default(raw,target,len(raw),len(target));assert n>0
   encoded=target.raw[:n];decoded=ctypes.create_string_buffer(len(raw));assert lz.LZ4_decompress_safe(encoded,decoded,n,len(raw))==len(raw) and decoded.raw==raw
   assets[name]=(raw,encoded)
 old_prefix=base64.b64decode(recipe['data']['prefix']);old_tail=base64.b64decode(recipe['data']['tail']);record_prefix=16+(8 if flags&64 else 0)
 index_size=sum(len(e['record']) for e in entries.values())+sum(record_prefix+len(n.encode())+1 for n in mods)
 payload=(32+index_size+63)&~63;shift=payload-len(old_prefix);assert shift>=0
 new_index=bytearray()
 for entry in entries.values():
  record=bytearray(entry['record']);struct.pack_into('<Q',record,0,entry['offset']+shift);new_index.extend(record)
 end=data_source.stat().st_size+shift;tail=bytearray(old_tail);asset_rows=[]
 for name,(raw,encoded) in assets.items():
  record=bytearray(record_prefix)+name.replace('/','\\').encode()+b'\0';struct.pack_into('<QII',record,0,end,len(raw),len(encoded));new_index.extend(record)
  asset_rows.append(dict(path=name,offset=end,length=len(raw),stored=len(encoded),sha256=sha(raw)));tail.extend(encoded);end+=len(encoded)
 assert len(new_index)==index_size
 new_header=bytearray(header);struct.pack_into('<II',new_header,16,len(entries)+len(mods),index_size)
 prefix=new_header+new_index+bytes(payload-32-index_size)
 base=GAME/'RemasteredCE/data/data.pack';assert digest(base)==recipe['data']['sourceSha256']
 old_hash=hashlib.sha256(old_prefix);new_hash=hashlib.sha256(prefix);body_length=0
 with base.open('rb') as stream:
  stream.seek(recipe['data']['sourcePayloadOffset'])
  while block:=stream.read(8*1024*1024):old_hash.update(block);new_hash.update(block);body_length+=len(block)
 old_hash.update(old_tail);assert old_hash.hexdigest()==DATA
 new_hash.update(tail);assert len(prefix)+body_length+len(tail)==end
 recipe['data'].update(sha256=new_hash.hexdigest(),length=end,prefix=b64(prefix),tail=b64(tail))
 recipe['record'].update(engineSha256=sha(new),dataSha256=new_hash.hexdigest(),build='sim8-religion-swap-v5-local-r1',gameplayTested=False)
 recipe['religionSwap']=dict(sourcePackSha256=PACK,sourceScriptSha256=json.loads((WORK/'religion-patches.json').read_text())['scriptSha256'],aiThresholdPercent=75,campaigns=['Sengoku','Rise of the Samurai','Fall of the Samurai'],privateIntegration=True)
 (WORK/'sim-turns-recipe.json').write_text(json.dumps(recipe,separators=(',',':')),encoding='utf-8')
 report=dict(status='BUILT_NOT_INSTALLED',engineSha256=sha(new),dataSha256=new_hash.hexdigest(),guards=guard_rows,assets=asset_rows,oldModeEntriesPreserved=len(entries),unchangedExistingPayload=True,normalEngineSha256=NORMAL,normalEngineUnchanged=True,engineLengthUnchanged=True,onlySevenReligionRangesAndChecksumChanged=True,signedInstallerReconstructionPending=True,gameplayTested=False,compiledEngine=False)
 (WORK/'build.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))

if __name__=='__main__':build()
