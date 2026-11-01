"""Compile a PIC native controller against private32. No installation or publishing."""
from pathlib import Path
import sys,os,subprocess,json,base64,struct,hashlib,shutil
sys.dont_write_bytecode=True
import pefile,capstone
import argparse,io,zipfile
SRC=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description='Build the campaign/night/weather helper against the pinned public0.1.28 baseline; never installs or signs.')
parser.add_argument('--ce-root',type=Path,required=True)
parser.add_argument('--baseline-package',type=Path,required=True)
parser.add_argument('--work-directory',type=Path,required=True)
args=parser.parse_args()
W=args.work_directory.resolve();W.mkdir(parents=True,exist_ok=True)
assert W!=SRC and SRC not in W.parents,'Use a separate build directory'
for source in SRC.iterdir():
 if source.suffix in ('.cpp','.inc','.h'):shutil.copyfile(source,W/source.name)
rawPackage=args.baseline_package.read_bytes()
assert hashlib.sha256(rawPackage).hexdigest()=='da44d366cc3e0f96d1ff6c12b5a0c21abb48b6152eaf01ccddc4b2dd005ad752','Public28 input hash mismatch'
archive=zipfile.ZipFile(io.BytesIO(rawPackage[12+struct.unpack_from('<I',rawPackage,8)[0]:]))
baseManifest=json.loads(archive.read('manifest.json'));(W/'base-helper.json').write_bytes(archive.read('helper.json'))
meta=json.loads((SRC/'native-build-inputs.json').read_text())
baseManifest['enginePatches'].append(meta['seasonPatch'])
baseManifest['engineEditedSha256']=meta['engineEditedSha25632']
baseManifest['engineFinalSha256']=meta['engineFinalSha25632']
(W/'base-manifest.json').write_text(json.dumps(baseManifest))

def digest(data):return hashlib.sha256(data).hexdigest()
def main():
 manifest=json.loads((W/'base-manifest.json').read_text());helper=json.loads((W/'base-helper.json').read_text())
 raw=bytearray((args.ce_root/'empire.retail.x64.dll').read_bytes());assert digest(raw)==manifest['engineSourceSha256']
 for op in manifest['enginePatches']:
  data=base64.b64decode(op['data']);raw[op['offset']:op['offset']+len(data)]=data
 assert digest(raw)==manifest['engineEditedSha256'];p=pefile.PE(data=raw)
 prefix=base64.b64decode(helper['payload']);start=(len(prefix)+4095)&~4095
 hooks=[('UnitCardFrame',0x15a8f90,9,'DynamicUnitCardFrame'),('UnitCardStats',0x15ea6c0,7,'DynamicUnitCardStats'),('Load',0x1b8bce0,7,'NightMapLoad'),('Select',0x1b94e70,5,'NightMapSelect'),('Frame',0x1b736b0,5,'NightMapFrame'),('CheckboxInit',0x1486010,5,'NightCheckboxInit'),('BattleClimate',0x56a560,5,'NightBattleClimate'),('ForecastUI',0x16407b0,5,'DynamicForecastUI'),('BattleTick',0x421ed0,11,'DynamicBattleTick'),('WeatherFrame',0x1ba06b0,5,'DynamicWeatherFrame'),('WeatherParticleCount',0x1b84cf0,7,'DynamicWeatherParticleCount'),('WeatherParameters',0x1a31e10,5,'DynamicWeatherParameters'),('ParticleMaterial',0x1b96970,5,'DynamicParticleMaterial'),('SkyDestroy',0x1b65c40,5,'DynamicSkyDestroy'),('WeatherProgram',0x1aeb850,5,'DynamicWeatherProgram'),('SkyMaterial',0x1b96e50,5,'DynamicSkyMaterial')]
 for name,site,size,_ in hooks:
  before=p.get_data(site,size);assert sum(i.size for i in capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64).disasm(before,site))==size
 parent=meta['parentNightSetRva']
 (W/'controller_layout.h').write_text(f'#define PARENT_NIGHT_SET 0x{parent:x}ull\n#define IAT_REG_QUERY 0x215a010ull\n#define IAT_REG_SET 0x215a020ull\n')
 assembly=['option casemap:none','.code','PUBLIC engine_base','engine_base PROC','lea rax,engine_base','mov r11d,12345678h','movsxd r11,r11d','add rax,r11','ret','engine_base ENDP']
 resumes={}
 for name,site,size,_ in hooks:
  if name in ('UnitCardFrame','UnitCardStats'):
   regs=['rbp','r14'] if name=='UnitCardFrame' else ['rbp','rsi','r14']
   assembly += [f'PUBLIC Original{name}',f'Original{name} PROC FRAME']
   if name=='UnitCardStats':assembly += ['mov rax,rsp']
   for reg in regs:assembly += ['push '+reg,'.pushreg '+reg]
   if name=='UnitCardFrame':assembly += ['lea rbp,[rsp-4fh]']
   assembly += ['.endprolog','xor r11d,r11d',f'jz NEAR PTR Resume{name}',f'Original{name} ENDP']
  elif name in ('BattleTick','WeatherFrame'):
   regs=['rbp','rbx'] if name=='BattleTick' else ['rbx','rsi']
   assembly += [f'PUBLIC Original{name}',f'Original{name} PROC FRAME']
   if name=='WeatherFrame':assembly += ['mov rax,rsp']
   for reg in regs:assembly += ['push '+reg,'.pushreg '+reg]
   if name=='BattleTick':assembly += ['lea rbp,[rsp-4fb8h]']
   assembly += ['.endprolog','xor r11d,r11d',f'jz NEAR PTR Resume{name}',f'Original{name} ENDP']
  elif name=='Frame':
   # A direct tail JMP after native pushes is misidentified as an epilog by
   # RtlVirtualUnwind. A guaranteed conditional transfer keeps frame metadata active.
   assembly+=['PUBLIC OriginalFrame','OriginalFrame PROC FRAME','push rbp','.pushreg rbp','push rsi','.pushreg rsi','push r13','.pushreg r13','.endprolog','xor r11d,r11d','jz NEAR PTR ResumeFrame','OriginalFrame ENDP']
  else:
   assembly += [f'PUBLIC Original{name}',f'Original{name} PROC','db '+','.join('0%02xh'%b for b in p.get_data(site,size)),f'jmp NEAR PTR Resume{name}',f'Original{name} ENDP']
  resumes['Resume'+name]=site+size
 for name in resumes:assembly += [f'PUBLIC {name}',f'{name} PROC','ret',f'{name} ENDP']
 assembly+=['END'];(W/'controller.asm').write_text('\n'.join(assembly)+'\n')
 exports=['DynamicUnitCardFrame','OriginalUnitCardFrame','DynamicUnitCardStats','OriginalUnitCardStats','DynamicSkyMaterial','OriginalSkyMaterial','DynamicWeatherProgram','OriginalWeatherProgram','DynamicAmbientFrame','DynamicWeatherParameters','OriginalWeatherParameters','DynamicParticleMaterial','OriginalParticleMaterial','DynamicSkyDestroy','OriginalSkyDestroy','DynamicWeatherParticleCount','OriginalWeatherParticleCount','DynamicForecastUI','DynamicBattleTick','DynamicWeatherFrame','OriginalForecastUI','OriginalBattleTick','OriginalWeatherFrame','engine_base','NightMapLoad','NightMapSelect','NightMapFrame','NightMapBattleSet','NightCheckboxInit','NightCheckboxCommit','NightBattleClimate','OriginalBattleClimate','OriginalCheckboxInit','OriginalLoad','OriginalSelect','OriginalFrame']+list(resumes)
 (W/'controller.def').write_text('EXPORTS\n'+'\n'.join(exports)+'\n')
 vs=Path(r'C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC')
 vc=sorted(vs.iterdir(),key=lambda x:tuple(map(int,x.name.split('.'))))[-1]/'bin/Hostx64/x64'
 env=os.environ.copy();(W/'Temp').mkdir(exist_ok=True);env['TEMP']=env['TMP']=str(W/'Temp')
 def run(args):subprocess.run([str(x) for x in args],cwd=W,env=env,check=True)
 run([vc/'cl.exe','/nologo','/c','/O1','/GS-','/Gs16384','/GR-','/EHs-c-','/Zl','/Oi-',f'/Fo{W/"controller.obj"}',W/'night_controller.cpp'])
 run([vc/'ml64.exe','/nologo','/c',f'/Fo{W/"adapters.obj"}',W/'controller.asm'])
 run([vc/'link.exe','/nologo','/dll','/noentry','/nodefaultlib','/machine:x64','/base:0x180000000',f'/out:{W/"controller.dll"}',f'/def:{W/"controller.def"}',W/'controller.obj',W/'adapters.obj'])
 q=pefile.PE(str(W/'controller.dll'));assert not getattr(q,'DIRECTORY_ENTRY_IMPORT',[])
 assert not [e for bl in getattr(q,'DIRECTORY_ENTRY_BASERELOC',[]) for e in bl.entries if e.type]
 text=next(s for s in q.sections if s.Name.rstrip(b'\0')==b'.text');origin=text.VirtualAddress
 mapped=bytearray(q.get_memory_mapped_image()[origin:q.OPTIONAL_HEADER.SizeOfImage]);mapped.extend(b'\0'*(q.OPTIONAL_HEADER.SizeOfImage-origin-len(mapped)))
 exports={e.name.decode():e.address for e in q.DIRECTORY_ENTRY_EXPORT.symbols}
 destinations={name:helper['rva']+start+rva-origin for name,rva in exports.items()}
 md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);md.detail=True
 for ins in md.disasm(mapped[:text.Misc_VirtualSize],origin):
  if (ins.mnemonic=='call' or ins.mnemonic.startswith('j')) and ins.operands[0].type==capstone.x86.X86_OP_IMM:
   names=[n for n in resumes if exports[n]==ins.operands[0].imm]
   if names:
    assert ins.imm_size==4;off=ins.address-origin+ins.imm_offset
    struct.pack_into('<i',mapped,off,resumes[names[0]]-(helper['rva']+start+ins.address-origin+ins.size));helper['fixups'].append(start+off)
 marker=bytes.fromhex('41bb78563412');assert mapped.count(marker)==1
 off=mapped.index(marker)+2;struct.pack_into('<i',mapped,off,-destinations['engine_base']);helper['fixups'].append(start+off)
 # MSVC type13 debug records embed link time inside .rdata. Replay only this
 # audited metadata timestamp to reproduce the accepted release byte-for-byte.
 debug=next(e.struct for e in q.DIRECTORY_ENTRY_DEBUG if e.struct.Type==13)
 stampRva=q.get_rva_from_offset(debug.get_file_offset())+4
 assert start+stampRva-origin==meta['linkerDebugTimestampPayloadOffset']
 struct.pack_into('<I',mapped,stampRva-origin,meta['acceptedLinkerDebugTimestamp'])
 helper['payload']=base64.b64encode(prefix+b'\0'*(start-len(prefix))+mapped).decode()
 writable=min(s.VirtualAddress for s in q.sections if s.Characteristics&0x80000000)
 helper['writableDataOffset']=start+writable-origin
 assert helper['writableDataOffset']%4096==0
 new_unwind=[]
 for e in q.DIRECTORY_ENTRY_EXCEPTION:
  row=[helper['rva']+start+value-origin for value in [e.struct.BeginAddress,e.struct.EndAddress,e.struct.UnwindData]]
  helper['unwind'].append(row);new_unwind.append(row)
 helper['unwind'].sort(key=lambda row:row[0]);assert all(a[1]<=b[0] for a,b in zip(helper['unwind'],helper['unwind'][1:]))
 writes=[]
 for name,site,size,target in hooks+[('AmbientCall',0x1ba0bd1,5,'DynamicAmbientFrame'),('BattleSet',0x78ea20,5,'NightMapBattleSet'),('CheckboxCommitOff',0x15a4aab,5,'NightCheckboxCommit'),('CheckboxCommitOn',0x15a4ac9,5,'NightCheckboxCommit')]:
  at=p.get_offset_from_rva(site);before=bytes(raw[at:at+size]);data=(b'\xe8' if (name.startswith('CheckboxCommit') or name=='AmbientCall') else b'\xe9')+struct.pack('<i',destinations[target]-site-5)+b'\x90'*(size-5)
  raw[at:at+size]=data;manifest['enginePatches'].append(dict(offset=at,data=base64.b64encode(data).decode()));writes.append(dict(rva=site,offset=at,before=before.hex(),data=data.hex(),target=destinations[target],kind=name))
 manifest['engineEditedSha256']=digest(raw)
 (W/'candidate-engine-edited.bin').write_bytes(raw)
 (W/'candidate-helper.json').write_text(json.dumps(helper,separators=(',',':')))
 assert digest((W/'candidate-helper.json').read_bytes())==meta['expectedHelperSha256'],'Rebuilt native helper differs from the accepted release'
 (W/'candidate-manifest.json').write_text(json.dumps(manifest,separators=(',',':')))
 result=dict(status='COMPILED_NOT_INSTALLED',sourceVersion='0.1.32-preview',helperPrefixBytes=len(prefix),moduleStartRva=helper['rva']+start,exports=destinations,writes=writes,unwind=new_unwind,writableDataOffset=helper['writableDataOffset'])
 (W/'controller-layout.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ['exports','writes','unwind']},indent=2))
if __name__=='__main__':main()
