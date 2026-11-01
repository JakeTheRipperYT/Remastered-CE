from pathlib import Path
import sys,json
sys.path.insert(0,r'F:/Codex/Remastered-CE-Port/work/particle-camera-stability');import build_candidate as b
G=Path(r'D:/SteamLibrary/steamapps/common/Shogun 2 Complete Edition/RemasteredCE/data');W=Path(r'F:/Codex/Remastered-CE-Port/work/grass-matte')
main,end=b.readpack((G/'shaders.pack').read_bytes());over=b.read_overlay(G/'rce_campaign_night_visuals.pack');eff={**main,**over}
for n,e in eff.items():
 if n.startswith('fx/'):
  p=W/'compile'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(e['data'])
(W/'compile/personal_config.h').write_text('// Runtime configuration\n')
for n,e in eff.items():
 if n.startswith('fxc/') and ('_rigidgrass.hlsl_ps_' in n or '_rigidgrasswet.hlsl_ps_' in n):print(n,len(e['data']),'overlay',n in over)
print('Material source', b.sha(eff['fx/rigidgrasscommon.hlsl']['data']))
