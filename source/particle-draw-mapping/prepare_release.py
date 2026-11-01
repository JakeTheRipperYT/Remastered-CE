from pathlib import Path
import json,base64,hashlib,shutil
W=Path(__file__).resolve().parent;R=W.parent.parent
cfg=json.loads((R/'source/current-installer.json').read_text());assert cfg['version']=='0.1.61-preview'
assert json.loads((W/'mapping-fix-validation.json').read_text())['status']=='PASS'
m=json.loads((W/'candidate-manifest.json').read_text());layout=json.loads((W/'mapping-layout.json').read_text())
update=json.loads(Path(cfg['engineUpdate']).read_text())
for o in layout['writes']:
 update['patches'].append(dict(offset=o['offset'],before=base64.b64encode(bytes.fromhex(o['before'])).decode(),data=base64.b64encode(bytes.fromhex(o['data'])).decode()))
notes='0.1.62-preview: correct CE grouped particle emitter draw indices. Distance buckets and the independently sorted source list can interleave; the original running bucket cursor then checks one emitter and uploads another. Resolve the checked emitter identity before each of the three grouped draw calls. Native reproduction confirms missing and duplicate vertex uploads; 5,057 candidate checks pass, including material transitions, all call sites and actual native vertex upload. Live smoke-flashing acceptance pending. Prior 0.1.61 depth-addressing change did not resolve the reported flashing. All nine archive recipes and previous performance/selection fixes retained.'
update.update(afterFinalSha256=m['engineFinalSha256'],description=notes)
(W/'engine-update.json').write_text(json.dumps(update,indent=2))
docs=W/'docs';shutil.copytree(cfg['documentation'],docs,dirs_exist_ok=True)
for name in ['README.txt','CHANGELOG.md']:
 p=docs/name;p.write_text(notes+'\n\n'+p.read_text(encoding='utf-8-sig'),encoding='utf-8')
cfg.update(version='0.1.62-preview',minimumInstallerVersion='0.1.62-preview',engineUpdate=str(W/'engine-update.json'),documentation=str(docs),releaseNotes=notes)
cfg['helperUpdate'].update(file=str(W/'candidate-helper.json'),sha256=hashlib.sha256((W/'candidate-helper.json').read_bytes()).hexdigest())
(W/'candidate-installer.json').write_text(json.dumps(cfg,indent=2))
(W/'Build-Candidate.ps1').write_text((R/'work/unit-deselection/Build-Candidate.ps1').read_text().replace('unit-deselection/candidate-installer.json','particle-code-investigation/candidate-installer.json'))
(W/'Verify-Package.ps1').write_text((R/'work/unit-deselection/Verify-Package.ps1').read_text().replace('release-056','release-062').replace('unit-deselection/CE.campaign-night-candidate.dll','particle-code-investigation/CE.campaign-night-candidate.dll'))
s=(R/'work/unit-drag-refresh/preflight_deploy.py').read_text().replace('release-058','release-062').replace('release-057','release-061').replace("['native-selection-results.json','unwind-validation.json']","['mapping-fix-validation.json']")
(W/'preflight_deploy.py').write_text(s)
print('Prepared cumulative 0.1.62 candidate; no installed files changed.')
