from pathlib import Path
import shutil
W=Path(r'F:/Codex/Remastered-CE-Port/work/grass-opening-wetness');R=W.parents[1];old=R/'work/weather-card-persistence'
for n in ['test_controller_native.py','test_dynamic_controller.py','test_fades_native.py','test_program_bindings.py','controller-layout.json','environment-catalog.json','plan_test.dll']:shutil.copyfile(old/n,W/n)
shutil.copyfile(R/'work/release-070/helper.json',W/'candidate-helper.json')
p=W/'test_controller_native.py';s=p.read_text().replace("sys.path[:0]=[", "sys.path[:0]=[r'F:/Codex/Temp/unit-selection-runtime',");p.write_text(s)
old=R/'work/grass-matte';s=(old/'prepare_release.py').read_text().replace("cfg['version']=='0.1.68-preview'","cfg['version']=='0.1.70-preview'").replace('grass070','grass071').replace('0.1.70-preview','0.1.71-preview')
# The predecessor assertion remains .70; only the new release is .71.
s=s.replace("assert cfg['version']=='0.1.71-preview'","assert cfg['version']=='0.1.70-preview'")
a=s.index("notes='");z=s.index('\ndocs=',a)
notes='0.1.71-preview: retain matte grass while restoring a distinct wet coating. Apply roughness floor 0.9 before wetness and use the immutable opening-ground wet flag for campaign grass, rather than the current dry/rain shader permutation. Rain-start grass remains wet after skies clear; clear-start grass stays dry during later rain. Keep non-campaign native wet/dry selection. Existing terrain puddle coverage and native opening-ground controller are retained. New named weather-buffer binding is verified and actual dry/wet GBuffer shaders are rendered in 36 cases on hardware and 36 on WARP, including every MRT output. Engine/helper and all other assets are unchanged. Live appearance and reported terrain-puddle behavior still require user confirmation.'
s=s[:a]+'notes='+repr(notes)+s[z:];s=s.replace('cumulative .70 trial','cumulative .71 fix');(W/'prepare_release.py').write_text(s)
