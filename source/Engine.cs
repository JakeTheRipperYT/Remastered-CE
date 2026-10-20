using System;
using System.IO;
using System.IO.Compression;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Security.Cryptography;
using System.Web.Script.Serialization;
using System.Runtime.InteropServices;
using System.Diagnostics;
using System.Reflection;
using System.Threading;
namespace RemasteredCE {
public static class J {
 public static Dictionary<string,object> Obj(object x){return (Dictionary<string,object>)x;}
 public static object[] Arr(object x){return (object[])x;}
 public static string S(Dictionary<string,object> d,string k){return Convert.ToString(d[k]);}
 public static long N(Dictionary<string,object> d,string k){return Convert.ToInt64(d[k]);}
 public static byte[] B(Dictionary<string,object> d,string k){return Convert.FromBase64String(S(d,k));}
 public static JavaScriptSerializer Json(){return new JavaScriptSerializer{MaxJsonLength=32*1024*1024,RecursionLimit=100};}
 public static Dictionary<string,object> Parse(string s){return Obj(Json().DeserializeObject(s));}
}
public sealed class Release : IDisposable {
 public Dictionary<string,object> Manifest,Helper;
 public byte[] Launcher;
 public string PackageHash;
 public static byte[] Resource(string name){using(var s=Assembly.GetExecutingAssembly().GetManifestResourceStream(name)){if(s==null)throw new InvalidDataException("Missing application resource: "+name);using(var m=new MemoryStream()){s.CopyTo(m);return m.ToArray();}}}
 public static Release Load(string path){
  byte[] bytes=String.IsNullOrEmpty(path)?Resource("release"):File.ReadAllBytes(path);
  if(bytes.Length>64*1024*1024 || bytes.Length<16 || Encoding.ASCII.GetString(bytes,0,8)!="RCEPKG01")throw new InvalidDataException("This is not a supported Remastered CE package.");
  int siglen=BitConverter.ToInt32(bytes,8);if(siglen<256 || siglen>1024 || bytes.Length<=12+siglen)throw new InvalidDataException("Invalid package signature length.");
  byte[] sig=new byte[siglen],zip=new byte[bytes.Length-12-siglen];Buffer.BlockCopy(bytes,12,sig,0,siglen);Buffer.BlockCopy(bytes,12+siglen,zip,0,zip.Length);
  using(var rsa=new RSACryptoServiceProvider()){rsa.FromXmlString(Encoding.UTF8.GetString(Resource("publicKey")));if(!rsa.VerifyData(zip,CryptoConfig.MapNameToOID("SHA256"),sig))throw new InvalidDataException("The update signature is invalid. Nothing was installed.");}
  var result=new Release();result.PackageHash=Engine.Hash(bytes);
  using(var archive=new ZipArchive(new MemoryStream(zip),ZipArchiveMode.Read)){
   result.Manifest=J.Parse(Encoding.UTF8.GetString(ReadEntry(archive,"manifest.json",32*1024*1024)));
   result.Helper=J.Parse(Encoding.UTF8.GetString(ReadEntry(archive,"helper.json",1024*1024)));
   result.Launcher=ReadEntry(archive,"launcher.exe",1024*1024);
  }
  if(J.N(result.Manifest,"schema")!=1 && J.N(result.Manifest,"schema")!=2)throw new InvalidDataException("This update requires a newer installer. Download the installer ZIP from the Remastered CE GitHub releases page.");
  if(result.Manifest.ContainsKey("minimumInstallerVersion") && ReleaseVersion.Parse(OnlineUpdates.AppVersion).CompareTo(ReleaseVersion.Parse(J.S(result.Manifest,"minimumInstallerVersion")))<0)throw new InvalidDataException("This release needs a newer installer. Download the latest installer ZIP from the Remastered CE GitHub releases page.");return result;
 }
 static byte[] ReadEntry(ZipArchive zip,string name,int limit){var e=zip.GetEntry(name);if(e==null || e.Length>limit)throw new InvalidDataException("Invalid package component: "+name);using(var s=e.Open())using(var m=new MemoryStream()){s.CopyTo(m);return m.ToArray();}}
 public void Dispose(){}
}
public static class Lz4 {
 [DllImport("kernel32",CharSet=CharSet.Unicode,SetLastError=true)] static extern IntPtr LoadLibraryW(string p);
 [DllImport("lz4.dll",CallingConvention=CallingConvention.Cdecl)] static extern int LZ4_decompress_safe(byte[] src,byte[] dst,int count,int capacity);
 [DllImport("lz4.dll",CallingConvention=CallingConvention.Cdecl)] static extern int LZ4_compressBound(int n);
 [DllImport("lz4.dll",CallingConvention=CallingConvention.Cdecl)] static extern int LZ4_compress_default(byte[] src,byte[] dst,int n,int capacity);
 [DllImport("lz4.dll",CallingConvention=CallingConvention.Cdecl)] static extern int LZ4_compress_HC(byte[] src,byte[] dst,int n,int capacity,int level);
 static bool ready;
 public static void Init(){if(ready)return;var data=Release.Resource("lz4");string root=Path.Combine(Path.GetTempPath(),"RemasteredCE-tools-"+Engine.Hash(data).Substring(0,16));Directory.CreateDirectory(root);string p=Path.Combine(root,"lz4.dll");if(!File.Exists(p)||Engine.FileHash(p)!=Engine.Hash(data))File.WriteAllBytes(p,data);if(LoadLibraryW(p)==IntPtr.Zero)throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());ready=true;}
 public static byte[] Decode(byte[] src,int size){Init();if(size<0||size>256*1024*1024)throw new InvalidDataException("Asset size exceeds limit.");var data=new byte[size];if(LZ4_decompress_safe(src,data,src.Length,size)!=size)throw new InvalidDataException("Asset decompression failed.");return data;}
 public static byte[] Encode(byte[] data,string codec,int level){if(codec=="raw")return data;Init();var dest=new byte[LZ4_compressBound(data.Length)];int n=codec=="fast"?LZ4_compress_default(data,dest,data.Length,dest.Length):LZ4_compress_HC(data,dest,data.Length,dest.Length,level);if(n<=0)throw new InvalidDataException("Asset compression failed.");Array.Resize(ref dest,n);return dest;}
}
public sealed class Engine {
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)]
 static extern bool CreateHardLinkW(string target,string source,IntPtr reserved);
 public string[] LinkBaseData(string ce,string stage){
  string sourceRoot=Under(ce,"data");NoLinks(sourceRoot);
  var linked=new List<string>();
  foreach(string source in Directory.EnumerateFiles(sourceRoot,"*",SearchOption.AllDirectories)){
   Cancel.ThrowIfCancellationRequested();NoLinks(Path.GetDirectoryName(source));RejectLinkedFile(source);
   string relative="data/"+source.Substring(sourceRoot.Length+1).Replace('\\','/');
   string target=Under(stage,relative);if(File.Exists(target))continue;
   Directory.CreateDirectory(Path.GetDirectoryName(target));
   if(!CreateHardLinkW(target,source,IntPtr.Zero))throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error(),"Unable to link required base game data: "+relative);
   linked.Add(relative);
  }
  return linked.ToArray();
 }
 public Action<string,int> Progress;
 public CancellationToken Cancel;
 public void Log(string s,int p){if(Progress!=null)Progress(s,p);Cancel.ThrowIfCancellationRequested();}
 public static string Hash(byte[] data){using(var sha=SHA256.Create())return BitConverter.ToString(sha.ComputeHash(data)).Replace("-","").ToLowerInvariant();}
 public static string FileHash(string p){using(var s=File.OpenRead(p))using(var sha=SHA256.Create())return BitConverter.ToString(sha.ComputeHash(s)).Replace("-","").ToLowerInvariant();}
 public static string Under(string root,string relative){if(Path.IsPathRooted(relative))throw new InvalidDataException("Absolute package paths are forbidden.");string r=Path.GetFullPath(root).TrimEnd(Path.DirectorySeparatorChar)+Path.DirectorySeparatorChar;string p=Path.GetFullPath(Path.Combine(r,relative.Replace('/',Path.DirectorySeparatorChar)));if(!p.StartsWith(r,StringComparison.OrdinalIgnoreCase))throw new InvalidDataException("Package path escapes its installation folder.");return p;}
 public static void NoLinks(string path){var d=new DirectoryInfo(Path.GetFullPath(path));while(d!=null){if(d.Exists && (d.Attributes&FileAttributes.ReparsePoint)!=0)throw new IOException("Linked installation folders are not supported: "+d.FullName);d=d.Parent;}}
 public static void GameClosed(){foreach(string n in new[]{"shogun2_complete_edition","RemasteredCE_Bootstrap","Launch_Remastered_CE"})if(Process.GetProcessesByName(n).Length>0)throw new IOException("Close CE and Remastered CE before installing or updating.");}
 static void RequireHash(string path,string expected){if(!File.Exists(path)||FileHash(path)!=expected)throw new InvalidDataException("Unsupported or modified source file: "+path+". This release needs the supported vanilla CE build; do not overwrite newer game files with old backups.");}
 public void Preflight(Release r,string ce,string legacy){
  NoLinks(ce);NoLinks(legacy);
  if(String.Equals(Path.GetFullPath(ce),Path.GetFullPath(legacy),StringComparison.OrdinalIgnoreCase))throw new IOException("Select separate CE and original Shogun 2 folders.");
  if(!File.Exists(Under(legacy,"Shogun2.exe")))throw new FileNotFoundException("Select the original Shogun 2 installation containing Shogun2.exe.");
  Log("Verifying CE executable…",0);RequireHash(Under(ce,"shogun2_complete_edition.exe"),J.S(r.Manifest,"ceExeSha256"));
  Log("Verifying vanilla CE engine…",2);RequireHash(Under(ce,"empire.retail.x64.dll"),J.S(r.Manifest,"engineSourceSha256"));
  if(J.N(r.Manifest,"schema")==2){Log("Verifying the locally installed NVIDIA DLSS runtime…",3);RequireHash(Under(ce,"nvngx_dlss.dll"),J.S(r.Manifest,"dlssRuntimeSha256"));}
  int i=0;foreach(object item in J.Arr(r.Manifest["files"])){var f=J.Obj(item);Log("Verifying vanilla "+J.S(f,"source")+"…",3+i*3);RequireHash(Under(ce,J.S(f,"source")),J.S(f,"sourceSha256"));i++;}
 }
 byte[] Source(Dictionary<string,object> s,string ce,string legacy){string root=J.S(s,"root")=="legacy"?legacy:ce;string file=Under(root,J.S(s,"file"));long off=J.N(s,"offset"),stored=J.N(s,"stored");if(off<0||stored<0||stored>256*1024*1024)throw new InvalidDataException("Invalid source range.");byte[] data=new byte[(int)stored];using(var stream=File.OpenRead(file)){if(off>stream.Length-stored)throw new InvalidDataException("Source archive version differs: "+file);stream.Position=off;ReadAll(stream,data);}
  if(Convert.ToBoolean(s["compressed"]))data=Lz4.Decode(data,(int)J.N(s,"size"));
  if(Hash(data)!=J.S(s,"sha256"))throw new InvalidDataException("An original asset does not match this release: "+J.S(s,"file")+". Check your original Shogun 2 installation.");return data;
 }
 static void ReadAll(Stream s,byte[] b){int p=0;while(p<b.Length){int n=s.Read(b,p,b.Length-p);if(n==0)throw new EndOfStreamException();p+=n;}}
 public static byte[] Transform(byte[] input,object[] operations){if(operations.Length==0)return input;using(var output=new MemoryStream()){foreach(object obj in operations){var op=J.Obj(obj);if(op.ContainsKey("data")){byte[] d=J.B(op,"data");output.Write(d,0,d.Length);}else{long off=J.N(op,"copy"),len=J.N(op,"length");if(off<0||len<0||off>input.Length-len)throw new InvalidDataException("Invalid source-copy instruction.");output.Write(input,(int)off,(int)len);}if(output.Length>256*1024*1024)throw new InvalidDataException("Asset output exceeds limit.");}return output.ToArray();}}
 static void ApplyWrites(Stream file,object[] ops){foreach(object item in ops){var op=J.Obj(item);long off=J.N(op,"offset");byte[] b=J.B(op,"data");if(off<0||off>file.Length-b.Length)throw new InvalidDataException("Patch range is outside the source file.");file.Position=off;file.Write(b,0,b.Length);}}
 // Move the original payload backwards in bounded chunks when new index entries need space.
 // Only operates on the private staging copy, before applying signed metadata and asset writes.
 public static void ShiftPackBody(Stream stream,long start,long shift,long originalLength){
  if(start<32 || start>originalLength || shift<=0 || shift>16*1024*1024 || originalLength>stream.Length-shift)throw new InvalidDataException("Invalid pack index expansion.");
  byte[] buffer=new byte[4*1024*1024];long end=originalLength;
  while(end>start){int count=(int)Math.Min(buffer.Length,end-start);long offset=end-count;stream.Position=offset;ReadAll(stream,buffer,count);stream.Position=offset+shift;stream.Write(buffer,0,count);end=offset;}
  Array.Clear(buffer,0,buffer.Length);stream.Position=start;long remaining=shift;
  while(remaining>0){int count=(int)Math.Min(buffer.Length,remaining);stream.Write(buffer,0,count);remaining-=count;}
 }
 static void ReadAll(Stream stream,byte[] buffer,int count){int done=0;while(done<count){int n=stream.Read(buffer,done,count-done);if(n==0)throw new EndOfStreamException();done+=n;}}
 public void Build(Release release,string ce,string legacy,string stage){
  Preflight(release,ce,legacy);NoLinks(stage);Directory.CreateDirectory(stage);var sources=J.Arr(release.Manifest["sources"]).Select(J.Obj).ToDictionary(x=>J.S(x,"id"));int done=0,total=J.Arr(release.Manifest["files"]).Select(J.Obj).Sum(x=>J.Arr(x["assets"]).Length);
  foreach(object item in J.Arr(release.Manifest["files"])){var f=J.Obj(item);string relative=J.S(f,"destination");if(!new[]{"data/data.pack","data/shaders.pack","data/bp_orig.pack","data/web_content.pack","data/local_global.pack","data/models.pack","data/audio.pack","data/movies.pack"}.Contains(relative))throw new InvalidDataException("Unsupported destination pack.");string output=Under(stage,relative);Directory.CreateDirectory(Path.GetDirectoryName(output));Log("Copying "+relative+"…",17+(int)(65L*done/Math.Max(1,total)));CopyFile(Under(ce,J.S(f,"source")),output);
   using(var stream=new FileStream(output,FileMode.Open,FileAccess.ReadWrite,FileShare.None)){long originalLength=stream.Length;stream.SetLength(J.N(f,"length"));if(f.ContainsKey("sourceBodyShift"))ShiftPackBody(stream,J.N(f,"sourceBodyOffset"),J.N(f,"sourceBodyShift"),originalLength);ApplyWrites(stream,J.Arr(f["metadata"]));foreach(object ao in J.Arr(f["assets"])){Cancel.ThrowIfCancellationRequested();var a=J.Obj(ao);string sid=J.S(a,"source");byte[] input=String.IsNullOrEmpty(sid)?new byte[0]:Source(sources[sid],ce,legacy);byte[] data=Transform(input,J.Arr(a["operations"]));if(data.Length!=J.N(a,"size")||Hash(data)!=J.S(a,"sha256"))throw new InvalidDataException("Patched asset failed verification: "+J.S(a,"path"));byte[] encoded=Lz4.Encode(data,J.S(a,"codec"),(int)J.N(a,"level"));if(encoded.Length!=J.N(a,"stored")||Hash(encoded)!=J.S(a,"encodedSha256"))throw new InvalidDataException("Encoded asset failed verification: "+J.S(a,"path"));long off=J.N(a,"offset");if(off<0||off>stream.Length-encoded.Length)throw new InvalidDataException("Asset output range is invalid.");stream.Position=off;stream.Write(encoded,0,encoded.Length);done++;if(done%40==0)Log("Building assets: "+done+" / "+total,17+(int)(65L*done/Math.Max(1,total)));}stream.Flush(true);}
   Log("Verifying completed "+relative+"…",83);RequireHash(output,J.S(f,"sha256"));
  }
  Log("Building the separate Remastered engine…",88);byte[] dll=File.ReadAllBytes(Under(ce,"empire.retail.x64.dll"));using(var stream=new MemoryStream(dll,true))ApplyWrites(stream,J.Arr(release.Manifest["enginePatches"]));if(Hash(dll)!=J.S(release.Manifest,"engineEditedSha256"))throw new InvalidDataException("Engine modifications failed verification.");dll=PePatch.Inject(dll,release.Helper);if(Hash(dll)!=J.S(release.Manifest,"engineFinalSha256"))throw new InvalidDataException("Engine path redirection failed verification.");File.WriteAllBytes(Under(stage,"CE.dll"),dll);
  byte[] exe=File.ReadAllBytes(Under(ce,"shogun2_complete_edition.exe"));byte[] expected=Encoding.ASCII.GetBytes("Empire.Retail.x64.dll\0"),replacement=Encoding.ASCII.GetBytes("RemasteredCE\\CE.dll\0");const int pathOffset=0xe5f8;if(!exe.Skip(pathOffset).Take(expected.Length).SequenceEqual(expected))throw new InvalidDataException("Unsupported bootstrap DLL-path layout.");Array.Clear(exe,pathOffset,expected.Length);Buffer.BlockCopy(replacement,0,exe,pathOffset,replacement.Length);File.WriteAllBytes(Under(stage,"RemasteredCE_Bootstrap.exe"),exe);File.WriteAllBytes(Under(stage,"Launch_Remastered_CE.exe"),release.Launcher);
  bool dlssLayout=J.N(release.Manifest,"schema")==2;
  if(dlssLayout){
   // NGX availability was verified with the original executable name and a local adjacent runtime.
   Array.Clear(exe,pathOffset,expected.Length);replacement=Encoding.ASCII.GetBytes("CE.dll\0");Buffer.BlockCopy(replacement,0,exe,pathOffset,replacement.Length);
   File.WriteAllBytes(Under(stage,"shogun2_complete_edition.exe"),exe);Log("Copying the local NVIDIA DLSS runtime…",92);
   CopyFile(Under(ce,"nvngx_dlss.dll"),Under(stage,"nvngx_dlss.dll"));RequireHash(Under(stage,"nvngx_dlss.dll"),J.S(release.Manifest,"dlssRuntimeSha256"));
  }
  var state=new Dictionary<string,object>{{"schema",1},{"version",J.S(release.Manifest,"version")},{"packageSha256",release.PackageHash},{"ceBuild",J.S(release.Manifest,"ceBuild")},{"installedUtc",DateTime.UtcNow.ToString("o")},{"engineHash",Hash(dll)},{"files",J.Arr(release.Manifest["files"]).Select(J.Obj).Select(x=>new Dictionary<string,object>{{"file",J.S(x,"destination")},{"sha256",J.S(x,"sha256")}}).ToArray()}};
  if(dlssLayout){state["layoutVersion"]=2;Log("Linking required local base game data…",93);state["baseDataFiles"]=LinkBaseData(ce,stage);}
  File.WriteAllText(Under(stage,"install-state.json"),J.Json().Serialize(state));Log("All generated files verified.",94);
 }
 void CopyFile(string source,string target){byte[] b=new byte[8*1024*1024];using(var input=File.OpenRead(source))using(var output=new FileStream(target,FileMode.CreateNew,FileAccess.Write,FileShare.None)){int n;while((n=input.Read(b,0,b.Length))>0){Cancel.ThrowIfCancellationRequested();output.Write(b,0,n);}output.Flush(true);}}

 public static bool ApplyUnitCameraPreference(string path){
  if(!File.Exists(path))return false;
  byte[] original=File.ReadAllBytes(path);Encoding encoding;
  if(original.Length>=2 && original[0]==255 && original[1]==254)encoding=new UnicodeEncoding(false,true,true);
  else if(original.Length>=2 && original[0]==254 && original[1]==255)encoding=new UnicodeEncoding(true,true,true);
  else encoding=new UTF8Encoding(original.Length>=3 && original[0]==239 && original[1]==187 && original[2]==191,true);
  byte[] preamble=encoding.GetPreamble();int skip=preamble.Length;
  string text=encoding.GetString(original,skip,original.Length-skip);
  var expression=new System.Text.RegularExpressions.Regex(@"(?m)^([ \t]*proximity_fading[ \t]+)(?:true|false)([ \t]*;[^\r\n]*)(?=\r?$)");
  // Preserve the player's saved toggle choice during installs and updates.
  if(expression.IsMatch(text))return false;
  string newline=text.Contains("\r\n")?"\r\n":"\n";
  string updated=text+(text.Length>0 && !text.EndsWith("\n")?newline:"")+"proximity_fading false;"+newline;
  if(updated==text)return false;
  string backup=path+".remasteredce-unit-fade.bak";
  if(!File.Exists(backup))File.WriteAllBytes(backup,original);
  string temporary=path+".remasteredce-"+Guid.NewGuid().ToString("N")+".tmp";
  try{File.WriteAllBytes(temporary,preamble.Concat(encoding.GetBytes(updated)).ToArray());File.Replace(temporary,path,null);}
  finally{if(File.Exists(temporary))File.Delete(temporary);}
  return true;
 }
 void ApplyReleasePreferences(Release release){
  if(!release.Manifest.ContainsKey("disableUnitProximityFading") || !Convert.ToBoolean(release.Manifest["disableUnitProximityFading"]))return;
  string preferences=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),@"The Creative Assembly\Shogun2CompleteEdition\Steam\scripts\preferences.script.txt");
  try{if(ApplyUnitCameraPreference(preferences))Log("Disabled near-camera unit fading; other preferences preserved. A preference backup was saved.",99);}
  catch(IOException){Log("Installed successfully. Unit camera preference could not be updated; set proximity_fading false manually.",99);}
  catch(UnauthorizedAccessException){Log("Installed successfully. Unit camera preference could not be updated; set proximity_fading false manually.",99);}
  catch(DecoderFallbackException){Log("Installed successfully. Preference encoding was not recognized; set proximity_fading false manually.",99);}
 }

 public void Install(Release r,string ce,string legacy){
  ce=Path.GetFullPath(ce);NoLinks(ce);GameClosed();string live=Under(ce,"RemasteredCE");NoLinks(live);
  using(var installLock=new FileStream(Under(ce,".remastered-install.lock"),FileMode.OpenOrCreate,FileAccess.ReadWrite,FileShare.None)){
   string stamp=DateTime.UtcNow.ToString("yyyyMMdd_HHmmss")+"_"+Guid.NewGuid().ToString("N").Substring(0,6);string stage=Under(ce,"RemasteredCE.staging_"+stamp);string previous=Under(ce,"RemasteredCE.previous_"+stamp);bool retainStage=false;
   try{
    var drive=new DriveInfo(Path.GetPathRoot(ce));long needed=J.Arr(r.Manifest["files"]).Select(J.Obj).Sum(f=>J.N(f,"length"))+512L*1024*1024;if(drive.AvailableFreeSpace<needed)throw new IOException("Not enough free disk space to stage this update safely.");
    Directory.CreateDirectory(stage);Build(r,ce,legacy,stage);Cancel.ThrowIfCancellationRequested();GameClosed();Log("Publishing verified Remastered files...",96);PublishVerified(stage,ce,previous);ApplyReleasePreferences(r);Log("Installed "+J.S(r.Manifest,"version")+". Vanilla game files were not replaced.",100);
   }catch(AggregateException){retainStage=true;throw;}finally{if(!retainStage && Directory.Exists(stage)){NoLinks(stage);if(!Path.GetFileName(stage).StartsWith("RemasteredCE.staging_",StringComparison.Ordinal))throw new IOException("Invalid staging cleanup target.");Directory.Delete(stage,true);}}
  }
 }
 public void Uninstall(string ce){
  ce=Path.GetFullPath(ce);NoLinks(ce);GameClosed();string live=Under(ce,"RemasteredCE");NoLinks(live);
  if(!File.Exists(Under(ce,"shogun2_complete_edition.exe")))throw new IOException("Select the Complete Edition game folder first.");
  string record=Under(live,"install-state.json");
  if(!File.Exists(record))throw new IOException("No installer-managed Remastered CE installation was found in this folder.");
  using(var installLock=new FileStream(Under(ce,".remastered-install.lock"),FileMode.OpenOrCreate,FileAccess.ReadWrite,FileShare.None)){
   RejectLinkedFile(record);var installed=J.Parse(File.ReadAllText(record));
   var packs=new[]{"data/data.pack","data/shaders.pack","data/bp_orig.pack","data/web_content.pack","data/local_global.pack","data/models.pack","data/audio.pack","data/movies.pack"};
   if(J.N(installed,"schema")!=1 || !installed.ContainsKey("engineHash"))throw new InvalidDataException("Unrecognized installation record; nothing was removed.");
   var recorded=J.Arr(installed["files"]).Select(J.Obj).Select(x=>J.S(x,"file")).ToArray();
   if(recorded.Length<4 || recorded.Length>packs.Length || !new HashSet<string>(recorded,StringComparer.Ordinal).SetEquals(packs.Take(recorded.Length)))throw new InvalidDataException("Unexpected installed file paths; nothing was removed.");
   packs=recorded;
   var owned=new List<string>();foreach(string pack in packs)owned.Add(Under(live,pack));owned.Add(Under(live,"CE.dll"));
   if(installed.ContainsKey("layoutVersion")){
    if(J.N(installed,"layoutVersion")!=2)throw new InvalidDataException("Unrecognized installation layout; nothing was removed.");
    owned.Add(Under(live,"shogun2_complete_edition.exe"));owned.Add(Under(live,"nvngx_dlss.dll"));
   }
   if(installed.ContainsKey("baseDataFiles"))foreach(object item in J.Arr(installed["baseDataFiles"])){
    string relative=Convert.ToString(item);
    if(!relative.StartsWith("data/",StringComparison.Ordinal) || packs.Contains(relative))throw new InvalidDataException("Unexpected base data path; nothing was removed.");
    owned.Add(Under(live,relative));
   }
   foreach(string name in new[]{"Launch_Remastered_CE.exe","RemasteredCE_Bootstrap.exe"}){
    string local=Under(live,name),root=Under(ce,name),backup=Under(live,"previous-launchers/"+name);
    RejectLinkedFile(local);RejectLinkedFile(root);RejectLinkedFile(backup);NoLinks(Path.GetDirectoryName(backup));
    if(File.Exists(root)){
     if(!File.Exists(local) || FileHash(root)!=FileHash(local))throw new IOException("The launcher differs from the installed Remastered copy; nothing was removed: "+name);
     owned.Add(root);
    }
    owned.Add(local);owned.Add(backup);
   }
   foreach(string path in owned){NoLinks(Path.GetDirectoryName(path));RejectLinkedFile(path);}
   Log("Removing the active Remastered installation...",10);GameClosed();
   // Remove only our named files. Keep the record until file removal succeeds, allowing retries.
   foreach(string path in owned)if(File.Exists(path))File.Delete(path);
   File.Delete(record);
   string dataFolder=Under(live,"data");
   if(Directory.Exists(dataFolder))foreach(string folder in Directory.EnumerateDirectories(dataFolder,"*",SearchOption.AllDirectories).OrderByDescending(x=>x.Length))if(!Directory.EnumerateFileSystemEntries(folder).Any())Directory.Delete(folder);
   foreach(string folder in new[]{Under(live,"data"),Under(live,"previous-launchers"),live})if(Directory.Exists(folder) && !Directory.EnumerateFileSystemEntries(folder).Any())Directory.Delete(folder);
   Log(Directory.Exists(live)?"Uninstalled. Unrecognized files in RemasteredCE were retained.":"Uninstalled Remastered CE. Vanilla files and previous-version backups were retained.",100);
  }
 }
 static void RejectLinkedFile(string path){if(File.Exists(path) && (File.GetAttributes(path)&FileAttributes.ReparsePoint)!=0)throw new IOException("Linked installed files are not supported: "+path);}
 public static void PublishVerified(string stage,string ce,string previous){
  string live=Under(ce,"RemasteredCE");NoLinks(stage);NoLinks(live);NoLinks(previous);
  if(!Path.GetFullPath(stage).StartsWith(Path.GetFullPath(ce).TrimEnd('\\')+"\\",StringComparison.OrdinalIgnoreCase)||!Path.GetFileName(stage).StartsWith("RemasteredCE.staging_",StringComparison.Ordinal))throw new IOException("Invalid publication staging folder.");
  var existed=new HashSet<string>();var replaced=new List<string>();bool moved=false,published=false;
  Directory.CreateDirectory(Under(stage,"previous-launchers"));foreach(string name in new[]{"Launch_Remastered_CE.exe","RemasteredCE_Bootstrap.exe"})if(File.Exists(Under(ce,name))){File.Copy(Under(ce,name),Under(stage,"previous-launchers/"+name),true);existed.Add(name);}
  try{
   if(Directory.Exists(live)){Directory.Move(live,previous);moved=true;}Directory.Move(stage,live);published=true;
   foreach(string name in new[]{"RemasteredCE_Bootstrap.exe","Launch_Remastered_CE.exe"}){string temp=Under(ce,name+".installing");File.Copy(Under(live,name),temp,true);if(File.Exists(Under(ce,name)))File.Replace(temp,Under(ce,name),null);else File.Move(temp,Under(ce,name));replaced.Add(name);}
  }catch(Exception original){
   var failures=new List<Exception>();failures.Add(original);
   foreach(string name in replaced.AsEnumerable().Reverse()){try{if(existed.Contains(name))File.Copy(Under(live,"previous-launchers/"+name),Under(ce,name),true);else File.Delete(Under(ce,name));}catch(Exception ex){failures.Add(ex);}}
   try{if(published)Directory.Move(live,stage);if(moved)Directory.Move(previous,live);}catch(Exception ex){failures.Add(ex);}
   if(failures.Count>1)throw new AggregateException("Update rollback needs attention. Keep the game closed; previous files have been retained.",failures);throw;
  }finally{foreach(string name in new[]{"RemasteredCE_Bootstrap.exe","Launch_Remastered_CE.exe"}){string temp=Under(ce,name+".installing");if(File.Exists(temp))File.Delete(temp);}}
 }
}
public sealed class PePatch {
 static ushort U16(byte[] b,int o){return BitConverter.ToUInt16(b,o);}static uint U32(byte[] b,int o){return BitConverter.ToUInt32(b,o);}static void W16(byte[] b,int o,int v){Buffer.BlockCopy(BitConverter.GetBytes((ushort)v),0,b,o,2);}static void W32(byte[] b,int o,long v){Buffer.BlockCopy(BitConverter.GetBytes(unchecked((uint)v)),0,b,o,4);}static int Align(int v,int a){return checked((v+a-1)/a*a);}
 sealed class Info {public int Nt,Opt,Count,Table,FileAlign,SectionAlign;public int[] Sections;public Info(byte[] b){Nt=(int)U32(b,0x3c);Opt=Nt+24;Count=U16(b,Nt+6);Table=Opt+U16(b,Nt+20);FileAlign=(int)U32(b,Opt+36);SectionAlign=(int)U32(b,Opt+32);Sections=Enumerable.Range(0,Count).Select(i=>Table+i*40).ToArray();}public int Offset(byte[] b,int rva){foreach(int s in Sections){int va=(int)U32(b,s+12),size=Math.Max((int)U32(b,s+8),(int)U32(b,s+16));if(rva>=va && rva<va+size)return checked((int)U32(b,s+20)+rva-va);}if(rva<(int)U32(b,Opt+60))return rva;throw new InvalidDataException("Invalid PE address.");}}
 public static byte[] Inject(byte[] input,Dictionary<string,object> helper){
  byte[] b=(byte[])input.Clone();var p=new Info(b);int oldrva=(int)J.N(helper,"rva");int newrva=Align(p.Sections.Max(s=>checked((int)U32(b,s+12)+(int)U32(b,s+8))),p.SectionAlign);int delta=newrva-oldrva;byte[] payload=J.B(helper,"payload");foreach(object fix in J.Arr(helper["fixups"])){int o=Convert.ToInt32(fix);W32(payload,o,unchecked((int)U32(payload,o)-delta));}
  int exdir=p.Opt+112+3*8,exrva=(int)U32(b,exdir),exsize=(int)U32(b,exdir+4),exoff=p.Offset(b,exrva);int pdata=Align(payload.Length,4);object[] unwind=J.Arr(helper["unwind"]);byte[] content=new byte[pdata+exsize+unwind.Length*12];Buffer.BlockCopy(payload,0,content,0,payload.Length);Buffer.BlockCopy(b,exoff,content,pdata,exsize);int dest=pdata+exsize;foreach(object row in unwind){object[] values=J.Arr(row);for(int i=0;i<3;i++)W32(content,dest+i*4,Convert.ToInt32(values[i])+delta);dest+=12;}
  int header=p.Table+p.Count*40,first=p.Sections.Min(s=>(int)U32(b,s+20));if(header+40>first){int shift=p.FileAlign;byte[] expanded=new byte[b.Length+shift];Buffer.BlockCopy(b,0,expanded,0,first);Buffer.BlockCopy(b,first,expanded,first+shift,b.Length-first);int debugdir=p.Opt+112+6*8,drva=(int)U32(b,debugdir),dsize=(int)U32(b,debugdir+4);if(drva!=0){int d=p.Offset(b,drva);for(int i=0;i+28<=dsize;i+=28)if(U32(b,d+i+24)!=0)W32(expanded,d+i+24+shift,U32(b,d+i+24)+shift);}
   foreach(int s in p.Sections)W32(expanded,s+20,U32(b,s+20)+shift);int secdir=p.Opt+112+4*8;if(U32(b,secdir)!=0)W32(expanded,secdir,U32(b,secdir)+shift);W32(expanded,p.Opt+60,U32(b,p.Opt+60)+shift);b=expanded;
  }
  p=new Info(b);int text=p.Sections.First(s=>Encoding.ASCII.GetString(b,s,5)==".text"),file=(int)U32(b,text+20),va=(int)U32(b,text+12),sizeText=(int)U32(b,text+16),wrapper=newrva+(int)J.N(helper,"entry")-oldrva,count=0;
  for(int i=0;i+6<sizeText;i++){int at=file+i;if(b[at]!=0xff||b[at+1]!=0x15)continue;int site=va+i;if(site+6+unchecked((int)U32(b,at+2))!=0x215a530)continue;b[at]=0xe8;W32(b,at+1,wrapper-(site+5));b[at+5]=0x90;count++;}if(count!=25)throw new InvalidDataException("Unsupported engine file-open layout.");
  int newfile=Align(b.Length,p.FileAlign),rawsize=Align(content.Length,p.FileAlign);Array.Resize(ref b,newfile+rawsize);Buffer.BlockCopy(content,0,b,newfile,content.Length);byte[] name=Encoding.ASCII.GetBytes(".cepath\0");Buffer.BlockCopy(name,0,b,header,name.Length);W32(b,header+8,content.Length);W32(b,header+12,newrva);W32(b,header+16,rawsize);W32(b,header+20,newfile);W32(b,header+36,0x60000020);W16(b,p.Nt+6,p.Count+1);W32(b,p.Opt+56,Align(newrva+content.Length,p.SectionAlign));W32(b,p.Opt+4,U32(b,p.Opt+4)+rawsize);W32(b,exdir,newrva+pdata);W32(b,exdir+4,exsize+unwind.Length*12);int checksum=p.Opt+64;W32(b,checksum,0);ulong sum=0;for(int i=0;i<b.Length;i+=2){sum+=(uint)(b[i]|((i+1<b.Length?b[i+1]:0)<<8));sum=(sum&0xffff)+(sum>>16);}sum=(sum&0xffff)+(sum>>16);W32(b,checksum,(long)(sum&0xffff)+b.Length);return b;
 }
}
}
