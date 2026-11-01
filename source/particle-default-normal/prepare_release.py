from pathlib import Path
import json,hashlib,shutil
W=Path(__file__).resolve().parent;R=W.parent.parent
cfg=json.loads((R/'source/current-installer.json').read_text());assert cfg['version']=='0.1.62-preview'
assert json.loads((W/'asset-validation.json').read_text())['status']=='PASS'
for f,status in [('gpu-validation.json','PASS_D3D11_WARP'),('gpu-validation-hardware.json','PASS_D3D11_HARDWARE')]:assert json.loads((W/f).read_text())['status']==status
asset=W/'default_pfx_packed_normal.dds'
cfg['assets'].append(dict(path='effects/textures/default_pfx_packed_normal.dds',file=str(asset),sha256=hashlib.sha256(asset.read_bytes()).hexdigest(),operations=str(W/'asset-operations.json')))
docs=W/'docs';shutil.copytree(cfg['documentation'],docs,dirs_exist_ok=True)
notes='0.1.63-preview: correct default particle normal-map channel packing for CE lighting. The shipped default map is unchanged RGB data with constant alpha, but CE reads red/alpha/blue. Carry the original green component in alpha at all eight mip levels; preserve decoded RGB and keep custom normal maps unchanged. DDS uses supported BGRA8 storage, adding 262128 texture bytes. Installed shaders/native engine are unchanged.376 offline rendering cases each pass on hardware and WARP; output alpha/coverage are identical. Lighting approaches the RGB reference, with maximum residual 0.004108 hardware / 0.001689 WARP due to BC3-to-byte rounding. This corrects the channel regression; live close-strafe flashing acceptance remains pending. User confirmed0.1.62 did not fix flashing. OG already decoded twice; double decoding is not a new CE regression.'
for name in ['README.txt','CHANGELOG.md']:
 p=docs/name;p.write_text(notes+'\n\n'+p.read_text(encoding='utf-8-sig'),encoding='utf-8')
cfg.update(version='0.1.63-preview',minimumInstallerVersion='0.1.63-preview',documentation=str(docs),releaseNotes=notes)
(W/'candidate-installer.json').write_text(json.dumps(cfg,indent=2))
(W/'Build-Candidate.ps1').write_text((R/'work/unit-deselection/Build-Candidate.ps1').read_text().replace('unit-deselection/candidate-installer.json','particle-default-normal/candidate-installer.json'))
print('Prepared private 0.1.63 lighting candidate; nothing installed.')
