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

   throw new ArgumentException("Unknown installer command.");

  }catch(Exception ex){string log=args.Length==5?Path.GetFullPath(args[4])+".log":"installer-error.txt";File.AppendAllText(log,"FAILED: "+ex+Environment.NewLine);return 1;}}

  Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);Application.Run(new MainForm());return 0;

 }

}

public sealed class MainForm : Form {

 readonly TextBox ce=new TextBox(),legacy=new TextBox(),package=new TextBox(),log=new TextBox();

 readonly Button install=new Button(),launch=new Button(),choosePackage=new Button(),cancel=new Button();

 readonly ProgressBar progress=new ProgressBar();readonly Label state=new Label();CancellationTokenSource cancellation;bool busy;

 readonly string settings=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"RemasteredCE","installer-settings.json");

 public MainForm(bool preview=false){

  Text="Remastered CE";ClientSize=new Size(810,650);MinimumSize=new Size(820,690);StartPosition=FormStartPosition.CenterScreen;Font=new Font("Segoe UI",10);BackColor=Color.FromArgb(23,27,30);ForeColor=Color.FromArgb(235,239,240);AutoScaleMode=AutoScaleMode.Dpi;

  var title=new Label{Text="REMASTERED CE",Font=new Font("Segoe UI Semibold",23),AutoSize=true,Location=new Point(28,24)};Controls.Add(title);

  Controls.Add(new Label{Text="By JakeTheRipper · Preview 0.1.1",AutoSize=true,ForeColor=Color.FromArgb(158,176,181),Location=new Point(31,73)});

  FolderRow("Complete Edition installation",ce,122);FolderRow("Original Shogun 2 installation",legacy,204);

  Controls.Add(new Label{Text="Release package",AutoSize=true,Location=new Point(30,286)});StyleBox(package);package.Location=new Point(30,312);package.Size=new Size(625,29);package.ReadOnly=true;package.Text="Included preview release";Controls.Add(package);ButtonStyle(choosePackage,"Update file…",new Rectangle(667,310,113,33));choosePackage.Click+=(s,e)=>{using(var dialog=new OpenFileDialog{Filter="Remastered CE release (*.rce)|*.rce",Title="Choose a signed Remastered CE update"})if(dialog.ShowDialog()==DialogResult.OK){try{using(var r=Release.Load(dialog.FileName)){package.Tag=dialog.FileName;package.Text=Path.GetFileName(dialog.FileName);Append("Selected "+J.S(r.Manifest,"version")+"; signature verified.");}}catch(Exception ex){ShowError(ex);}}};

  ButtonStyle(install,"Install / Update Remastered CE",new Rectangle(30,367,325,47));install.BackColor=Color.FromArgb(49,117,98);install.Click+=async(s,e)=>await Install();

  ButtonStyle(launch,"Launch Remastered CE",new Rectangle(369,367,260,47));launch.Click+=(s,e)=>{try{string file=Engine.Under(ce.Text,"Launch_Remastered_CE.exe");if(!File.Exists(file))throw new FileNotFoundException("Install Remastered CE first.");Process.Start(new ProcessStartInfo(file){WorkingDirectory=Path.GetFullPath(ce.Text),UseShellExecute=true});}catch(Exception ex){ShowError(ex);}};

  ButtonStyle(cancel,"Cancel",new Rectangle(643,367,137,47));cancel.Enabled=false;cancel.Click+=(s,e)=>{if(cancellation!=null)cancellation.Cancel();};

  state.Text="Vanilla game files stay untouched. Both games must be installed.";state.AutoSize=false;state.Location=new Point(30,429);state.Size=new Size(750,42);state.ForeColor=Color.FromArgb(158,176,181);Controls.Add(state);

  progress.Location=new Point(30,478);progress.Size=new Size(750,9);Controls.Add(progress);

  StyleBox(log);log.Multiline=true;log.ReadOnly=true;log.ScrollBars=ScrollBars.Vertical;log.Location=new Point(30,503);log.Size=new Size(750,115);log.Anchor=AnchorStyles.Left|AnchorStyles.Right|AnchorStyles.Bottom|AnchorStyles.Top;Controls.Add(log);

  ce.Text=FindGame("Shogun 2 Complete Edition","shogun2_complete_edition.exe");legacy.Text=FindGame("Total War SHOGUN 2","Shogun2.exe");LoadSettings();if(preview){ce.Text=@"C:\Users\JakeTheRipper\Games\Shogun 2 Complete Edition";legacy.Text=@"C:\Users\JakeTheRipper\Games\Total War SHOGUN 2";}

  using(var r=Release.Load(null))Append("Included release "+J.S(r.Manifest,"version")+". Source assets are extracted locally; no complete game files are included.");

  FormClosing+=(s,e)=>{if(busy){e.Cancel=true;MessageBox.Show(this,"Cancel the installation and wait for it to stop before closing.",Text,MessageBoxButtons.OK,MessageBoxIcon.Information);}};

 }

 void FolderRow(string label,TextBox box,int y){Controls.Add(new Label{Text=label,AutoSize=true,Location=new Point(30,y)});StyleBox(box);box.Location=new Point(30,y+27);box.Size=new Size(625,29);Controls.Add(box);var browse=new Button();ButtonStyle(browse,"Browse…",new Rectangle(667,y+25,113,33));browse.Click+=(s,e)=>{using(var dialog=new FolderBrowserDialog{Description=label,SelectedPath=Directory.Exists(box.Text)?box.Text:""})if(dialog.ShowDialog()==DialogResult.OK)box.Text=dialog.SelectedPath;};}

 void ButtonStyle(Button b,string text,Rectangle bounds){b.Text=text;b.Bounds=bounds;b.FlatStyle=FlatStyle.Flat;b.FlatAppearance.BorderColor=Color.FromArgb(72,85,91);b.BackColor=Color.FromArgb(40,48,53);b.ForeColor=ForeColor;Controls.Add(b);}

 void StyleBox(TextBox t){t.BackColor=Color.FromArgb(32,39,43);t.ForeColor=ForeColor;t.BorderStyle=BorderStyle.FixedSingle;}

 void Append(string s){log.AppendText(DateTime.Now.ToString("HH:mm:ss")+"  "+s+Environment.NewLine);}

 void ShowError(Exception ex){string message=ex is UnauthorizedAccessException?"Windows denied access to the selected folder. Close the game and, if this folder requires it, run this installer as administrator.":ex.Message;Append(message);MessageBox.Show(this,message,Text,MessageBoxButtons.OK,MessageBoxIcon.Warning);}

 async Task Install(){

  if(busy)return;string cePath=ce.Text.Trim(),legacyPath=legacy.Text.Trim(),pkg=package.Tag as string;

  if(!Directory.Exists(cePath)||!Directory.Exists(legacyPath)){ShowError(new IOException("Choose both installed game folders first."));return;}

  busy=true;install.Enabled=false;launch.Enabled=false;choosePackage.Enabled=false;ce.ReadOnly=true;legacy.ReadOnly=true;cancel.Enabled=true;cancellation=new CancellationTokenSource();progress.Value=0;

  try{SaveSettings();using(var release=Release.Load(pkg)){

    Append("Starting "+J.S(release.Manifest,"version")+". Existing Remastered files will be retained as a previous version.");

    var uiProgress=new Progress<Tuple<string,int>>(v=>{state.Text=v.Item1;progress.Value=Math.Max(0,Math.Min(100,v.Item2));Append(v.Item1);});

    var engine=new Engine{Cancel=cancellation.Token,Progress=(s,p)=>((IProgress<Tuple<string,int>>)uiProgress).Report(Tuple.Create(s,p))};

    await Task.Run(()=>engine.Install(release,cePath,legacyPath));state.Text="Ready · "+J.S(release.Manifest,"version");Append("Installation complete. Launch Remastered CE when ready.");

   }}catch(OperationCanceledException){state.Text="Cancelled. Installed files were preserved.";Append(state.Text);}catch(Exception ex){state.Text="Installation stopped. See the message below.";ShowError(ex);}finally{busy=false;install.Enabled=true;launch.Enabled=true;choosePackage.Enabled=true;ce.ReadOnly=false;legacy.ReadOnly=false;cancel.Enabled=false;cancellation.Dispose();cancellation=null;}

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

  File.WriteAllLines(path,results);

 }

}

}

