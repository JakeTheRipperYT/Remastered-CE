from pathlib import Path
import shutil
W=Path(r'F:/Codex/Remastered-CE-Port/work/grass-matte');base=Path(r'F:/Codex/Remastered-CE-Port/work/particle-camera-stability/vanilla-control/fx')
for name in ['lighting.hlsl','sky.hlsl','fog_3k.hlsl']:shutil.copyfile(base/name,W/'compile/fx'/name)
