"""Verified engine-only local upgrade; preserve all packs and user state."""
from pathlib import Path
import json,hashlib,subprocess,datetime,ctypes,msvcrt,os,shutil
W=Path(__file__).parent;R=W.parents[1];B=R/'work/release-068';G=Path('D:/SteamLibrary/steamapps/common/Shogun 2 Complete Edition/RemasteredCE')
sha=lambda b:hashlib.sha256(b).hexdigest()
processes=subprocess.run(['powershell.exe','-NoProfile','-Command',"Get-Process | Where-Object { $_.ProcessName -match 'shogun|empire|RemasteredCE' } | Select-Object -ExpandProperty Id"],capture_output=True,text=True,check=True)
assert not processes.stdout.strip(),'Game or launcher must be closed.'
pre=json.loads((B/'deployment-preflight.json').read_text());m=json.loads((B/'manifest.json').read_text());build=json.loads((B/'build.json').read_text())
for path in [W/'cleanup-validation.json',W/'stream-validation.json',W/'unwind-validation.json',W/'engine-delta-validation.json',B/'engine-reconstruction.json']:
 assert json.loads(path.read_text())['status']=='PASS'
assert json.loads((B/'engine-reconstruction.json').read_text())['nativeTestedEngineMatches']
for f in pre['packs']:
 p=G/f['file'];assert p.stat().st_size==f['size'] and p.stat().st_mtime_ns==f['mtimeNs']
state=json.loads((G/'install-state.json').read_text());assert state['engineHash']==pre['previousEngineHash']
assert sha((G/'CE.dll').read_bytes())==pre['previousEngineHash']
assert sha((G/'release.rce').read_bytes())==pre['previousPackageHash']
files=[(G/'CE.dll',(B/'CE.verified.dll').read_bytes(),m['engineFinalSha256']),
 (G/'RemasteredCE_Launcher.exe',Path(build['launcher']).read_bytes(),build['launcherSha256']),
 (G/'release.rce',Path(build['package']).read_bytes(),build['packageSha256'])]
state.update(version=build['version'],engineHash=m['engineFinalSha256'],packageSha256=build['packageSha256'],offlineReleaseSha256=build['packageSha256'],unifiedLauncherSha256=build['launcherSha256'],installedUtc=datetime.datetime.now(datetime.timezone.utc).isoformat())
state_bytes=json.dumps(state,separators=(',',':')).encode();files.append((G/'install-state.json',state_bytes,sha(state_bytes)))
for _,data,h in files:assert sha(data)==h
k=ctypes.WinDLL('kernel32',use_last_error=True);k.CreateFileW.argtypes=[ctypes.c_wchar_p,ctypes.c_uint,ctypes.c_uint,ctypes.c_void_p,ctypes.c_uint,ctypes.c_uint,ctypes.c_void_p];k.CreateFileW.restype=ctypes.c_void_p
opened=[];previous=[];changed=False
try:
 for path,data,h in files:
  handle=k.CreateFileW(str(path),0xc0000000,0,None,3,128,None)
  if handle==ctypes.c_void_p(-1).value:raise OSError(ctypes.get_last_error(),'Cannot exclusively lock '+str(path))
  f=os.fdopen(msvcrt.open_osfhandle(handle,os.O_BINARY|os.O_RDWR),'r+b');opened.append(f);previous.append(f.read())
 assert sha(previous[0])==pre['previousEngineHash'] and sha(previous[2])==pre['previousPackageHash']
 changed=True
 for f,(_,data,h) in zip(opened,files):
  f.seek(0);f.write(data);f.truncate();f.flush();os.fsync(f.fileno());f.seek(0);assert sha(f.read())==h
except BaseException:
 if changed:
  for f,old in zip(opened,previous):f.seek(0);f.write(old);f.truncate();f.flush();os.fsync(f.fileno())
 raise
finally:
 for f in opened:f.close()
for path,data,h in files:assert sha(path.read_bytes())==h
assert sha((G.parent/'empire.retail.x64.dll').read_bytes())==pre['originalEngineSha256']
assert sha((G.parent/'shogun2_complete_edition.exe').read_bytes())==pre['originalExecutableSha256']
for row in pre['packs']:
 p=G/row['file'];assert p.stat().st_size==row['size'] and p.stat().st_mtime_ns==row['mtimeNs']
shutil.copyfile(W/'candidate-installer.json',R/'source/current-installer.json')
notes=json.loads((W/'candidate-installer.json').read_text())['releaseNotes']
resume='Private 0.1.68 dead particle-helper cleanup installed. '+notes+'\nEvidence: work/particle-helper-cleanup. Source: F:/Codex/Release/Remastered-CE/source/particle-helper-cleanup. 0.1.67 user-confirmed battle improvement retained; paused downward-camera drop remains unresolved. Wind audit partial; no density cap implemented. No public release or update feed change.\n'
for path in [R/'source/CURRENT-BUILD.txt',R/'ACTIVE.txt',R/'NEW_CHAT_RESUME.txt']:path.write_text(resume)
backup=Path('F:/Codex/Installer-Backups/RemasteredCE/RemasteredCE_Installer-0.1.68-preview.zip');source=R/'outputs/release-0.1.68/RemasteredCE_Installer_Preview.zip'
if backup.exists():assert sha(backup.read_bytes())==sha(source.read_bytes())
else:shutil.copyfile(source,backup)
receipt=dict(status='INSTALLED_VERIFIED_DEAD_HELPER_CLEANUP',version=build['version'],previousVersion=pre['previousVersion'],engineSha256=m['engineFinalSha256'],packageSha256=build['packageSha256'],launcherSha256=build['launcherSha256'],allNineArchivesRetained=True,originalGameEngineAndExecutableUnchanged=True,gameLaunched=False,githubPublished=False,backupPolicy='Installer ZIPs on F only; prior installer verified; rollback bytes retained in memory during mutation.',files=[str(p) for p,_,_ in files],removedHelperBytes=324,removedUnwindRows=4,activeRenderingCodeUnchanged=True)
(B/'installation.json').write_text(json.dumps(receipt,indent=2));build.update(status=receipt['status'],installed=True,published=False);(B/'build.json').write_text(json.dumps(build,indent=2))
repo=Path('F:/Codex/Release/Remastered-CE/source/particle-helper-cleanup');repo.mkdir(parents=True,exist_ok=True)
for name in ['build_candidate.py','audit_candidate.py','prepare_release.py','deploy_fix.py','preflight_deploy.py','Build-Candidate.ps1','Emit-Candidate.ps1','Verify-Package.ps1','PePatchCandidate.cs','layout.json','cleanup-validation.json','engine-delta-validation.json','stream-validation.json','unwind-validation.json','test_stream.py','test_unwind.py']:
 shutil.copyfile(W/name,repo/name)
(repo/'README.md').write_text(notes+'\n')
print('Installed private 0.1.68: superseded helper and metadata removed; active rendering code unchanged.')
