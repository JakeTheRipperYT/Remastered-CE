using System;
using System.IO;
using System.Linq;
using System.Text;
using System.Collections.Generic;
using System.Diagnostics;
using System.Threading;
using RemasteredCE;
class UpdateTests {
 static void Reject(Action a,string message){bool rejected=false;try{a();}catch(InvalidDataException){rejected=true;}if(!rejected)throw new Exception(message);}
 static int Main(string[] args){try{
  if(args.Length==5&&args[0]=="--apply-self-update"){SelfUpdate.Apply(Int32.Parse(args[1]),args[2],args[3],args[4]);return 0;}
  if(args.Length==2&&args[0]=="--begin-fixture"){if(!SelfUpdate.Begin(args[1],"0.1.14-preview"))throw new Exception("Fixture did not start updater");return 0;}
  string real=args[0],fixture=args[1],report=args[2],root=Path.Combine(Path.GetDirectoryName(report),"update-fixture-"+Guid.NewGuid().ToString("N"));Directory.CreateDirectory(root);var results=new List<string>();
  var bundle=InstallerBundle.Load(real,"0.1.13-preview");if(bundle.Version!="0.1.13-preview")throw new Exception("Bundle version");results.Add("PASS: published installer bundle signature, hashes, executable and config verified");
  Reject(()=>InstallerBundle.Load(real,"99.0.0"),"Mismatched bundle accepted");results.Add("PASS: installer bundle version mismatch rejected");
  var bytes=File.ReadAllBytes(real);bytes[bytes.Length-1]^=1;string tampered=Path.Combine(root,"tampered.rceu");File.WriteAllBytes(tampered,bytes);Reject(()=>InstallerBundle.Load(tampered),"Tampered bundle accepted");results.Add("PASS: tampered signed installer rejected before replacement");
  string prefix="https://github.com/JakeTheRipperYT/Remastered-CE/releases/download/v0.1.13-preview/";
  var row=new Dictionary<string,object>{{"tag_name","v0.1.13-preview"},{"draft",false},{"assets",new[]{new Dictionary<string,object>{{"name","RemasteredCE-0.1.13-preview.rce"},{"state","uploaded"},{"size",123},{"browser_download_url",prefix+"RemasteredCE-0.1.13-preview.rce"}},new Dictionary<string,object>{{"name","RemasteredCE-0.1.13-preview.rceu"},{"state","uploaded"},{"size",456},{"browser_download_url",prefix+"RemasteredCE-0.1.13-preview.rceu"}}}}};
  string json=J.Json().Serialize(new[]{row});var selected=OnlineUpdates.Select(json);if(selected.InstallerSize!=456||selected.InstallerDownloadUrl!=prefix+"RemasteredCE-0.1.13-preview.rceu")throw new Exception("Installer release selection failed");results.Add("PASS: update discovery pairs patch and installer from the same release");
  string bad=json.Replace(prefix+"RemasteredCE-0.1.13-preview.rceu","https://untrusted.invalid/setup.rceu");if(OnlineUpdates.Select(bad).InstallerDownloadUrl!=null)throw new Exception("Untrusted installer URL accepted");results.Add("PASS: installer discovery rejects external download addresses");
  string target=Path.Combine(root,"RemasteredCE_Setup.exe");File.WriteAllBytes(target,bundle.Executable);File.WriteAllBytes(target+".config",bundle.Config);string before=Engine.FileHash(target);var next=InstallerBundle.Load(fixture);
  SelfUpdate.Apply(Int32.MaxValue,target,fixture,before);
  string marker=Path.Combine(root,"resume.txt");for(int n=0;n<100&&!File.Exists(marker);n++)Thread.Sleep(100);
  if(!File.Exists(marker)||File.ReadAllText(marker)!="--resume-update"||Engine.FileHash(target)!=Engine.Hash(next.Executable)||!Directory.GetFiles(root,"RemasteredCE_Setup.previous-*.exe").Any(p=>Engine.FileHash(p)==before))throw new Exception("End-to-end helper replacement or resume failed");
  results.Add("PASS: signed helper update replaces actual setup, keeps rollback copy and restarts with --resume-update");
  string chain=Path.Combine(root,"helper chain with spaces");Directory.CreateDirectory(chain);string chainSetup=Path.Combine(chain,"RemasteredCE_Setup.exe");File.Copy(System.Reflection.Assembly.GetExecutingAssembly().Location,chainSetup);File.WriteAllBytes(chainSetup+".config",bundle.Config);
  using(var parent=Process.Start(new ProcessStartInfo(chainSetup,"--begin-fixture "+SelfUpdate.Quote(fixture)){UseShellExecute=false,CreateNoWindow=true,WorkingDirectory=chain})){if(!parent.WaitForExit(60000)||parent.ExitCode!=0)throw new Exception("Begin helper parent failed");}
  string chainMarker=Path.Combine(chain,"resume.txt");for(int n=0;n<150&&!File.Exists(chainMarker);n++)Thread.Sleep(100);
  if(!File.Exists(chainMarker)||File.ReadAllText(chainMarker)!="--resume-update"||Engine.FileHash(chainSetup)!=Engine.Hash(next.Executable))throw new Exception("Full parent/helper/resume chain failed");results.Add("PASS: actual parent exits, copied helper verifies bundle and replaces setup at a path with spaces, then resumes automatically");
  SelfUpdate.Tests(results);
  foreach(int count in new[]{4,5,6}){
   string game=Path.Combine(root,"uninstall-"+count),live=Path.Combine(game,"RemasteredCE");Directory.CreateDirectory(Path.Combine(live,"data"));Directory.CreateDirectory(Path.Combine(game,"data"));
   string[] packs=new[]{"data/data.pack","data/shaders.pack","data/bp_orig.pack","data/web_content.pack","data/local_global.pack","data/models.pack"}.Take(count).ToArray();
   File.WriteAllText(Path.Combine(game,"shogun2_complete_edition.exe"),"vanilla executable");File.WriteAllText(Path.Combine(game,"data","models.pack"),"vanilla models");File.WriteAllText(Path.Combine(live,"CE.dll"),"fixture engine");
   foreach(string pack in packs)File.WriteAllText(Engine.Under(live,pack),"modified pack");File.WriteAllText(Path.Combine(live,"keep.txt"),"user file");
   var installed=new Dictionary<string,object>{{"schema",1},{"engineHash","fixture"},{"files",packs.Select(p=>new Dictionary<string,object>{{"file",p}}).ToArray()}};
   File.WriteAllText(Path.Combine(live,"install-state.json"),J.Json().Serialize(installed));new Engine().Uninstall(game);
   if(packs.Any(p=>File.Exists(Engine.Under(live,p)))||File.ReadAllText(Path.Combine(game,"data","models.pack"))!="vanilla models"||File.ReadAllText(Path.Combine(live,"keep.txt"))!="user file")throw new Exception("Managed pack uninstall failed: "+count);
   results.Add("PASS: uninstall supports "+count+" managed packs and preserves vanilla models and user files");
  }
  File.WriteAllLines(report,results);Console.WriteLine(String.Join(Environment.NewLine,results));return 0;
 }catch(Exception ex){Console.Error.WriteLine(ex);return 1;}}
}
