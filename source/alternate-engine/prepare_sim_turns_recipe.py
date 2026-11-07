"""Package guarded engine/data recipes, never a full replacement game DLL."""
from pathlib import Path
import base64,hashlib,json
from trace_sim_turns import ROOT,WORK,GAME

def prepare():
 e=json.loads((WORK/'engine-integration.json').read_text());d=json.loads((WORK/'data-integration.json').read_text());v=json.loads((WORK/'engine-verification.json').read_text())
 assert v['normalEngineFixBytesPreserved'] and d['sourcePayloadByteIdentical']
 old=(GAME/'RemasteredCE/CE.dll').read_bytes();new=(WORK/'CE8.candidate.dll').read_bytes();writes=[];i=0
 while i<len(old):
  if old[i]==new[i]:i+=1;continue
  start=i;last=i+1;gap=0
  while i<len(old) and gap<=16:
   if old[i]!=new[i]:last=i+1;gap=0
   else:gap+=1
   i+=1
  writes.append(dict(offset=start,before=base64.b64encode(old[start:last]).decode(),data=base64.b64encode(new[start:last]).decode()))
  i=last
 data_path=WORK/'data.sim8'
 with data_path.open('rb') as f:
  prefix=f.read(d['outputPayloadOffset']);f.seek((GAME/'RemasteredCE/data/data.pack').stat().st_size+d['outputPayloadOffset']-d['sourcePayloadOffset']);tail=f.read()
 bootstrap=bytearray((GAME/'RemasteredCE/shogun2_complete_edition.exe').read_bytes())
 assert bootstrap[58872:58879]==b'CE.dll\0'
 bootstrap[58872:58893]=bytes(21);bootstrap[58872:58880]=b'CE8.dll\0'
 (WORK/'RemasteredCE_Sim8.exe').write_bytes(bootstrap)
 record=dict(schema=1,normalEngineSha256=e['normalEngineSha256'],engineSha256=e['candidateSha256'],
  bootstrapSha256=hashlib.sha256(bootstrap).hexdigest(),dataSha256=d['sha256'],
  upstreamEngineSha256=e['suppliedSha256'],upstreamLobbySha256='77e135031ed9097a78e6a7c1c2e04d5dcacee73226d59766ea2529029434e0b7',
  build='sim8-integrated-local-r1',gameplayTested=False)
 recipe=dict(schema=1,record=record,engine=dict(sourceSha256=e['normalEngineSha256'],sha256=e['candidateSha256'],length=len(new),writes=writes,
  append=base64.b64encode(new[len(old):]).decode()),data=dict(sourceSha256=d['sourceSha256'],sha256=d['sha256'],length=d['length'],
  prefix=base64.b64encode(prefix).decode(),sourcePayloadOffset=d['sourcePayloadOffset'],tail=base64.b64encode(tail).decode()),
  attribution=(Path(r'C:\Users\CT-MK2\Downloads\SimTurnsBeta8P 1.1\SimTurnsBeta8P 1.1\LICENSE_njn313.txt')).read_text())
 (WORK/'sim-turns-recipe.json').write_text(json.dumps(recipe,separators=(',',':')),encoding='utf-8')
 (WORK/'sim-turns-state.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
 print(json.dumps(dict(engineWrites=len(writes),recipeBytes=(WORK/'sim-turns-recipe.json').stat().st_size,bootstrapSha256=record['bootstrapSha256'],normalEngineUnchanged=True)))

if __name__=='__main__':prepare()
