using System;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Threading;
using System.Windows.Forms;

namespace RemasteredCE;

public static class UnifiedLauncher
{
	public static string ResolveGameHint(string[] args, string detected)
	{
		if (args.Length == 0 || args[0] != "--game") return detected ?? "";
		if (args.Length < 2 || args[1] == "--") throw new ArgumentException("The --game option requires a game folder.");
		return string.IsNullOrWhiteSpace(args[1]) ? "" : args[1];
	}

	public static string CacheExecutable(string source, string cacheRoot)
	{
		source = Path.GetFullPath(source);
		string text = Engine.FileHash(source);
		string text2 = Path.Combine(cacheRoot, text);
		string text3 = Path.Combine(text2, "RemasteredCE_Launcher.exe");
		if (string.Equals(source, Path.GetFullPath(text3), StringComparison.OrdinalIgnoreCase))
		{
			return text3;
		}
		Directory.CreateDirectory(text2);
		if (!File.Exists(text3))
		{
			string text4 = Path.Combine(text2, "launch-" + Guid.NewGuid().ToString("N") + ".tmp");
			try
			{
				File.Copy(source, text4);
				if (Engine.FileHash(text4) != text)
				{
					throw new IOException("Launcher changed while preparing its update-safe copy.");
				}
				try
				{
					File.Move(text4, text3);
				}
				catch (IOException)
				{
					if (!File.Exists(text3) || Engine.FileHash(text3) != text)
					{
						throw;
					}
				}
			}
			finally
			{
				if (File.Exists(text4))
				{
					File.Delete(text4);
				}
			}
		}
		if (Engine.FileHash(text3) != text)
		{
			throw new IOException("The cached launcher was changed. Keep it for inspection and reinstall the launcher.");
		}
		return text3;
	}

	public static int Run(string[] args)
	{
		try
		{
			if (args.Length != 0 && args[0] == "--game" && (args.Length < 2 || args[1] == "--"))
			{
				throw new ArgumentException("The --game option requires a game folder.");
			}
			string executablePath = Application.ExecutablePath;
			string text = Path.GetDirectoryName(executablePath);
			if (Path.GetFileName(text).Equals("RemasteredCE", StringComparison.OrdinalIgnoreCase))
			{
				text = Directory.GetParent(text).FullName;
			}
			string text2 = (File.Exists(Path.Combine(text, "shogun2_complete_edition.exe")) ? text : MainForm.FindGame());
			string[] array = new string[0];
			if (args.Length >= 2 && args[0] == "--game")
			{
				text2 = ResolveGameHint(args, text2);
				int num = Array.IndexOf(args, "--");
				if (num >= 0)
				{
					array = args.Skip(num + 1).ToArray();
				}
			}
			string text3 = CacheExecutable(executablePath, Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "RemasteredCE", "launcher"));
			if (!string.Equals(Path.GetFullPath(executablePath), text3, StringComparison.OrdinalIgnoreCase))
			{
				string arguments = string.Join(" ", new string[3]
				{
					"--game",
					text2 ?? "",
					"--"
				}.Concat(array).Select(Mods.QuoteArgument));
				Process.Start(new ProcessStartInfo(text3, arguments)
				{
					WorkingDirectory = Path.GetDirectoryName(text3),
					UseShellExecute = false,
					CreateNoWindow = true
				});
				return 0;
			}
			Application.EnableVisualStyles();
			Application.SetCompatibleTextRenderingDefault(defaultValue: false);
			Application.ThreadException += (object sender, ThreadExceptionEventArgs e) =>
			{
				Engine.LogLauncherError(e.Exception);
				MessageBox.Show(e.Exception.Message, "Remastered CE", MessageBoxButtons.OK, MessageBoxIcon.Hand);
			};
			Application.Run(new UnifiedForm(text2, array));
			return 0;
		}
		catch (Exception ex)
		{
			Engine.LogLauncherError(ex);
			MessageBox.Show(ex.Message, "Remastered CE", MessageBoxButtons.OK, MessageBoxIcon.Hand);
			return 1;
		}
	}
}
