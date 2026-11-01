from pathlib import Path
import json,base64,hashlib,shutil
W=Path(__file__).resolve().parent;R=W.parent.parent
cfg=json.loads((R/'source/current-installer.json').read_text());assert cfg['version']=='0.1.65-preview'
for name in ['stream-validation.json','unwind-validation.json','mapping-fix-validation.json']:assert json.loads((W/name).read_text())['status']=='PASS'
m=json.loads((W/'candidate-manifest.json').read_text());layout=json.loads((W/'layout.json').read_text());update=json.loads(Path(cfg['engineUpdate']).read_text())
for o in layout['writes']:update['patches'].append(dict(offset=o['offset'],before=base64.b64encode(bytes.fromhex(o['before'])).decode(),data=base64.b64encode(bytes.fromhex(o['data'])).decode()))
notes='0.1.66-preview: replace per-emitter group construction with sorted source streams. User confirmed64 fixes flashing;64/65 cause severe FPS loss (65 screenshot about44FPS). Compute camera position once per source, update exact native distance keys and retain the native per-source sort. Emit one empty ownership marker per nonempty source; no per-emitter group vectors or their native gather/sort deep copies. After gather, heap-merge sorted source lists and submit adjacent same-source runs through the original native callback. One scratch allocation per pass; pointer membership and unique-distance ordering match strict64. Ties use deterministic source priority.43 native fixtures cover1000 emitters, multiple sources, random cameras, ties, empty sources, real sort/clear/vector-copy/draw/destructor, no leaks/double frees.6669 Windows unwind boundaries at3bases and5057 retained draw-index checks pass. All nine archives and smoke layers unchanged. Live FPS and flashing retention pending; remaining material interleaving/GPU overdraw costs are not claimed solved.'
update.update(afterFinalSha256=m['engineFinalSha256'],description=notes);(W/'engine-update.json').write_text(json.dumps(update,indent=2))
docs=W/'docs';shutil.copytree(cfg['documentation'],docs,dirs_exist_ok=True)
for name in ['README.txt','CHANGELOG.md']:
 p=docs/name;p.write_text(notes+'\n\n'+p.read_text(encoding='utf-8-sig'),encoding='utf-8')
cfg.update(version='0.1.66-preview',minimumInstallerVersion='0.1.66-preview',engineUpdate=str(W/'engine-update.json'),documentation=str(docs),releaseNotes=notes)
cfg['helperUpdate'].update(file=str(W/'candidate-helper.json'),sha256=hashlib.sha256((W/'candidate-helper.json').read_bytes()).hexdigest())
(W/'candidate-installer.json').write_text(json.dumps(cfg,indent=2))
(W/'Build-Candidate.ps1').write_text((R/'work/unit-deselection/Build-Candidate.ps1').read_text().replace('unit-deselection/candidate-installer.json','particle-sorted-stream/candidate-installer.json'))
(W/'Verify-Package.ps1').write_text((R/'work/particle-overlap-batching/Verify-Package.ps1').read_text().replace('release-065','release-066').replace('particle-overlap-batching/CE.campaign-night-candidate.dll','particle-sorted-stream/CE.campaign-night-candidate.dll'))
(W/'preflight_deploy.py').write_text((R/'work/particle-overlap-batching/preflight_deploy.py').read_text().replace('release-065','release-066').replace('release-064','release-065'))
print('Prepared private66 sorted-stream candidate.')
