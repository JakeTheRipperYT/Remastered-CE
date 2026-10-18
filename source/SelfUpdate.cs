using System;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Text;
using System.Security.Cryptography;
using System.Collections.Generic;
using System.Diagnostics;
using System.Threading;
using System.Windows.Forms;

namespace RemasteredCE {
public sealed class InstallerBundle {
 public string Version;public byte[] Executable,Config;
 public static InstallerBundle Load(string path,string expected=null){
  byte[] bytes=File.ReadAllBytes(path);
  if(bytes.Length<400||bytes.Length>64*1024*1024||Encoding.ASCII.GetString(bytes,0,8)!="RCEAPP01")throw new InvalidDataException("Invalid installer update bundle.");
  int n=BitConverter.ToInt32(bytes,8);if(n<256||n>1024||bytes.Length<=12+n)throw new InvalidDataException("Invalid installer update signature.");
  byte[] sig=new byte[n],zip=new byte[bytes.Length-12-n];Buffer.BlockCopy(bytes,12,sig,0,n);Buffer.BlockCopy(bytes,12+n,zip,0,zip.Length);
  using(var rsa=new RSACryptoServiceProvider()){rsa.FromXmlString(Encoding.UTF8.GetString(Release.Resource("publicKey")));if(!rsa.VerifyData(zip,CryptoConfig.MapNameToOID("SHA256"),sig))throw new InvalidDataException("Installer update signature verification failed. Your installer was preserved.");}
  using(var archive=new ZipArchive(new MemoryStream(zip),ZipArchiveMode.Read)){
   var names=new[]{"installer.json","RemasteredCE_Setup.exe","RemasteredCE_Setup.exe.config"};
   if(archive.Entries.Count!=3||!new HashSet<string>(archive.Entries.Select(e=>e.FullName),StringComparer.Ordinal).SetEquals(names))throw new InvalidDataException("Unexpected installer bundle files.");
   var meta=J.Parse(Encoding.UTF8.GetString(Read(archive,names[0],16384)));string version=J.S(meta,"version");ReleaseVersion.Parse(version);
   if(J.N(meta,"schema")!=1||(expected!=null&&version!=expected))throw new InvalidDataException("Installer bundle version does not match the selected release.");
   byte[] exe=Read(archive,names[1],48*1024*1024),config=Read(archive,names[2],65536);
   if(exe.Length<2||exe[0]!='M'||exe[1]!='Z'||Engine.Hash(exe)!=J.S(meta,"executableSha256")||Engine.Hash(config)!=J.S(meta,"configSha256"))throw new InvalidDataException("Installer bundle contents failed verification.");
   return new InstallerBundle{Version=version,Executable=exe,Config=config};
  }
 }
 static byte[] Read(ZipArchive zip,string name,int max){var e=zip.GetEntry(name);if(e==null||e.Length<1||e.Length>max)throw new InvalidDataException("Invalid installer component: "+name);using(var s=e.Open())using(var output=new MemoryStream()){s.CopyTo(output);if(output.Length!=e.Length||output.Length>max)throw new InvalidDataException("Incomplete installer component.");return output.ToArray();}}
}
public static class SelfUpdate {
 public static string Quote(string s){if(s.IndexOf('\0')>=0)throw new ArgumentException("Invalid process argument.");var b=new StringBuilder("\"");int slashes=0;foreach(char c in s){if(c=='\\'){slashes++;continue;}if(c=='\"'){b.Append('\\',slashes*2+1);b.Append(c);}else{b.Append('\\',slashes);b.Append(c);}slashes=0;}b.Append('\\',slashes*2);return b.Append('"').ToString();}
 public static bool Begin(string bundle,string expected){
  var update=InstallerBundle.Load(bundle,expected);if(!OnlineUpdates.NeedsUpdate(OnlineUpdates.AppVersion,update.Version))return false;
  string target=Path.GetFullPath(Application.ExecutablePath);ValidateTarget(target);
  string dir=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"RemasteredCE","self-update",Guid.NewGuid().ToString("N"));Engine.NoLinks(dir);Directory.CreateDirectory(dir);
  string helper=Path.Combine(dir,"RemasteredCE_UpdateHelper.exe"),saved=Path.Combine(dir,"installer.rceu");File.Copy(target,helper);if(File.Exists(target+".config"))File.Copy(target+".config",helper+".config");File.Copy(bundle,saved);
  string args="--apply-self-update "+Process.GetCurrentProcess().Id+" "+Quote(target)+" "+Quote(saved)+" "+Engine.FileHash(target);
  Process.Start(new ProcessStartInfo(helper,args){UseShellExecute=false,CreateNoWindow=true,WorkingDirectory=dir});return true;
 }
 static void ValidateTarget(string target){if(!String.Equals(Path.GetFileName(target),"RemasteredCE_Setup.exe",StringComparison.OrdinalIgnoreCase))throw new IOException("Keep the installer named RemasteredCE_Setup.exe to enable automatic installer updates.");Engine.NoLinks(Path.GetDirectoryName(target));if(File.Exists(target)&&(File.GetAttributes(target)&FileAttributes.ReparsePoint)!=0)throw new IOException("Linked installer executables cannot be updated.");if(File.Exists(target+".config")&&(File.GetAttributes(target+".config")&FileAttributes.ReparsePoint)!=0)throw new IOException("Linked installer configuration cannot be updated.");}
 public static void Apply(int parentId,string target,string bundle,string oldHash){
  target=Path.GetFullPath(target);ValidateTarget(target);var update=InstallerBundle.Load(bundle);
  if(!OnlineUpdates.NeedsUpdate(OnlineUpdates.AppVersion,update.Version))throw new InvalidDataException("The installer update must be newer than the running helper.");
  Process parent=null;try{parent=Process.GetProcessById(parentId);}catch(ArgumentException){}
  if(parent!=null){using(parent){try{if(!parent.HasExited&&!String.Equals(Path.GetFullPath(parent.MainModule.FileName),target,StringComparison.OrdinalIgnoreCase))throw new IOException("Installer update parent does not match its target.");}catch(InvalidOperationException){if(!parent.HasExited)throw;}catch(System.ComponentModel.Win32Exception){if(!parent.HasExited)throw;}if(!parent.WaitForExit(60000))throw new IOException("The installer did not close. Close it and retry the update.");}}
  Replace(target,update,oldHash,()=>Process.Start(new ProcessStartInfo(target,"--resume-update"){UseShellExecute=false,WorkingDirectory=Path.GetDirectoryName(target)}));
 }
 internal static void Replace(string target,InstallerBundle update,string oldHash,Action restart){
  ValidateTarget(target);string dir=Path.GetDirectoryName(target),id=Guid.NewGuid().ToString("N");
  string staged=Path.Combine(dir,".RemasteredCE-"+id+".new.exe"),config=target+".config",stagedConfig=staged+".config",backup=Path.Combine(dir,"RemasteredCE_Setup.previous-"+id+".exe"),backupConfig=backup+".config";
  string lockPath=Path.Combine(dir,".RemasteredCE-installer-update.lock");if(File.Exists(lockPath)&&(File.GetAttributes(lockPath)&FileAttributes.ReparsePoint)!=0)throw new IOException("Linked installer update lock.");
  using(var updateLock=new FileStream(lockPath,FileMode.OpenOrCreate,FileAccess.ReadWrite,FileShare.None)){
   if(!File.Exists(target)||Engine.FileHash(target)!=oldHash)throw new IOException("The installer changed while the update was being prepared. Retry the update.");
   bool exeReplaced=false,configReplaced=false,hadConfig=File.Exists(config);
   try{
    File.WriteAllBytes(staged,update.Executable);File.WriteAllBytes(stagedConfig,update.Config);
    if(Engine.FileHash(staged)!=Engine.Hash(update.Executable)||Engine.FileHash(stagedConfig)!=Engine.Hash(update.Config))throw new IOException("Installer staging verification failed.");
    File.Replace(staged,target,backup);exeReplaced=true;
    if(hadConfig)File.Replace(stagedConfig,config,backupConfig);else File.Move(stagedConfig,config);configReplaced=true;
    if(Engine.FileHash(target)!=Engine.Hash(update.Executable)||Engine.FileHash(config)!=Engine.Hash(update.Config))throw new IOException("Installed setup verification failed.");
    restart();
   }catch{
    if(configReplaced){if(hadConfig)File.Copy(backupConfig,config,true);else File.Delete(config);}
    if(exeReplaced)File.Copy(backup,target,true);
    throw;
   }finally{if(File.Exists(staged))File.Delete(staged);if(File.Exists(stagedConfig))File.Delete(stagedConfig);}
  }
 }
 public static void Tests(List<string> results){
  string root=Path.Combine(Path.GetTempPath(),"RCE-self-update-test-"+Guid.NewGuid().ToString("N"));Directory.CreateDirectory(root);
  try{
   string target=Path.Combine(root,"RemasteredCE_Setup.exe");byte[] before=Encoding.ASCII.GetBytes("old setup"),after=Encoding.ASCII.GetBytes("new setup");File.WriteAllBytes(target,before);File.WriteAllText(target+".config","old config");
   var update=new InstallerBundle{Version="99.0.0",Executable=after,Config=Encoding.ASCII.GetBytes("new config")};bool called=false;
   Replace(target,update,Engine.Hash(before),()=>called=true);if(!called||!File.ReadAllBytes(target).SequenceEqual(after)||File.ReadAllText(target+".config")!="new config")throw new Exception("Installer replacement failed.");results.Add("PASS: installer and config replaced together, previous setup preserved");
   bool rejected=false;try{Replace(target,update,Engine.Hash(before),()=>{});}catch(IOException){rejected=true;}if(!rejected)throw new Exception("Changed setup was accepted.");results.Add("PASS: installer replacement rejects changed target");
   rejected=false;try{Replace(target,new InstallerBundle{Executable=before,Config=Encoding.ASCII.GetBytes("other config")},Engine.Hash(after),()=>{throw new IOException("restart fixture");});}catch(IOException){rejected=true;}
   if(!rejected||!File.ReadAllBytes(target).SequenceEqual(after)||File.ReadAllText(target+".config")!="new config")throw new Exception("Installer rollback failed.");results.Add("PASS: restart failure restores both previous installer and config");
   if(Quote(@"C:\folder with spaces\")!="\"C:\\folder with spaces\\\\\"")throw new Exception("Argument quoting failed.");results.Add("PASS: updater quotes spaces and trailing path separators");
  }finally{Engine.NoLinks(root);foreach(string file in Directory.GetFiles(root))File.Delete(file);Directory.Delete(root);}
 }
}
}
