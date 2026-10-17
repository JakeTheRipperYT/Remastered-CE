using System;
using System.IO;
using System.Linq;
using System.Text;
using System.Drawing;
using System.Diagnostics;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;
using System.Collections.Generic;
using System.Text.RegularExpressions;
using Microsoft.Win32;
[assembly: System.Runtime.Versioning.TargetFramework(".NETFramework,Version=v4.8")]
[assembly: System.Reflection.AssemblyCompany("JakeTheRipper")]
[assembly: System.Reflection.AssemblyCopyright("JakeTheRipper")]
[assembly: System.Reflection.AssemblyProduct("Remastered CE")]
[assembly: System.Reflection.AssemblyTitle("Remastered CE by JakeTheRipper")]
namespace RemasteredCE {
static class Program {
 [STAThread] static int Main(string[] args){
  if(args.Length>0){try{
   if(args[0]=="--preview" && args.Length==2){Application.EnableVisualStyles();using(var form=new MainForm(true)){form.Show();Application.DoEvents();using(var bitmap=new Bitmap(form.Width,form.Height)){form.DrawToBitmap(bitmap,new Rectangle(0,0,form.Width,form.Height));bitmap.Save(args[1]);}}return 0;}
   if(args[0]=="--self-test"){SelfTests.Run(args.Length>1?args[1]:"installer-selftest.txt");return 0;}
   if(args[0]=="--build-only" && args.Length==5){string ce=args[1],legacy=args[2],dest=Path.GetFullPath(args[4]);if(Directory.Exists(dest))throw new IOException("Build-only output already exists.");string log=dest+".log";using(var release=Release.Load(args[3])){var engine=new Engine{Progress=(s,p)=>File.AppendAllText(log,p+"% "+s+Environment.NewLine)};engine.Build(release,ce,legacy,dest);}File.AppendAllText(log,"SUCCESS"+Environment.NewLine);return 0;}
   if(args[0]=="--check-online" && args.Length==2){var latest=OnlineUpdates.Latest(CancellationToken.None);string file=OnlineUpdates.Download(latest,args[1],CancellationToken.None,null);Console.WriteLine("Verified online release "+latest.Version);File.WriteAllText(Path.Combine(args[1],"online-check.txt"),latest.Version+Environment.NewLine+Engine.FileHash(file));return 0;}
   throw new ArgumentException("Unknown installer command.");
  }catch(Exception ex){string log=args.Length==5?Path.GetFullPath(args[4])+".log":"installer-error.txt";File.AppendAllText(log,"FAILED: "+ex+Environment.NewLine);return 1;}}
  Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);Application.Run(new MainForm());return 0;
 }
}
public sealed class MainForm : Form {
 readonly TextBox ce=new TextBox(),legacy=new TextBox(),package=new TextBox(),log=new TextBox();
 readonly Button install=new Button(),launch=new Button(),choosePackage=new Button(),cancel=new Button(),uninstall=new Button(),github=new Button();
 readonly ProgressBar progress=new ProgressBar();readonly Label state=new Label();CancellationTokenSource cancellation;bool busy;
 readonly string settings=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"RemasteredCE","installer-settings.json");
 public MainForm(bool preview=false){
  Icon=Icon.ExtractAssociatedIcon(Application.ExecutablePath);Text="Remastered CE";ClientSize=new Size(810,650);MinimumSize=new Size(820,690);StartPosition=FormStartPosition.CenterScreen;Font=new Font("Segoe UI",10);BackColor=Color.FromArgb(23,27,30);ForeColor=Color.FromArgb(235,239,240);AutoScaleMode=AutoScaleMode.Dpi;
  var title=new Label{Text="REMASTERED CE",Font=new Font("Segoe UI Semibold",23),AutoSize=true,Location=new Point(28,24)};Controls.Add(title);
  Controls.Add(new Label{Text="By JakeTheRipper · Preview 0.1.8",AutoSize=true,ForeColor=Color.FromArgb(158,176,181),Location=new Point(31,73)});
  FolderRow("Complete Edition installation",ce,122);FolderRow("Original Shogun 2 installation",legacy,204);
  Controls.Add(new Label{Text="Release package",AutoSize=true,Location=new Point(30,286)});StyleBox(package);package.Location=new Point(30,312);package.Size=new Size(505,29);package.ReadOnly=true;package.Text="GitHub — latest release";Controls.Add(package);
  ButtonStyle(github,"GitHub",new Rectangle(547,310,108,33));github.Click+=(s,e)=>{package.Tag=null;package.Text="GitHub — latest release";};
  ButtonStyle(choosePackage,"Offline…",new Rectangle(667,310,113,33));
  var localMenu=new ContextMenuStrip();localMenu.Items.Add("Choose a downloaded .rce file…",null,(s,e)=>{using(var dialog=new OpenFileDialog{Filter="Remastered CE release (*.rce)|*.rce",Title="Choose a signed Remastered CE update"})if(dialog.ShowDialog()==DialogResult.OK){try{using(var r=Release.Load(dialog.FileName)){package.Tag=dialog.FileName;package.Text=Path.GetFileName(dialog.FileName);Append("Selected "+J.S(r.Manifest,"version")+"; signature verified.");}}catch(Exception ex){ShowError(ex);}}});
  localMenu.Items.Add("Use included release (offline)",null,(s,e)=>{package.Tag=":embedded";package.Text="Included release (offline)";});choosePackage.Click+=(s,e)=>localMenu.Show(choosePackage,new Point(0,choosePackage.Height));

  ButtonStyle(install,"Install / Update Remastered CE",new Rectangle(30,367,325,47));install.BackColor=Color.FromArgb(49,117,98);install.Click+=async(s,e)=>await Install();
  ButtonStyle(launch,"Launch Remastered CE",new Rectangle(369,367,260,47));launch.Click+=(s,e)=>{try{string file=Engine.Under(ce.Text,"Launch_Remastered_CE.exe");if(!File.Exists(file))throw new FileNotFoundException("Install Remastered CE first.");Process.Start(new ProcessStartInfo(file){WorkingDirectory=Path.GetFullPath(ce.Text),UseShellExecute=true});}catch(Exception ex){ShowError(ex);}};
  ButtonStyle(cancel,"Cancel",new Rectangle(643,367,137,47));cancel.Enabled=false;cancel.Click+=(s,e)=>{if(cancellation!=null)cancellation.Cancel();};
  state.Text="Vanilla game files stay untouched. Both games must be installed.";state.AutoSize=false;state.Location=new Point(30,429);state.Size=new Size(520,42);state.ForeColor=Color.FromArgb(158,176,181);Controls.Add(state);
  ButtonStyle(uninstall,"Uninstall Remastered CE",new Rectangle(562,429,218,36));uninstall.Click+=async(s,e)=>await Uninstall();
  progress.Location=new Point(30,478);progress.Size=new Size(750,9);Controls.Add(progress);
  StyleBox(log);log.Multiline=true;log.ReadOnly=true;log.ScrollBars=ScrollBars.Vertical;log.Location=new Point(30,503);log.Size=new Size(750,115);log.Anchor=AnchorStyles.Left|AnchorStyles.Right|AnchorStyles.Bottom|AnchorStyles.Top;Controls.Add(log);
  ce.Text=FindGame("Shogun 2 Complete Edition","shogun2_complete_edition.exe");legacy.Text=FindGame("Total War SHOGUN 2","Shogun2.exe");LoadSettings();if(preview){ce.Text=@"C:\Users\JakeTheRipper\Games\Shogun 2 Complete Edition";legacy.Text=@"C:\Users\JakeTheRipper\Games\Total War SHOGUN 2";}
  using(var r=Release.Load(null))Append("Included release "+J.S(r.Manifest,"version")+". Source assets are extracted locally; no complete game files are included.");
  FormClosing+=(s,e)=>{if(busy){e.Cancel=true;MessageBox.Show(this,"Wait for the current operation to finish before closing.",Text,MessageBoxButtons.OK,MessageBoxIcon.Information);}};
 }
 void FolderRow(string label,TextBox box,int y){Controls.Add(new Label{Text=label,AutoSize=true,Location=new Point(30,y)});StyleBox(box);box.Location=new Point(30,y+27);box.Size=new Size(625,29);Controls.Add(box);var browse=new Button();ButtonStyle(browse,"Browse…",new Rectangle(667,y+25,113,33));browse.Click+=(s,e)=>{using(var dialog=new FolderBrowserDialog{Description=label,SelectedPath=Directory.Exists(box.Text)?box.Text:""})if(dialog.ShowDialog()==DialogResult.OK)box.Text=dialog.SelectedPath;};}
 void ButtonStyle(Button b,string text,Rectangle bounds){b.Text=text;b.Bounds=bounds;b.FlatStyle=FlatStyle.Flat;b.FlatAppearance.BorderColor=Color.FromArgb(72,85,91);b.BackColor=Color.FromArgb(40,48,53);b.ForeColor=ForeColor;Controls.Add(b);}
 void StyleBox(TextBox t){t.BackColor=Color.FromArgb(32,39,43);t.ForeColor=ForeColor;t.BorderStyle=BorderStyle.FixedSingle;}
 void Append(string s){log.AppendText(DateTime.Now.ToString("HH:mm:ss")+"  "+s+Environment.NewLine);}
 void ShowError(Exception ex){string message=ex is UnauthorizedAccessException?"Windows denied access to the selected folder. Close the game and, if this folder requires it, run this installer as administrator.":ex.Message;Append(message);MessageBox.Show(this,message,Text,MessageBoxButtons.OK,MessageBoxIcon.Warning);}
 async Task Install(){
  if(busy)return;string cePath=ce.Text.Trim(),legacyPath=legacy.Text.Trim(),pkg=package.Tag as string;
  if(!Directory.Exists(cePath)||!Directory.Exists(legacyPath)){ShowError(new IOException("Choose both installed game folders first."));return;}
  busy=true;uninstall.Enabled=false;install.Enabled=false;launch.Enabled=false;choosePackage.Enabled=false;github.Enabled=false;ce.ReadOnly=true;legacy.ReadOnly=true;cancel.Enabled=true;cancellation=new CancellationTokenSource();progress.Value=0;
  try{SaveSettings();
   if(pkg==null){
    state.Text="Checking GitHub for the latest Remastered CE release...";Append(state.Text);
    var latest=await Task.Run(()=>OnlineUpdates.Latest(cancellation.Token));Append("Latest published release: "+latest.Version);
    string installedRecord=Engine.Under(cePath,"RemasteredCE/install-state.json");
    if(File.Exists(installedRecord)){
     var current=J.Parse(File.ReadAllText(installedRecord));string version=J.S(current,"version");
     if(!OnlineUpdates.NeedsUpdate(version,latest.Version)){state.Text="Up to date · "+version;Append("No newer release is available. Your installed files were kept.");return;}
    }
    state.Text="Downloading Remastered CE "+latest.Version+"...";
    var downloadProgress=new Progress<Tuple<long,long>>(v=>{state.Text="Downloading "+latest.Version+" · "+(v.Item1/1024)+" KB";progress.Value=v.Item2>0?(int)Math.Min(100,v.Item1*100/v.Item2):0;});
    string folder=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"RemasteredCE","downloads");
    pkg=await Task.Run(()=>OnlineUpdates.Download(latest,folder,cancellation.Token,(a,b)=>((IProgress<Tuple<long,long>>)downloadProgress).Report(Tuple.Create(a,b))));
    Append("Downloaded "+latest.Version+"; release signature verified.");progress.Value=0;
   }else if(pkg==":embedded")pkg=null;
   using(var release=Release.Load(pkg)){
    Append("Starting "+J.S(release.Manifest,"version")+". Existing Remastered files will be retained as a previous version.");
    var uiProgress=new Progress<Tuple<string,int>>(v=>{state.Text=v.Item1;progress.Value=Math.Max(0,Math.Min(100,v.Item2));Append(v.Item1);});
    var engine=new Engine{Cancel=cancellation.Token,Progress=(s,p)=>((IProgress<Tuple<string,int>>)uiProgress).Report(Tuple.Create(s,p))};
    await Task.Run(()=>engine.Install(release,cePath,legacyPath));state.Text="Ready · "+J.S(release.Manifest,"version");Append("Installation complete. Launch Remastered CE when ready.");
   }}catch(OperationCanceledException){state.Text="Cancelled. Installed files were preserved.";Append(state.Text);}catch(Exception ex){state.Text="Installation stopped. See the message below.";ShowError(ex);}finally{busy=false;uninstall.Enabled=true;install.Enabled=true;launch.Enabled=true;choosePackage.Enabled=true;github.Enabled=true;ce.ReadOnly=false;legacy.ReadOnly=false;cancel.Enabled=false;cancellation.Dispose();cancellation=null;}
 }
 async Task Uninstall(){
  if(busy)return;string cePath=ce.Text.Trim();
  if(!Directory.Exists(cePath)){ShowError(new IOException("Choose the Complete Edition game folder first."));return;}
  if(MessageBox.Show(this,"Remove the active Remastered CE installation and its launchers?\n\nVanilla game files, saves, settings, and previous-version backup folders will be kept.","Uninstall Remastered CE",MessageBoxButtons.YesNo,MessageBoxIcon.Question,MessageBoxDefaultButton.Button2)!=DialogResult.Yes)return;
  busy=true;install.Enabled=false;launch.Enabled=false;uninstall.Enabled=false;choosePackage.Enabled=false;github.Enabled=false;ce.ReadOnly=true;legacy.ReadOnly=true;cancel.Enabled=false;progress.Value=0;
  try{
   var uiProgress=new Progress<Tuple<string,int>>(v=>{state.Text=v.Item1;progress.Value=v.Item2;Append(v.Item1);});
   var engine=new Engine{Progress=(s,p)=>((IProgress<Tuple<string,int>>)uiProgress).Report(Tuple.Create(s,p))};
   await Task.Run(()=>engine.Uninstall(cePath));Append("Use Steam to launch the vanilla game.");
  }catch(Exception ex){state.Text="Uninstall stopped. See the message below.";ShowError(ex);}finally{busy=false;install.Enabled=true;launch.Enabled=true;uninstall.Enabled=true;choosePackage.Enabled=true;github.Enabled=true;ce.ReadOnly=false;legacy.ReadOnly=false;}
 }
 void LoadSettings(){try{if(File.Exists(settings)){var d=J.Parse(File.ReadAllText(settings));if(Directory.Exists(J.S(d,"ce")))ce.Text=J.S(d,"ce");if(Directory.Exists(J.S(d,"legacy")))legacy.Text=J.S(d,"legacy");}}catch{}}
 void SaveSettings(){Directory.CreateDirectory(Path.GetDirectoryName(settings));File.WriteAllText(settings,J.Json().Serialize(new Dictionary<string,object>{{"ce",ce.Text.Trim()},{"legacy",legacy.Text.Trim()}}));}
 static string FindGame(string folder,string exe){var roots=new List<string>();try{using(var key=Registry.CurrentUser.OpenSubKey(@"Software\Valve\Steam")){if(key!=null){string s=Convert.ToString(key.GetValue("SteamPath"));if(!String.IsNullOrEmpty(s))roots.Add(s);}}}catch{}
  roots.Add(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86),"Steam"));foreach(var drive in DriveInfo.GetDrives()){if(drive.DriveType==DriveType.Fixed)roots.Add(Path.Combine(drive.RootDirectory.FullName,"SteamLibrary"));}
  foreach(string root in roots.ToArray()){string vdf=Path.Combine(root,"steamapps","libraryfolders.vdf");try{if(File.Exists(vdf))foreach(Match m in Regex.Matches(File.ReadAllText(vdf),"\"path\"\\s+\"([^\"]+)\""))roots.Add(m.Groups[1].Value.Replace("\\\\","\\"));}catch{}}
  foreach(string root in roots.Distinct(StringComparer.OrdinalIgnoreCase)){string p=Path.Combine(root,"steamapps","common",folder);if(File.Exists(Path.Combine(p,exe)))return p;}return "";
 }
}
static class SelfTests {
 public static void Run(string path){var results=new List<string>();string root=Path.Combine(Path.GetTempPath(),"RCE-test");bool rejected=false;try{Engine.Under(root,"../escape");}catch(InvalidDataException){rejected=true;}if(!rejected)throw new Exception("Path traversal test failed.");results.Add("PASS: path traversal rejected");
  byte[] source=Encoding.ASCII.GetBytes("abcdefgh");object[] ops={new Dictionary<string,object>{{"copy",2},{"length",3}},new Dictionary<string,object>{{"data",Convert.ToBase64String(Encoding.ASCII.GetBytes("XYZ"))}}};if(Encoding.ASCII.GetString(Engine.Transform(source,ops))!="cdeXYZ")throw new Exception("Transform failed.");results.Add("PASS: source-copy and write instructions");
  byte[] compressed=Lz4.Encode(source,"fast",0);if(!Lz4.Decode(compressed,source.Length).SequenceEqual(source))throw new Exception("LZ4 failed.");results.Add("PASS: embedded LZ4 roundtrip");
  using(var release=Release.Load(null)){results.Add("PASS: embedded release signature");byte[] original=Release.Resource("release");original[original.Length-1]^=1;string temp=Path.Combine(Path.GetTempPath(),"RCE-tampered-"+Guid.NewGuid().ToString("N")+".rce");File.WriteAllBytes(temp,original);try{rejected=false;try{using(var bad=Release.Load(temp)){} }catch(InvalidDataException){rejected=true;}if(!rejected)throw new Exception("Tampered package accepted.");results.Add("PASS: tampered release rejected");}finally{File.Delete(temp);}}
  
  string transactionRoot=Path.Combine(Path.GetTempPath(),"RCE-publication-test-"+Guid.NewGuid().ToString("N"));Directory.CreateDirectory(transactionRoot);
  try{string live=Engine.Under(transactionRoot,"RemasteredCE"),stage=Engine.Under(transactionRoot,"RemasteredCE.staging_test"),previous=Engine.Under(transactionRoot,"RemasteredCE.previous_test");Directory.CreateDirectory(live);Directory.CreateDirectory(stage);File.WriteAllText(Engine.Under(live,"old.txt"),"old installation");File.WriteAllText(Engine.Under(transactionRoot,"Launch_Remastered_CE.exe"),"old launcher");File.WriteAllText(Engine.Under(transactionRoot,"RemasteredCE_Bootstrap.exe"),"old bootstrap");File.WriteAllText(Engine.Under(stage,"RemasteredCE_Bootstrap.exe"),"new bootstrap");
   rejected=false;try{Engine.PublishVerified(stage,transactionRoot,previous);}catch(FileNotFoundException){rejected=true;}
   if(!rejected||!File.Exists(Engine.Under(live,"old.txt"))||File.ReadAllText(Engine.Under(transactionRoot,"RemasteredCE_Bootstrap.exe"))!="old bootstrap"||File.ReadAllText(Engine.Under(transactionRoot,"Launch_Remastered_CE.exe"))!="old launcher")throw new Exception("Publication rollback failed.");results.Add("PASS: failed update restores previous folder and already-replaced bootstrap");
   File.WriteAllText(Engine.Under(stage,"Launch_Remastered_CE.exe"),"new launcher");Engine.PublishVerified(stage,transactionRoot,previous);if(!File.Exists(Engine.Under(previous,"old.txt"))||File.ReadAllText(Engine.Under(transactionRoot,"Launch_Remastered_CE.exe"))!="new launcher")throw new Exception("Publication commit failed.");results.Add("PASS: verified update publishes and preserves previous installation");
  }finally{Engine.NoLinks(transactionRoot);if(!Path.GetFileName(transactionRoot).StartsWith("RCE-publication-test-",StringComparison.Ordinal))throw new Exception("Invalid self-test cleanup target.");Directory.Delete(transactionRoot,true);}
  string uninstallRoot=Path.Combine(Path.GetTempPath(),"RCE-uninstall-test-"+Guid.NewGuid().ToString("N"));Directory.CreateDirectory(uninstallRoot);
  try{
   string live=Engine.Under(uninstallRoot,"RemasteredCE"),record=Engine.Under(live,"install-state.json");Directory.CreateDirectory(Engine.Under(live,"data"));Directory.CreateDirectory(Engine.Under(live,"previous-launchers"));
   var packs=new[]{"data/data.pack","data/shaders.pack","data/bp_orig.pack","data/web_content.pack"};
   File.WriteAllText(Engine.Under(uninstallRoot,"shogun2_complete_edition.exe"),"vanilla executable");Directory.CreateDirectory(Engine.Under(uninstallRoot,"data"));File.WriteAllText(Engine.Under(uninstallRoot,"data/data.pack"),"vanilla pack");
   Directory.CreateDirectory(Engine.Under(uninstallRoot,"RemasteredCE.previous_test"));File.WriteAllText(Engine.Under(uninstallRoot,"RemasteredCE.previous_test/keep.txt"),"previous version");
   foreach(string pack in packs)File.WriteAllText(Engine.Under(live,pack),"modified pack");File.WriteAllText(Engine.Under(live,"CE.dll"),"modified engine");
   foreach(string name in new[]{"Launch_Remastered_CE.exe","RemasteredCE_Bootstrap.exe"}){File.WriteAllText(Engine.Under(live,name),name);File.WriteAllText(Engine.Under(uninstallRoot,name),name);File.WriteAllText(Engine.Under(live,"previous-launchers/"+name),"previous launcher");}
   File.WriteAllText(Engine.Under(live,"shogun2_complete_edition.exe"),"copied bootstrap");File.WriteAllText(Engine.Under(live,"nvngx_dlss.dll"),"copied NVIDIA runtime");File.WriteAllText(Engine.Under(uninstallRoot,"nvngx_dlss.dll"),"vanilla NVIDIA runtime");
   Directory.CreateDirectory(Engine.Under(uninstallRoot,"data/subfolder"));File.WriteAllText(Engine.Under(uninstallRoot,"data/subfolder/base.txt"),"base data");
   string[] linked=new Engine().LinkBaseData(uninstallRoot,live);
   if(linked.Length!=1 || File.ReadAllText(Engine.Under(live,"data/subfolder/base.txt"))!="base data" || File.ReadAllText(Engine.Under(live,"data/data.pack"))!="modified pack")throw new Exception("Base data linking failed.");
   results.Add("PASS: base data links include nested files and preserve modified packs");
   var state=new Dictionary<string,object>{{"schema",1},{"layoutVersion",2},{"engineHash","fixture"},{"files",packs.Select(x=>new Dictionary<string,object>{{"file",x}}).ToArray()}};
   state["baseDataFiles"]=linked;
   var wrong=new Dictionary<string,object>(state);wrong["files"]=new[]{new Dictionary<string,object>{{"file","../shogun2_complete_edition.exe"}}};File.WriteAllText(record,J.Json().Serialize(wrong));
   rejected=false;try{new Engine().Uninstall(uninstallRoot);}catch(InvalidDataException){rejected=true;}if(!rejected || !File.Exists(Engine.Under(live,"CE.dll")))throw new Exception("Unsafe uninstall record was accepted.");results.Add("PASS: uninstall rejects unexpected file paths before removing anything");
   File.WriteAllText(record,J.Json().Serialize(state));File.WriteAllText(Engine.Under(uninstallRoot,"Launch_Remastered_CE.exe"),"unrecognized replacement");
   rejected=false;try{new Engine().Uninstall(uninstallRoot);}catch(IOException){rejected=true;}if(!rejected || !File.Exists(Engine.Under(live,"CE.dll")))throw new Exception("Unrecognized launcher was removed.");results.Add("PASS: uninstall preserves an unrecognized root launcher and stops before deletion");
   File.WriteAllText(Engine.Under(uninstallRoot,"Launch_Remastered_CE.exe"),"Launch_Remastered_CE.exe");File.WriteAllText(Engine.Under(live,"keep-user-file.txt"),"user file");new Engine().Uninstall(uninstallRoot);
   if(File.Exists(Engine.Under(live,"data/subfolder/base.txt"))||File.Exists(Engine.Under(live,"shogun2_complete_edition.exe"))||File.Exists(Engine.Under(live,"nvngx_dlss.dll"))||File.Exists(record)||File.Exists(Engine.Under(live,"CE.dll"))||packs.Any(x=>File.Exists(Engine.Under(live,x)))||File.Exists(Engine.Under(uninstallRoot,"Launch_Remastered_CE.exe"))||File.Exists(Engine.Under(uninstallRoot,"RemasteredCE_Bootstrap.exe")))throw new Exception("Uninstall left managed files.");
   if(File.ReadAllText(Engine.Under(uninstallRoot,"data/subfolder/base.txt"))!="base data"||File.ReadAllText(Engine.Under(uninstallRoot,"nvngx_dlss.dll"))!="vanilla NVIDIA runtime"||File.ReadAllText(Engine.Under(uninstallRoot,"shogun2_complete_edition.exe"))!="vanilla executable"||File.ReadAllText(Engine.Under(uninstallRoot,"data/data.pack"))!="vanilla pack"||!File.Exists(Engine.Under(uninstallRoot,"RemasteredCE.previous_test/keep.txt"))||!File.Exists(Engine.Under(live,"keep-user-file.txt")))throw new Exception("Uninstall removed unrelated files.");results.Add("PASS: uninstall removes managed files and launchers; preserves vanilla including NVIDIA runtime, user files, and previous versions");
  }finally{Engine.NoLinks(uninstallRoot);if(!Path.GetFileName(uninstallRoot).StartsWith("RCE-uninstall-test-",StringComparison.Ordinal))throw new Exception("Invalid uninstall-test cleanup target.");Directory.Delete(uninstallRoot,true);}
  if(!OnlineUpdates.NeedsUpdate("0.1.9-preview","0.1.10-preview")||OnlineUpdates.NeedsUpdate("0.1.10-preview","0.1.9-preview")||OnlineUpdates.NeedsUpdate("0.1.3-preview","0.1.3-preview")||ReleaseVersion.Parse("1.0.0-preview.10").CompareTo(ReleaseVersion.Parse("1.0.0-preview.2"))<=0||ReleaseVersion.Parse("1.0.0").CompareTo(ReleaseVersion.Parse("1.0.0-preview"))<=0)throw new Exception("Release version ordering failed.");results.Add("PASS: updater orders versions numerically and avoids same-version installs and downgrades");
  var onlineRows=new List<object>();
  foreach(string version in new[]{"0.1.9-preview","0.1.10-preview","0.1.11-preview"})onlineRows.Add(new Dictionary<string,object>{{"tag_name","v"+version},{"draft",version=="0.1.11-preview"},{"prerelease",true},{"assets",new[]{new Dictionary<string,object>{{"name","RemasteredCE-"+version+".rce"},{"state","uploaded"},{"size",123},{"browser_download_url","https://github.com/JakeTheRipperYT/Remastered-CE/releases/download/v"+version+"/RemasteredCE-"+version+".rce"}}}}});
  string onlineJson=J.Json().Serialize(onlineRows);var selected=OnlineUpdates.Select(onlineJson);if(selected.Version!="0.1.10-preview")throw new Exception("Release selection failed.");results.Add("PASS: updater selects newest published package including prereleases and excludes drafts");
  rejected=false;try{OnlineUpdates.Select(onlineJson.Replace("https://github.com/","https://untrusted.invalid/"));}catch(InvalidDataException){rejected=true;}if(!rejected)throw new Exception("External update URL accepted.");results.Add("PASS: updater rejects download addresses outside the release repository");
  string packageTest=Path.Combine(Path.GetTempPath(),"RCE-version-test-"+Guid.NewGuid().ToString("N")+".rce");File.WriteAllBytes(packageTest,Release.Resource("release"));try{rejected=false;try{OnlineUpdates.ValidatePackage(packageTest,new OnlineRelease{Version="9.9.9"});}catch(InvalidDataException){rejected=true;}if(!rejected)throw new Exception("Mismatched signed release version accepted.");}finally{File.Delete(packageTest);}results.Add("PASS: updater rejects a signed package that differs from the advertised version");
  rejected=false;try{OnlineUpdates.Download(selected,Path.Combine(Path.GetTempPath(),"RCE-cancelled-download"),new CancellationToken(true),null);}catch(OperationCanceledException){rejected=true;}if(!rejected)throw new Exception("Download cancellation failed.");results.Add("PASS: cancelled update download stops before making a request or changing game files");
  File.WriteAllLines(path,results);
 }
}
}
