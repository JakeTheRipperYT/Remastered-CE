from pathlib import Path
import json,hashlib,ctypes,msvcrt,os,subprocess,datetime,shutil,zipfile
W=Path(__file__).parent;R=W.parents[1];B=R/'work/release-071';G=Path(r'D:/SteamLibrary/steamapps/common/Shogun 2 Complete Edition/RemasteredCE')
sha=lambda b:hashlib.sha256(b).hexdigest()
for f in [W/'shader-validation.json',W/'asset-scope-validation.json',B/'reconstruction.json']:assert json.loads(f.read_text())['status']=='PASS'
process=subprocess.run(['powershell.exe','-NoProfile','-Command',"Get-Process -Name shogun2_complete_edition,RemasteredCE_Bootstrap,Launch_Remastered_CE,RemasteredCE_Launcher -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id"],capture_output=True,text=True);assert not process.stdout.strip(),'Close the game/launcher before installation.'
for filename in ['gpu-validation.json','gpu-validation-hardware.json']:
 assert json.loads((W/filename).read_text())['status'].startswith('PASS_D3D11')
for filename in ['program-binding-validation.json','fade-native-validation.json']:
 assert json.loads((W/filename).read_text())['status']=='PASS'
old=json.loads((R/'work/release-070/manifest.json').read_text());new=json.loads((B/'manifest.json').read_text());build=json.loads((B/'build.json').read_text());state=json.loads((G/'install-state.json').read_text());assert state['version']=='0.1.70-preview'
assert old['enginePatches']==new['enginePatches'] and old['engineFinalSha256']==new['engineFinalSha256'];assert (R/'work/release-070/helper.json').read_bytes()==(B/'helper.json').read_bytes()
assert sha((G/'CE.dll').read_bytes())==new['engineFinalSha256'];assert not (G/'d3d11.dll').exists();assert sha((G/'release.rce').read_bytes())==state['offlineReleaseSha256'];assert sha((G/'RemasteredCE_Launcher.exe').read_bytes())==state['unifiedLauncherSha256']
a={f['destination']:f for f in old['files']};b={f['destination']:f for f in new['files']};changed=[n for n in a if a[n]!=b[n]];assert set(changed)=={'data/shaders.pack','data/rce_campaign_night_visuals.pack'}
prior=json.loads((R/'work/release-069/deployment-preflight.json').read_text());untouched=[]
for row in prior['packs']:
 if row['file'] in changed:continue
 p=G/row['file'];assert p.stat().st_size==row['size'] and p.stat().st_mtime_ns==row['mtimeNs'];untouched.append(row)
backup=Path('F:/Codex/Installer-Backups/RemasteredCE/RemasteredCE_Installer-0.1.70-preview.zip');assert backup.exists()
with zipfile.ZipFile(backup) as z:assert z.testzip() is None
files=[]
for name in changed:
 assert sha((G/name).read_bytes())==a[name]['sha256'];data=(B/'acceptance'/name).read_bytes();assert sha(data)==b[name]['sha256'];files.append((G/name,data,b[name]['sha256']))
files += [(G/'RemasteredCE_Launcher.exe',Path(build['launcher']).read_bytes(),build['launcherSha256']),(G/'release.rce',Path(build['package']).read_bytes(),build['packageSha256'])]
state.update(version='0.1.71-preview',packageSha256=build['packageSha256'],offlineReleaseSha256=build['packageSha256'],unifiedLauncherSha256=build['launcherSha256'],installedUtc=datetime.datetime.now(datetime.timezone.utc).isoformat())
for row in state['files']:row['sha256']=b[row['file']]['sha256']
data=json.dumps(state,separators=(',',':')).encode();files.append((G/'install-state.json',data,sha(data)))
k=ctypes.WinDLL('kernel32',use_last_error=True);k.CreateFileW.argtypes=[ctypes.c_wchar_p,ctypes.c_uint,ctypes.c_uint,ctypes.c_void_p,ctypes.c_uint,ctypes.c_uint,ctypes.c_void_p];k.CreateFileW.restype=ctypes.c_void_p
opened=[];before=[];engine_lock=None;changed_live=False
try:
 h=k.CreateFileW(str(G/'CE.dll'),0x80000000,0,None,3,128,None)
 if h==ctypes.c_void_p(-1).value:raise OSError(ctypes.get_last_error(),'Cannot lock engine')
 engine_lock=os.fdopen(msvcrt.open_osfhandle(h,os.O_BINARY|os.O_RDONLY),'rb')
 for path,data,digest in files:
  assert sha(data)==digest
  h=k.CreateFileW(str(path),0xc0000000,0,None,3,128,None)
  if h==ctypes.c_void_p(-1).value:raise OSError(ctypes.get_last_error(),'Cannot exclusively lock '+str(path))
  f=os.fdopen(msvcrt.open_osfhandle(h,os.O_BINARY|os.O_RDWR),'r+b');opened.append(f);before.append(f.read())
 changed_live=True
 for f,(_,data,digest) in zip(opened,files):f.seek(0);f.write(data);f.truncate();f.flush();os.fsync(f.fileno());f.seek(0);assert sha(f.read())==digest
except BaseException:
 if changed_live:
  for f,data in zip(opened,before):f.seek(0);f.write(data);f.truncate();f.flush();os.fsync(f.fileno())
 raise
finally:
 for f in opened:f.close()
 if engine_lock:engine_lock.close()
for path,data,digest in files:assert sha(path.read_bytes())==digest
assert sha((G/'CE.dll').read_bytes())==new['engineFinalSha256']
for row in untouched:
 p=G/row['file'];assert p.stat().st_size==row['size'] and p.stat().st_mtime_ns==row['mtimeNs']
assert sha((G.parent/'empire.retail.x64.dll').read_bytes())==prior['originalEngineSha256'];assert sha((G.parent/'shogun2_complete_edition.exe').read_bytes())==prior['originalExecutableSha256']
shutil.copyfile(W/'candidate-installer.json',R/'source/current-installer.json')
notes=json.loads((W/'candidate-installer.json').read_text())['releaseNotes']
resume='Private 0.1.70 grass matte trial installed. '+notes+' Engine SHA '+new['engineFinalSha256']+'. User visual test pending. .69 s2fix remains withdrawn due weather regression; no proxy installed. Multiplayer pursuit remains paused and separate. No public push. Evidence: work/grass-opening-wetness and work/release-071.\n'
for p in [R/'ACTIVE.txt',R/'NEW_CHAT_RESUME.txt',R/'source/CURRENT-BUILD.txt']:p.write_text(resume)
backup=Path('F:/Codex/Installer-Backups/RemasteredCE/RemasteredCE_Installer-0.1.71-preview.zip');source=R/'outputs/release-0.1.70/RemasteredCE_Installer_Preview.zip'
if backup.exists():assert sha(backup.read_bytes())==sha(source.read_bytes())
else:shutil.copyfile(source,backup)
receipt=dict(status='INSTALLED_VERIFIED_GRASS_OPENING_WETNESS_FIX',version='0.1.71-preview',previousVersion='0.1.70-preview',engineSha256=new['engineFinalSha256'],packageSha256=build['packageSha256'],launcherSha256=build['launcherSha256'],changedPacks=changed,unchangedSevenPacks=True,allOtherAssetContentsUnchanged=True,weatherEngineAndHelperUnchanged=True,particleAndSelectionFixesRetained=True,baseRoughnessFloor=.9,grassMetalness=0,openingGroundWetnessPreserved=True,compiledVariants=6,inGameAppearanceVerified=False,gameLaunched=False,published=False)
(B/'installation.json').write_text(json.dumps(receipt,indent=2));build.update(status=receipt['status'],installed=True,published=False);(B/'build.json').write_text(json.dumps(build,indent=2))
repo=Path('F:/Codex/Release/Remastered-CE/source/grass-opening-wetness');repo.mkdir(parents=True,exist_ok=True)
for name in ['prepare_source.py','prepare_validation.py','build_shaders.py','prepare_release.py','deploy_fix.py','GrassFixture.cs','Verify-Package.ps1','shader-validation.json','asset-scope-validation.json','test_gpu.py','gpu-validation.json','gpu-validation-hardware.json','program-binding-validation.json','fade-native-validation.json']:shutil.copyfile(W/name,repo/name)
shutil.copytree(W/'replacements',repo/'replacements',dirs_exist_ok=True);(repo/'README.txt').write_text(notes+'\n')
print('Installed .71 grass opening-wetness correction; matte base retained. Native campaign transitions and real shader tests pass; live retest pending.')
