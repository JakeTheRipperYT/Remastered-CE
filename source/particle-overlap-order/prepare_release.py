from pathlib import Path
import json,base64,shutil
W=Path(__file__).resolve().parent;R=W.parent.parent
cfg=json.loads((R/'source/current-installer.json').read_text());assert cfg['version']=='0.1.63-preview'
native=json.loads((R/'work/particle-code-investigation/overlap-order-reproduction.json').read_text());assert native['status']=='REPRODUCED_CAMERA_STRAFE_ORDER_JUMP'
assert json.loads((R/'work/particle-default-normal/overlap-gpu-hardware.json').read_text())['status']=='PASS'
assert json.loads((W/'mapping-fix-validation.json').read_text())['status']=='PASS'
m=json.loads((W/'candidate-manifest.json').read_text());layout=json.loads((W/'layout.json').read_text());update=json.loads(Path(cfg['engineUpdate']).read_text())
for o in layout['writes']:update['patches'].append(dict(offset=o['offset'],before=base64.b64encode(bytes.fromhex(o['before'])).decode(),data=base64.b64encode(bytes.fromhex(o['data'])).decode()))
notes='0.1.64-preview: strict per-emitter transparent draw ordering candidate. Disable CE emitter-bucket coalescing with one six-byte native branch change. Every emitter retains its own distance key; the original native allocation, sort and draw machinery remain. Reproduction: fixed emitters at3-4m and2cm sideways camera motion flip grouped order B,A,C to C,B,A while actual distance order remains C,B,A. Candidate stays C,B,A across both positions,21 strafe frames and128 randomized near/far fixtures. Installed smoke PS overlap rendering with fixed lighting produces0.1196 maximum RGB jump from this order change, with identical alpha.5,057 native draw-index checks pass. May increase material submissions; live flashing and performance acceptance pending.0.1.63 did not resolve flashing. All nine archive recipes, helper, prior selection and shader performance fixes retained.'
update.update(afterFinalSha256=m['engineFinalSha256'],description=notes);(W/'engine-update.json').write_text(json.dumps(update,indent=2))
docs=W/'docs';shutil.copytree(cfg['documentation'],docs,dirs_exist_ok=True)
for name in ['README.txt','CHANGELOG.md']:
 p=docs/name;p.write_text(notes+'\n\n'+p.read_text(encoding='utf-8-sig'),encoding='utf-8')
cfg.update(version='0.1.64-preview',minimumInstallerVersion='0.1.64-preview',engineUpdate=str(W/'engine-update.json'),documentation=str(docs),releaseNotes=notes)
(W/'candidate-installer.json').write_text(json.dumps(cfg,indent=2))
(W/'Build-Candidate.ps1').write_text((R/'work/unit-deselection/Build-Candidate.ps1').read_text().replace('unit-deselection/candidate-installer.json','particle-overlap-order/candidate-installer.json'))
(W/'Verify-Package.ps1').write_text((R/'work/particle-code-investigation/Verify-Package.ps1').read_text().replace('release-062','release-064').replace('particle-code-investigation/CE.campaign-night-candidate.dll','particle-overlap-order/CE.campaign-night-candidate.dll'))
(W/'preflight_deploy.py').write_text((R/'work/particle-code-investigation/preflight_deploy.py').read_text().replace('release-062','release-064').replace('release-061','release-063'))
for name in ['overlap-order-reproduction.json','test_overlap_order.py']:
 shutil.copyfile(R/'work/particle-code-investigation'/name,W/name)
shutil.copyfile(R/'work/particle-default-normal/overlap-gpu-hardware.json',W/'overlap-gpu-hardware.json')
print('Prepared private0.1.64 overlap-order candidate.')
