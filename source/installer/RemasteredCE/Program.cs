using System;
using System.Drawing;
using System.IO;
using System.Threading;
using System.Windows.Forms;

namespace RemasteredCE;

internal static class Program
{
	[STAThread]
	private static int Main(string[] args)
	{
		if (args.Length != 0 && args[0] != "--game")
		{
			try
			{
				if (args[0] == "--preview" && args.Length == 2)
				{
					Application.EnableVisualStyles();
					using (MainForm mainForm = new MainForm(preview: true))
					{
						mainForm.Show();
						Application.DoEvents();
						using Bitmap bitmap = new Bitmap(mainForm.Width, mainForm.Height);
						mainForm.DrawToBitmap(bitmap, new Rectangle(0, 0, mainForm.Width, mainForm.Height));
						bitmap.Save(args[1]);
					}
					return 0;
				}
				if (args[0] == "--self-test")
				{
					SelfTests.Run((args.Length > 1) ? args[1] : "installer-selftest.txt");
					return 0;
				}
				if (args[0] == "--build-only" && args.Length == 5)
				{
					string ce = args[1];
					string legacy = args[2];
					string fullPath = Path.GetFullPath(args[4]);
					if (Directory.Exists(fullPath))
					{
						throw new IOException("Build-only output already exists.");
					}
					string log = fullPath + ".log";
					using (Release release = Release.Load(args[3]))
					{
						Engine engine = new Engine();
						engine.Progress = (string s, int num) =>
						{
							File.AppendAllText(log, num + "% " + s + Environment.NewLine);
						};
						engine.Build(release, ce, legacy, fullPath);
					}
					File.AppendAllText(log, "SUCCESS" + Environment.NewLine);
					return 0;
				}
				if (!(args[0] == "--check-online") || args.Length != 2)
				{
					throw new ArgumentException("Unknown installer command.");
				}
				OnlineRelease onlineRelease = OnlineUpdates.Latest(CancellationToken.None);
				string p = OnlineUpdates.Download(onlineRelease, args[1], CancellationToken.None, null);
				Console.WriteLine("Verified online release " + onlineRelease.Version);
				File.WriteAllText(Path.Combine(args[1], "online-check.txt"), onlineRelease.Version + Environment.NewLine + Engine.FileHash(p));
				return 0;
			}
			catch (Exception ex)
			{
				File.AppendAllText((args.Length == 5) ? (Path.GetFullPath(args[4]) + ".log") : "installer-error.txt", "FAILED: " + ex?.ToString() + Environment.NewLine);
				return 1;
			}
		}
		Application.EnableVisualStyles();
		Application.SetCompatibleTextRenderingDefault(defaultValue: false);
		return UnifiedLauncher.Run(args);
	}
}
