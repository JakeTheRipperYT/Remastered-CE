"""Compile this project's native launcher only; never compile engine code."""
from pathlib import Path
import os,subprocess

def build(root,work):
 source=root/'source';work.mkdir(exist_ok=True,parents=True)
 vs=Path(r'C:\Program Files\Microsoft Visual Studio\18\Community')
 vcroot=sorted((vs/'VC/Tools/MSVC').iterdir(),key=lambda p:tuple(map(int,p.name.split('.'))))[-1]
 vc=vcroot/'bin/Hostx64/x64';sdk=Path(r'C:\Program Files (x86)\Windows Kits\10');version='10.0.26100.0'
 env=os.environ.copy();env['TEMP']=env['TMP']=str(root/'work/temp')
 env['PATH']=str(sdk/'bin'/version/'x64')+';'+str(vc)+';'+env['PATH']
 env['INCLUDE']=';'.join(map(str,[vcroot/'include']+[sdk/'Include'/version/p for p in ['ucrt','shared','um','winrt']]))
 env['LIB']=';'.join(map(str,[vcroot/'lib/x64',sdk/'Lib'/version/'um/x64',sdk/'Lib'/version/'ucrt/x64']))
 def run(args):subprocess.run(list(map(str,args)),cwd=work,env=env,check=True)
 resource=work/'launcher.rc';resource.write_text('1 ICON "'+str(source/'assets/RemasteredCE.ico').replace('\\','\\\\')+'"\n')
 run([sdk/'bin'/version/'x64/rc.exe','/nologo','/fo',work/'launcher.res',resource])
 run([vc/'cl.exe','/nologo','/O1','/GS-','/W4','/WX','/c',source/'launcher.c',f'/Fo{work/"launcher.obj"}'])
 output=work/'Launch_Remastered_CE.exe'
 run([vc/'link.exe','/nologo','/MANIFEST:EMBED',"/MANIFESTUAC:level='asInvoker' uiAccess='false'",'/NODEFAULTLIB','/ENTRY:entry','/SUBSYSTEM:WINDOWS','/MACHINE:X64',f'/OUT:{output}',work/'launcher.obj',work/'launcher.res','kernel32.lib','user32.lib','advapi32.lib'])
 run([vc/'cl.exe','/nologo','/O1','/GS-','/W4','/WX','/c',source/'test_launcher_modes.c',f'/Fo{work/"launcher-tests.obj"}'])
 test=work/'test-launcher-modes.exe'
 run([vc/'link.exe','/nologo','/NODEFAULTLIB','/ENTRY:test_entry','/SUBSYSTEM:CONSOLE','/MACHINE:X64',f'/OUT:{test}',work/'launcher-tests.obj','kernel32.lib','user32.lib','advapi32.lib'])
 run([test])
 return output
