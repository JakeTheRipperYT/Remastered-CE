from pathlib import Path
import json,hashlib,shutil
W=Path(__file__).resolve().parent;R=W.parent.parent
cfg=json.loads((R/'source/current-installer.json').read_text());assert cfg['version']=='0.1.67-preview'
for name in ['cleanup-validation.json','engine-delta-validation.json','stream-validation.json','unwind-validation.json']:
 assert json.loads((W/name).read_text())['status']=='PASS'
m=json.loads((W/'candidate-manifest.json').read_text())
notes='0.1.68-preview: remove the superseded 0.1.65 particle batching helper. Clear its 324-byte region, remove its native-call relocation and four obsolete unwind entries. The current 0.1.66 stream renderer and 0.1.67 dynamic-resolution correction remain byte-identical; all nine archive recipes remain unchanged. Pointer/reference checks, 43 native stream scenarios and 6,669 Windows unwind checks pass. This is dead-code cleanup, with no intended gameplay, visual or performance change. Section padding remains allocated, so this does not imply a 324-byte smaller DLL. The user-confirmed battle-performance improvement from 0.1.67 is retained; residual paused downward-camera dips remain unresolved. No smoke-density or wind changes are included.'
update=json.loads(Path(cfg['engineUpdate']).read_text());update.update(afterFinalSha256=m['engineFinalSha256'],description=notes)
(W/'engine-update.json').write_text(json.dumps(update,indent=2))
docs=W/'docs';shutil.copytree(cfg['documentation'],docs,dirs_exist_ok=True)
for name in ['README.txt','CHANGELOG.md']:
 f=docs/name;f.write_text(notes+'\n\n'+f.read_text(encoding='utf-8-sig'),encoding='utf-8')
cfg.update(version='0.1.68-preview',minimumInstallerVersion='0.1.68-preview',documentation=str(docs),releaseNotes=notes,engineUpdate=str(W/'engine-update.json'))
cfg['helperUpdate'].update(file=str(W/'candidate-helper.json'),sha256=hashlib.sha256((W/'candidate-helper.json').read_bytes()).hexdigest())
(W/'candidate-installer.json').write_text(json.dumps(cfg,indent=2))
for name in ['Build-Candidate.ps1','Verify-Package.ps1']:
 s=(R/'work/particle-dynres-controller'/name).read_text().replace('particle-dynres-controller','particle-helper-cleanup').replace('release-067','release-068')
 (W/name).write_text(s)
s=(R/'work/particle-dynres-controller/preflight_deploy.py').read_text().replace('release-067','release-068').replace('release-066','release-067').replace("['native-validation.json','engine-delta-validation.json']","['cleanup-validation.json','engine-delta-validation.json','stream-validation.json','unwind-validation.json']")
(W/'preflight_deploy.py').write_text(s)
print('Prepared private 0.1.68 cleanup package.')
