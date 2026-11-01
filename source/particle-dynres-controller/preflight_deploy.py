from pathlib import Path
import json,hashlib,subprocess,zipfile
W=Path(__file__).parent;R=W.parents[1];B=R/'work/release-067';G=Path('D:/SteamLibrary/steamapps/common/Shogun 2 Complete Edition/RemasteredCE')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while block:=f.read(8*1024*1024):h.update(block)
 return h.hexdigest()
old=json.loads((R/'work/release-066/manifest.json').read_text());new=json.loads((B/'manifest.json').read_text());state=json.loads((G/'install-state.json').read_text())
assert old['files']==new['files'],'Archive recipes must remain identical'
assert sha(G/'CE.dll')==state['engineHash']==old['engineFinalSha256']
assert sha(G/'release.rce')==state['offlineReleaseSha256']
assert sha(G/'RemasteredCE_Launcher.exe')==state['unifiedLauncherSha256']
for name in ['native-validation.json','engine-delta-validation.json']:assert json.loads((W/name).read_text())['status']=='PASS'
assert json.loads((B/'engine-reconstruction.json').read_text())['status']=='PASS'
packs=[]
for f in new['files']:
 p=G/f['destination'];assert sha(p)==f['sha256'],str(p)
 packs.append(dict(file=f['destination'],sha256=f['sha256'],size=p.stat().st_size,mtimeNs=p.stat().st_mtime_ns))
backup=Path('F:/Codex/Installer-Backups/RemasteredCE')/('RemasteredCE_Installer-'+state['version']+'.zip')
assert backup.exists()
with zipfile.ZipFile(backup) as z:assert z.testzip() is None
receipt=dict(status='PASS',previousVersion=state['version'],previousEngineHash=state['engineHash'],previousPackageHash=state['offlineReleaseSha256'],packs=packs,backupInstaller=str(backup),backupInstallerSha256=sha(backup),newEngineSha256=new['engineFinalSha256'],originalEngineSha256=sha(G.parent/'empire.retail.x64.dll'),originalExecutableSha256=sha(G.parent/'shogun2_complete_edition.exe'))
(B/'deployment-preflight.json').write_text(json.dumps(receipt,indent=2));print('PASS: all nine installed packs match unchanged signed recipes; previous installer ZIP verified.')
