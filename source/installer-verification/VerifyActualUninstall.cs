using System;using System.IO;using System.Reflection;using System.Web.Script.Serialization;
public static class VerifyActualUninstall {
 public static int Main(string[] a){try{
  string root=Path.GetFullPath(a[1]);if(!root.StartsWith(@"F:\Codex\Remastered-CE-Port\work\github-release-071\acceptance-full",StringComparison.OrdinalIgnoreCase))throw new Exception("Wrong isolated root");
  var asm=Assembly.LoadFrom(a[0]);var type=asm.GetType("RemasteredCE.Engine",true);var engine=Activator.CreateInstance(type);
  if(!File.Exists(Path.Combine(root,"installation-verification.json")))throw new Exception("Full installation verification is required first");
  type.GetMethod("Uninstall").Invoke(engine,new object[]{root});
  string live=Path.Combine(root,"RemasteredCE");
  foreach(string name in new[]{"CE.dll","install-state.json","release.rce","RemasteredCE_Launcher.exe","data/rce_campaign_night_visuals.pack","data/data.pack","data/shaders.pack","data/bp_orig.pack","data/web_content.pack","data/local_global.pack","data/models.pack","data/audio.pack","data/movies.pack"})if(File.Exists(Path.Combine(live,name)))throw new Exception("Owned file survived uninstall: "+name);
  if(File.ReadAllText(Path.Combine(live,"mods/keep.pack"))!="user mod retained"||File.ReadAllText(Path.Combine(live,"data/custom-keep.pack"))!="custom data mod retained"||File.ReadAllText(Path.Combine(root,"user-settings/profile.json"))!="profile retained")throw new Exception("Custom data or external profile changed");
  var receipt=new{status="PASS",actualFinalSetupUninstallCalled=true,nineGeneratedPacksRemoved=true,userModsPreserved=true,externalProfilePreserved=true,realGameInstallationModified=false};
  File.WriteAllText(a[2],new JavaScriptSerializer().Serialize(receipt));Console.WriteLine("PASS: actual final installer uninstall removed all nine owned packs and retained custom mods/profile");return 0;
 }catch(Exception e){Console.Error.WriteLine(e);return 1;}}
}
