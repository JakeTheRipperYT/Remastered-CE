from pathlib import Path
import subprocess,sys,json,concurrent.futures,os,time
W=Path(__file__).parent;env=os.environ.copy();env['TEMP']=env['TMP']='F:/Codex/Temp'
def run(name,args=()):
 started=time.monotonic();r=subprocess.run([sys.executable,'-B',str(W/name),*args],cwd=W,env=env,capture_output=True,text=True);suffix='-hardware' if '--hardware' in args else '';log=W/(name.removesuffix('.py')+suffix+'.log');log.write_text(r.stdout+r.stderr)
 return dict(test=name,args=list(args),exitCode=r.returncode,seconds=round(time.monotonic()-started,2),log=str(log),status='PASS' if r.returncode==0 else 'FAIL')
results=[run('test_weather_plan.py')];print(json.dumps(results[-1]),flush=True)
if results[-1]['exitCode']:raise SystemExit(1)
tests=['test_controller_native.py','test_dynamic_controller.py','test_fades_native.py','test_program_bindings.py','test_deployment_puddles.py','test_unit_weather_cards.py','test_native_colour_and_storm.py','test_weather_cycles_native.py','test_puddle_material.py','test_sky_material.py','test_battle_scene.py','test_actual_checkbox_notify.py','test_fade_gpu.py']
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 futures=[pool.submit(run,n) for n in tests]+[pool.submit(run,'test_grass_gpu.py'),pool.submit(run,'test_grass_gpu.py',('--hardware',))]
 for f in concurrent.futures.as_completed(futures):row=f.result();results.append(row);print(json.dumps(row),flush=True)
report=dict(status='PASS' if all(r['exitCode']==0 for r in results) else 'FAIL',installedVersion='0.1.71-preview',tests=results,liveGameplayVerified=False,scope='Native installed helper, original unchanged engine routines, compiled policy, shader binding, actual installed grass DXBC, and installed shader helper math under controlled fixtures. Does not establish live campaign visual/audio acceptance.')
(W/'suite-results.json').write_text(json.dumps(report,indent=2));raise SystemExit(0 if report['status']=='PASS' else 1)
