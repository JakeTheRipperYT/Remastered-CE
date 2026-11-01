from pathlib import Path
import json,base64,hashlib,shutil
W=Path(__file__).resolve().parent;R=W.parent.parent
cfg=json.loads((R/'source/current-installer.json').read_text());assert cfg['version']=='0.1.64-preview'
for name in ['batching-validation.json','unwind-validation.json','mapping-fix-validation.json','merge-benchmark.json']:assert json.loads((W/name).read_text())['status']=='PASS'
layout=json.loads((W/'layout.json').read_text());m=json.loads((W/'candidate-manifest.json').read_text());update=json.loads(Path(cfg['engineUpdate']).read_text())
for o in layout['writes']:update['patches'].append(dict(offset=o['offset'],before=base64.b64encode(bytes.fromhex(o['before'])).decode(),data=base64.b64encode(bytes.fromhex(o['data'])).decode()))
notes='0.1.65-preview: restore particle material batching after the strict global emitter sort. User confirmed0.1.64 fixes flashing but causes a huge FPS drop. Merge only adjacent same-source groups after sorting; preserve the exact successful0.1.64 emitter sequence and leave interleaved sources in place. Native material-change detection now spans the complete run, reducing forced setups1000->1 in a1000-emitter same-source fixture.145 native cases cover segment boundaries, interleaving, inactive entries, vector growth and full native destruction with no leaks/double frees.1158 actual Windows unwind boundaries pass at three bases;5057 prior draw-index checks pass. Isolated native merger median5.2us/1000 emitters with preallocated capacity, excluding gathering/sorting/allocations/GPU work. All nine archives unchanged. Live FPS recovery and flashing retention pending; no claim of measured battle FPS.'
update.update(afterFinalSha256=m['engineFinalSha256'],description=notes);(W/'engine-update.json').write_text(json.dumps(update,indent=2))
docs=W/'docs';shutil.copytree(cfg['documentation'],docs,dirs_exist_ok=True)
for name in ['README.txt','CHANGELOG.md']:
 p=docs/name;p.write_text(notes+'\n\n'+p.read_text(encoding='utf-8-sig'),encoding='utf-8')
cfg.update(version='0.1.65-preview',minimumInstallerVersion='0.1.65-preview',engineUpdate=str(W/'engine-update.json'),documentation=str(docs),releaseNotes=notes)
cfg['helperUpdate'].update(file=str(W/'candidate-helper.json'),sha256=hashlib.sha256((W/'candidate-helper.json').read_bytes()).hexdigest())
(W/'candidate-installer.json').write_text(json.dumps(cfg,indent=2))
(W/'Build-Candidate.ps1').write_text((R/'work/unit-deselection/Build-Candidate.ps1').read_text().replace('unit-deselection/candidate-installer.json','particle-overlap-batching/candidate-installer.json'))
(W/'Verify-Package.ps1').write_text((R/'work/particle-overlap-order/Verify-Package.ps1').read_text().replace('release-064','release-065').replace('particle-overlap-order/CE.campaign-night-candidate.dll','particle-overlap-batching/CE.campaign-night-candidate.dll'))
(W/'preflight_deploy.py').write_text((R/'work/particle-overlap-order/preflight_deploy.py').read_text().replace('release-064','release-065').replace('release-063','release-064'))
print('Prepared private0.1.65 post-sort batching candidate.')
