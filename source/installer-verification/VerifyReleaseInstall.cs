using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Security.Cryptography;
using System.Web.Script.Serialization;
public static class VerifyReleaseInstall {
 static readonly JavaScriptSerializer Json=new JavaScriptSerializer { MaxJsonLength=64*1024*1024,RecursionLimit=200 };
 static int assertions;
 static void Check(bool b,string message){if(!b)throw new Exception(message);assertions++;}
 static string Hash(string path){using(var stream=File.OpenRead(path))using(var sha=SHA256.Create())return BitConverter.ToString(sha.ComputeHash(stream)).Replace("-","").ToLowerInvariant();}
 static void Put(string root,string path,string text){path=Path.Combine(root,path);Directory.CreateDirectory(Path.GetDirectoryName(path));File.WriteAllText(path,text);}
 static void EnsureF(string path){Check(Path.GetPathRoot(Path.GetFullPath(path)).Equals("F:\\",StringComparison.OrdinalIgnoreCase),"All outputs must be on F");}
 static object Invoke(MethodInfo m,object target,params object[] args){try{return m.Invoke(target,args);}catch(TargetInvocationException ex){throw ex.InnerException??ex;}}
 public static int Main(string[] args){
  // args: final setup, final signed RCE, original CE root, original OG root, NEW F-only acceptance root
  string log=null;object release=null;
  try{
   Check(args.Length==5,"Expected setup/package/CE/OG/F-root arguments");
   string fixture=Path.GetFullPath(args[4]);EnsureF(fixture);Check(!Directory.Exists(fixture),"Acceptance root must be new");
   Directory.CreateDirectory(fixture);log=Path.Combine(fixture,"installation.log");
   var assembly=Assembly.LoadFrom(args[0]);var rt=assembly.GetType("RemasteredCE.Release",true);var et=assembly.GetType("RemasteredCE.Engine",true);
   release=Invoke(rt.GetMethod("Load"),null,new object[]{null});
   var manifest=(Dictionary<string,object>)rt.GetField("Manifest").GetValue(release);
   var embedded=(byte[])rt.GetField("PackageBytes").GetValue(release);
   Check(embedded.SequenceEqual(File.ReadAllBytes(args[1])),"Final setup embeds exact final signed package");
   Check((string)manifest["version"]=="0.1.71-preview","Final public version");
   string stage=Path.Combine(fixture,"RemasteredCE.staging_acceptance"),previous=Path.Combine(fixture,"RemasteredCE.previous_acceptance"),live=Path.Combine(fixture,"RemasteredCE");
   EnsureF(stage);EnsureF(previous);EnsureF(live);
   // Synthetic pre-existing installation tests upgrade publication without changing
   // the real installation. User settings are modeled outside the managed folder.
   Put(live,"CE.dll","previous engine fixture");Put(live,"mods/keep.pack","user mod retained");Put(live,"data/custom-keep.pack","custom data mod retained");Put(fixture,"user-settings/profile.json","profile retained");
   Put(fixture,"Launch_Remastered_CE.exe","old root launcher fixture");Put(fixture,"RemasteredCE_Bootstrap.exe","old root bootstrap fixture");
   File.Copy(Path.Combine(args[2],"shogun2_complete_edition.exe"),Path.Combine(fixture,"shogun2_complete_edition.exe"));string originalExeHash=Hash(Path.Combine(fixture,"shogun2_complete_edition.exe"));
   object engine=Activator.CreateInstance(et);
   et.GetField("Progress").SetValue(engine,(Action<string,int>)((s,p)=>{string line=DateTime.UtcNow.ToString("o")+" "+p+"% "+s;File.AppendAllText(log,line+Environment.NewLine);if(!s.StartsWith("Building assets:"))Console.WriteLine(line);}));
   // Actual final-setup Build reads D inputs but directs every generated output to F.
   // Its normal code verifies source hashes, every reconstructed asset and all nine completed packs.
   Invoke(et.GetMethod("Build"),engine,release,args[2],args[3],stage);
   var state=Json.Deserialize<Dictionary<string,object>>(File.ReadAllText(Path.Combine(stage,"install-state.json")));
   Check((string)state["version"]==(string)manifest["version"],"Staged state version");
   Check(Hash(Path.Combine(stage,"CE.dll"))==(string)manifest["engineFinalSha256"],"Entire final engine matches signed hash");
   Check(Hash(Path.Combine(stage,"release.rce"))==Hash(args[1]),"Offline package staged exactly");
   string managerHash=Hash(Path.Combine(stage,"RemasteredCE_Launcher.exe"));
   Check(managerHash==(string)state["unifiedLauncherSha256"],"Fixed manager ownership hash matches actual staged manager");
   Check(managerHash==(string)manifest["unifiedLauncherSha256"],"Signed package contains fixed manager");
   Check(((object[])manifest["files"]).Length==9,"Nine reconstructed packs");
   var packRows=new List<object>();foreach(Dictionary<string,object> f in (object[])manifest["files"]){string path=Path.Combine(stage,((string)f["destination"]).Replace('/',Path.DirectorySeparatorChar));Check(File.Exists(path),"Reconstructed pack exists");packRows.Add(new{file=f["destination"],sha256=f["sha256"],hashVerifiedByActualBuild=true});}
   // Invoke the actual publication method, with ONLY F paths, including root helper copies.
   var publish=et.GetMethod("PublishVerified",BindingFlags.Public|BindingFlags.Static);Check(publish!=null,"Actual publication method available");
   Invoke(publish,null,stage,fixture,previous);
   Check(Hash(Path.Combine(live,"CE.dll"))==(string)manifest["engineFinalSha256"],"Published engine hash");
   Check(File.ReadAllText(Path.Combine(previous,"CE.dll"))=="previous engine fixture","Previous installation retained");
   Check(File.ReadAllText(Path.Combine(live,"mods/keep.pack"))=="user mod retained","User mod preserved during actual publication");
   Check(File.ReadAllText(Path.Combine(live,"data/custom-keep.pack"))=="custom data mod retained","Custom data mod preserved during actual publication");
   Check(File.ReadAllText(Path.Combine(fixture,"user-settings/profile.json"))=="profile retained","External profile fixture preserved");
   Check(Hash(Path.Combine(fixture,"shogun2_complete_edition.exe"))==originalExeHash,"Original CE executable fixture not replaced");
   foreach(string name in new[]{"Launch_Remastered_CE.exe","RemasteredCE_Bootstrap.exe"})Check(Hash(Path.Combine(fixture,name))==Hash(Path.Combine(live,name)),"Root/managed helper match");
   Check(Hash(Path.Combine(live,"RemasteredCE_Launcher.exe"))==managerHash,"Published corrected manager");
   // A separate tiny failure fixture exercises actual publication rollback.
   string failed=Path.Combine(fixture,"rollback-fixture"),flive=Path.Combine(failed,"RemasteredCE"),fstage=Path.Combine(failed,"RemasteredCE.staging_failure"),fprevious=Path.Combine(failed,"RemasteredCE.previous_failure");
   Put(flive,"CE.dll","old engine");Put(flive,"mods/keep.pack","old user mod");Put(fstage,"CE.dll","new engine");Put(fstage,"Launch_Remastered_CE.exe","new launcher");Put(fstage,"RemasteredCE_Bootstrap.exe","new bootstrap");Put(failed,"RemasteredCE_Bootstrap.exe","old bootstrap");Directory.CreateDirectory(Path.Combine(failed,"Launch_Remastered_CE.exe"));
   bool rejected=false;try{Invoke(publish,null,fstage,failed,fprevious);}catch(IOException){rejected=true;}
   Check(rejected,"Forced root publication failure rejected");Check(File.ReadAllText(Path.Combine(flive,"CE.dll"))=="old engine","Rollback restored old engine");
   Check(File.ReadAllText(Path.Combine(flive,"mods/keep.pack"))=="old user mod","Rollback restored user mod location");Check(File.ReadAllText(Path.Combine(failed,"RemasteredCE_Bootstrap.exe"))=="old bootstrap","Rollback restored replaced root helper");Check(Directory.Exists(fstage)&&!Directory.Exists(fprevious),"Failed candidate retained and previous restored");
   var receipt=new {status="PASS",version=manifest["version"],setupSha256=Hash(args[0]),packageSha256=Hash(args[1]),engineSha256=manifest["engineFinalSha256"],launcherSha256=managerHash,assertions,packRows,fixture,actualFinalSetupAssemblyUsed=true,actualFullBuildAndPublicationPassed=true,allNinePackHashesVerifiedByActualBuild=true,upgradeModsPreserved=true,customDataModsPreserved=true,publicationRollbackPassed=true,realGameInstallationModified=false,gameLaunched=false,scope="Actual final installer reconstruction and publication in isolated F target, plus forced publication rollback. Does not call Install wrapper or change user preferences; launcher/UI/integration tests cover those separately."};
   File.WriteAllText(Path.Combine(fixture,"installation-verification.json"),Json.Serialize(receipt));Console.WriteLine("PASS complete F-only installer reconstruction/publication verification");return 0;
  }catch(Exception ex){if(log!=null)File.AppendAllText(log,"FAILED "+ex+Environment.NewLine);Console.Error.WriteLine(ex);return 1;}
  finally{if(release is IDisposable)((IDisposable)release).Dispose();}
 }
}
