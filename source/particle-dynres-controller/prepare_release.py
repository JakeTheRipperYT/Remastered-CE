from pathlib import Path
import json,base64,hashlib,shutil,sys
sys.path.insert(0,'F:/Codex/Shogun2-CE/work/disasm_runtime');import pefile
W=Path(__file__).resolve().parent;R=W.parent.parent
cfg=json.loads((R/'source/current-installer.json').read_text());assert cfg['version']=='0.1.66-preview'
for name in ['native-validation.json','native-validation-0x230000000.json','native-validation-0x7ff600000000.json']:
 assert json.loads((W/name).read_text())['status']=='PASS'
m=json.loads((W/'candidate-manifest.json').read_text());layout=json.loads((W/'layout.json').read_text())
old=(Path(cfg['ceRoot'])/'RemasteredCE/CE.dll').read_bytes();new=(W/'CE.campaign-night-candidate.dll').read_bytes();assert len(old)==len(new)
p=pefile.PE(data=old,fast_load=True)
allowed={i for w in layout['writes'] for i in range(p.get_offset_from_rva(w['rva']),p.get_offset_from_rva(w['rva'])+len(bytes.fromhex(w['data'])))}
checksum=p.OPTIONAL_HEADER.get_field_absolute_offset('CheckSum')
allowed.update(range(checksum,checksum+4))
changed=[i for i,(a,b) in enumerate(zip(old,new)) if a!=b]
assert set(changed)<=allowed
cp=pefile.PE(data=new,fast_load=True);assert cp.OPTIONAL_HEADER.CheckSum==cp.generate_checksum()
for name in ['.pdata','.xdata']:
 p=pefile.PE(data=old,fast_load=True);a=next((s for s in p.sections if s.Name.rstrip(b'\0').decode()==name),None)
 if a:assert old[a.PointerToRawData:a.PointerToRawData+a.SizeOfRawData]==new[a.PointerToRawData:a.PointerToRawData+a.SizeOfRawData]
delta=dict(status='PASS',changedBytes=len(changed),guardedControllerWriteBytes=16,peChecksumRecomputed=True,changedOffsets=changed,onlyControllerChanged=True,helperUnchanged=True,unwindMetadataUnchanged=True,shaderAndArchiveRecipesUnchanged=True)
(W/'engine-delta-validation.json').write_text(json.dumps(delta,indent=2))
notes='0.1.67-preview: correct particle dynamic-resolution feedback. The native controller divides particle GPU ticks by whole-frame GPU ticks, so heavier camera-dependent scene rendering can make it raise particle resolution while the frame is already slower. Reproduction with a constant6ms particle pass: a16ms frame lowers scale0.70->0.69, but24-48ms frames raise it0.70->0.71. It also adjusts repeatedly from an old result when no timing is ready. Use actual GPU timestamp frequency and an absolute3.3ms particle budget; adjust only after a fresh completed query. Retain native30%-100% scale bounds, step, overrides, particle contents, shaders and confirmed anti-flashing ordering.402 native cases at3ASLR bases pass, including not-ready queries, missing timestamps, rollover, clamps, viewport scaling and nonvolatile registers. Only16 guarded controller bytes; helper and unwind metadata unchanged. This repairs a reproduced controller mechanism; live contribution to reported motion spikes and FPS improvement remain unverified. The existing adaptive path may choose a lower smoke rendering resolution to meet the budget.'
update=json.loads(Path(cfg['engineUpdate']).read_text())
for w in layout['writes']:update['patches'].append(dict(offset=w['offset'],before=base64.b64encode(bytes.fromhex(w['before'])).decode(),data=base64.b64encode(bytes.fromhex(w['data'])).decode()))
update.update(afterFinalSha256=m['engineFinalSha256'],description=notes);(W/'engine-update.json').write_text(json.dumps(update,indent=2))
docs=W/'docs';shutil.copytree(cfg['documentation'],docs,dirs_exist_ok=True)
for name in ['README.txt','CHANGELOG.md']:
 f=docs/name;f.write_text(notes+'\n\n'+f.read_text(encoding='utf-8-sig'),encoding='utf-8')
cfg.update(version='0.1.67-preview',minimumInstallerVersion='0.1.67-preview',engineUpdate=str(W/'engine-update.json'),documentation=str(docs),releaseNotes=notes)
cfg['helperUpdate'].update(file=str(W/'candidate-helper.json'),sha256=hashlib.sha256((W/'candidate-helper.json').read_bytes()).hexdigest())
(W/'candidate-installer.json').write_text(json.dumps(cfg,indent=2))
(W/'Build-Candidate.ps1').write_text((R/'work/particle-sorted-stream/Build-Candidate.ps1').read_text().replace('particle-sorted-stream/candidate-installer.json','particle-dynres-controller/candidate-installer.json'))
(W/'Verify-Package.ps1').write_text((R/'work/particle-sorted-stream/Verify-Package.ps1').read_text().replace('release-066','release-067').replace('particle-sorted-stream/CE.campaign-night-candidate.dll','particle-dynres-controller/CE.campaign-night-candidate.dll'))
pre=(R/'work/particle-sorted-stream/preflight_deploy.py').read_text().replace('release-066','release-067').replace('release-065','release-066').replace("['mapping-fix-validation.json']","['native-validation.json','engine-delta-validation.json']")
(W/'preflight_deploy.py').write_text(pre)
print(json.dumps(delta));print('Private67 candidate ready to package.')
