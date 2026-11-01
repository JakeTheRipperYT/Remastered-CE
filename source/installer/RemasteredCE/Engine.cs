using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;

namespace RemasteredCE;

public sealed class Engine
{
	public Action<string, int> Progress;

	public CancellationToken Cancel;

	[DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
	private static extern bool CreateHardLinkW(string target, string source, IntPtr reserved);

	public string[] LinkBaseData(string ce, string stage)
	{
		string text = Under(ce, "data");
		NoLinks(text);
		List<string> list = new List<string>();
		foreach (string item in Directory.EnumerateFiles(text, "*", SearchOption.AllDirectories))
		{
			Cancel.ThrowIfCancellationRequested();
			NoLinks(Path.GetDirectoryName(item));
			RejectLinkedFile(item);
			string text2 = "data/" + item.Substring(text.Length + 1).Replace('\\', '/');
			string text3 = Under(stage, text2);
			if (File.Exists(text3))
			{
				continue;
			}
			Directory.CreateDirectory(Path.GetDirectoryName(text3));
			if (!CreateHardLinkW(text3, item, IntPtr.Zero))
			{
				int lastWin32Error = Marshal.GetLastWin32Error();
				if (lastWin32Error != 17)
				{
					throw new Win32Exception(lastWin32Error, "Unable to link required base game data: " + text2);
				}
				CopyFile(item, text3);
			}
			list.Add(text2);
		}
		return list.ToArray();
	}

	public void Log(string s, int p)
	{
		if (Progress != null)
		{
			Progress(s, p);
		}
		Cancel.ThrowIfCancellationRequested();
	}

	public static string Hash(byte[] data)
	{
		using SHA256 sHA = SHA256.Create();
		return BitConverter.ToString(sHA.ComputeHash(data)).Replace("-", "").ToLowerInvariant();
	}

	public static string FileHash(string p)
	{
		using FileStream inputStream = File.OpenRead(p);
		using SHA256 sHA = SHA256.Create();
		return BitConverter.ToString(sHA.ComputeHash(inputStream)).Replace("-", "").ToLowerInvariant();
	}

	public static string Under(string root, string relative)
	{
		if (Path.IsPathRooted(relative))
		{
			throw new InvalidDataException("Absolute package paths are forbidden.");
		}
		string text = Path.GetFullPath(root).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
		string fullPath = Path.GetFullPath(Path.Combine(text, relative.Replace('/', Path.DirectorySeparatorChar)));
		if (!fullPath.StartsWith(text, StringComparison.OrdinalIgnoreCase))
		{
			throw new InvalidDataException("Package path escapes its installation folder.");
		}
		return fullPath;
	}

	public static void NoLinks(string path)
	{
		for (DirectoryInfo directoryInfo = new DirectoryInfo(Path.GetFullPath(path)); directoryInfo != null; directoryInfo = directoryInfo.Parent)
		{
			if (directoryInfo.Exists && (directoryInfo.Attributes & FileAttributes.ReparsePoint) != 0)
			{
				throw new IOException("Linked installation folders are not supported: " + directoryInfo.FullName);
			}
		}
	}

	public static void GameClosed()
	{
		string[] array = new string[4] { "shogun2_complete_edition", "RemasteredCE_Bootstrap", "Launch_Remastered_CE", "RemasteredCE_Launcher" };
		for (int i = 0; i < array.Length; i++)
		{
			if (Process.GetProcessesByName(array[i]).Any((Process p) => p.Id != Process.GetCurrentProcess().Id))
			{
				throw new IOException("Close CE and Remastered CE before installing or updating.");
			}
		}
	}

	private static void RequireHash(string path, string expected)
	{
		if (!File.Exists(path) || FileHash(path) != expected)
		{
			throw new InvalidDataException("Unsupported or modified source file: " + path + ". This release needs the supported vanilla CE build; do not overwrite newer game files with old backups.");
		}
	}

	public void Preflight(Release r, string ce, string legacy)
	{
		NoLinks(ce);
		NoLinks(legacy);
		if (string.Equals(Path.GetFullPath(ce), Path.GetFullPath(legacy), StringComparison.OrdinalIgnoreCase))
		{
			throw new IOException("Select separate CE and original Shogun 2 folders.");
		}
		if (!File.Exists(Under(legacy, "Shogun2.exe")))
		{
			throw new FileNotFoundException("Select the original Shogun 2 installation containing Shogun2.exe.");
		}
		Log("Verifying CE executableâ€¦", 0);
		RequireHash(Under(ce, "shogun2_complete_edition.exe"), J.S(r.Manifest, "ceExeSha256"));
		Log("Verifying vanilla CE engineâ€¦", 2);
		RequireHash(Under(ce, "empire.retail.x64.dll"), J.S(r.Manifest, "engineSourceSha256"));
		if (J.N(r.Manifest, "schema") == 2)
		{
			Log("Verifying the locally installed NVIDIA DLSS runtimeâ€¦", 3);
			RequireHash(Under(ce, "nvngx_dlss.dll"), J.S(r.Manifest, "dlssRuntimeSha256"));
		}
		int num = 0;
		object[] array = J.Arr(r.Manifest["files"]);
		for (int i = 0; i < array.Length; i++)
		{
			Dictionary<string, object> d = J.Obj(array[i]);
			if (GeneratedCampaignVisuals(d)) continue;
			Log("Verifying vanilla " + J.S(d, "source") + "â€¦", 3 + num * 3);
			RequireHash(Under(ce, J.S(d, "source")), J.S(d, "sourceSha256"));
			num++;
		}
	}

	private static bool GeneratedCampaignVisuals(Dictionary<string, object> recipe)
	{
		bool generated = recipe.ContainsKey("generated") && Convert.ToBoolean(recipe["generated"]);
		if (generated && (J.S(recipe, "destination") != "data/" + GameLayout.CampaignNightPack || !string.IsNullOrEmpty(J.S(recipe, "source"))))
			throw new InvalidDataException("Unsupported generated pack recipe.");
		return generated;
	}

	private byte[] Source(Dictionary<string, object> s, string ce, string legacy)
	{
		string text = Under((J.S(s, "root") == "legacy") ? legacy : ce, J.S(s, "file"));
		long num = J.N(s, "offset");
		long num2 = J.N(s, "stored");
		if (num < 0 || num2 < 0 || num2 > 268435456)
		{
			throw new InvalidDataException("Invalid source range.");
		}
		byte[] array = new byte[(int)num2];
		using (FileStream fileStream = File.OpenRead(text))
		{
			if (num > fileStream.Length - num2)
			{
				throw new InvalidDataException("Source archive version differs: " + text);
			}
			fileStream.Position = num;
			ReadAll(fileStream, array);
		}
		if (Convert.ToBoolean(s["compressed"]))
		{
			array = Lz4.Decode(array, (int)J.N(s, "size"));
		}
		if (Hash(array) != J.S(s, "sha256"))
		{
			throw new InvalidDataException("An original asset does not match this release: " + J.S(s, "file") + ". Check your original Shogun 2 installation.");
		}
		return array;
	}

	private static void ReadAll(Stream s, byte[] b)
	{
		int num;
		for (int i = 0; i < b.Length; i += num)
		{
			num = s.Read(b, i, b.Length - i);
			if (num == 0)
			{
				throw new EndOfStreamException();
			}
		}
	}

	public static byte[] Transform(byte[] input, object[] operations)
	{
		if (operations.Length == 0)
		{
			return input;
		}
		using MemoryStream memoryStream = new MemoryStream();
		for (int i = 0; i < operations.Length; i++)
		{
			Dictionary<string, object> dictionary = J.Obj(operations[i]);
			if (dictionary.ContainsKey("data"))
			{
				byte[] array = J.B(dictionary, "data");
				memoryStream.Write(array, 0, array.Length);
			}
			else
			{
				long num = J.N(dictionary, "copy");
				long num2 = J.N(dictionary, "length");
				if (num < 0 || num2 < 0 || num > input.Length - num2)
				{
					throw new InvalidDataException("Invalid source-copy instruction.");
				}
				memoryStream.Write(input, (int)num, (int)num2);
			}
			if (memoryStream.Length > 268435456)
			{
				throw new InvalidDataException("Asset output exceeds limit.");
			}
		}
		return memoryStream.ToArray();
	}

	private static void ApplyWrites(Stream file, object[] ops)
	{
		for (int i = 0; i < ops.Length; i++)
		{
			Dictionary<string, object> d = J.Obj(ops[i]);
			long num = J.N(d, "offset");
			byte[] array = J.B(d, "data");
			if (num < 0 || num > file.Length - array.Length)
			{
				throw new InvalidDataException("Patch range is outside the source file.");
			}
			file.Position = num;
			file.Write(array, 0, array.Length);
		}
	}

	public static void ShiftPackBody(Stream stream, long start, long shift, long originalLength)
	{
		if (start < 32 || start > originalLength || shift <= 0 || shift > 16777216 || originalLength > stream.Length - shift)
		{
			throw new InvalidDataException("Invalid pack index expansion.");
		}
		byte[] array = new byte[4194304];
		long num = originalLength;
		while (num > start)
		{
			int num2 = (int)Math.Min(array.Length, num - start);
			long num3 = (stream.Position = num - num2);
			ReadAll(stream, array, num2);
			stream.Position = num3 + shift;
			stream.Write(array, 0, num2);
			num = num3;
		}
		Array.Clear(array, 0, array.Length);
		stream.Position = start;
		long num5 = shift;
		while (num5 > 0)
		{
			int num6 = (int)Math.Min(array.Length, num5);
			stream.Write(array, 0, num6);
			num5 -= num6;
		}
	}

	private static void ReadAll(Stream stream, byte[] buffer, int count)
	{
		int num;
		for (int i = 0; i < count; i += num)
		{
			num = stream.Read(buffer, i, count - i);
			if (num == 0)
			{
				throw new EndOfStreamException();
			}
		}
	}

	public void Build(Release release, string ce, string legacy, string stage)
	{
		Preflight(release, ce, legacy);
		NoLinks(stage);
		Directory.CreateDirectory(stage);
		Dictionary<string, Dictionary<string, object>> dictionary = J.Arr(release.Manifest["sources"]).Select(J.Obj).ToDictionary((Dictionary<string, object> d) => J.S(d, "id"));
		int num = 0;
		int val = J.Arr(release.Manifest["files"]).Select(J.Obj).Sum((Dictionary<string, object> dictionary5) => J.Arr(dictionary5["assets"]).Length);
		object[] array = J.Arr(release.Manifest["files"]);
		for (int num2 = 0; num2 < array.Length; num2++)
		{
			Dictionary<string, object> dictionary2 = J.Obj(array[num2]);
			string text = J.S(dictionary2, "destination");
			if (!new string[9] { "data/data.pack", "data/shaders.pack", "data/bp_orig.pack", "data/web_content.pack", "data/local_global.pack", "data/models.pack", "data/audio.pack", "data/movies.pack", "data/" + GameLayout.CampaignNightPack }.Contains(text))
			{
				throw new InvalidDataException("Unsupported destination pack.");
			}
			string text2 = Under(stage, text);
			Directory.CreateDirectory(Path.GetDirectoryName(text2));
			Log("Copying " + text + "â€¦", 17 + (int)(65L * (long)num / Math.Max(1, val)));
			if (GeneratedCampaignVisuals(dictionary2))
				using (new FileStream(text2, FileMode.CreateNew, FileAccess.Write, FileShare.None)) { }
			else CopyFile(Under(ce, J.S(dictionary2, "source")), text2);
			using (FileStream fileStream = new FileStream(text2, FileMode.Open, FileAccess.ReadWrite, FileShare.None))
			{
				long length = fileStream.Length;
				fileStream.SetLength(J.N(dictionary2, "length"));
				if (dictionary2.ContainsKey("sourceBodyShift"))
				{
					ShiftPackBody(fileStream, J.N(dictionary2, "sourceBodyOffset"), J.N(dictionary2, "sourceBodyShift"), length);
				}
				ApplyWrites(fileStream, J.Arr(dictionary2["metadata"]));
				object[] array2 = J.Arr(dictionary2["assets"]);
				foreach (object x in array2)
				{
					Cancel.ThrowIfCancellationRequested();
					Dictionary<string, object> dictionary3 = J.Obj(x);
					string text3 = J.S(dictionary3, "source");
					byte[] array3 = Transform(string.IsNullOrEmpty(text3) ? new byte[0] : Source(dictionary[text3], ce, legacy), J.Arr(dictionary3["operations"]));
					if (array3.Length != J.N(dictionary3, "size") || Hash(array3) != J.S(dictionary3, "sha256"))
					{
						throw new InvalidDataException("Patched asset failed verification: " + J.S(dictionary3, "path"));
					}
					byte[] array4 = Lz4.Encode(array3, J.S(dictionary3, "codec"), (int)J.N(dictionary3, "level"));
					if (array4.Length != J.N(dictionary3, "stored") || Hash(array4) != J.S(dictionary3, "encodedSha256"))
					{
						throw new InvalidDataException("Encoded asset failed verification: " + J.S(dictionary3, "path"));
					}
					long num4 = J.N(dictionary3, "offset");
					if (num4 < 0 || num4 > fileStream.Length - array4.Length)
					{
						throw new InvalidDataException("Asset output range is invalid.");
					}
					fileStream.Position = num4;
					fileStream.Write(array4, 0, array4.Length);
					num++;
					if (num % 40 == 0)
					{
						Log("Building assets: " + num + " / " + val, 17 + (int)(65L * (long)num / Math.Max(1, val)));
					}
				}
				fileStream.Flush(flushToDisk: true);
			}
			Log("Verifying completed " + text + "â€¦", 83);
			RequireHash(text2, J.S(dictionary2, "sha256"));
		}
		Log("Building the separate Remastered engineâ€¦", 88);
		byte[] array5 = File.ReadAllBytes(Under(ce, "empire.retail.x64.dll"));
		using (MemoryStream file = new MemoryStream(array5, writable: true))
		{
			ApplyWrites(file, J.Arr(release.Manifest["enginePatches"]));
		}
		if (Hash(array5) != J.S(release.Manifest, "engineEditedSha256"))
		{
			throw new InvalidDataException("Engine modifications failed verification.");
		}
		array5 = PePatch.Inject(array5, release.Helper);
		if (Hash(array5) != J.S(release.Manifest, "engineFinalSha256"))
		{
			throw new InvalidDataException("Engine path redirection failed verification.");
		}
		File.WriteAllBytes(Under(stage, "CE.dll"), array5);
		byte[] array6 = File.ReadAllBytes(Under(ce, "shogun2_complete_edition.exe"));
		byte[] bytes = Encoding.ASCII.GetBytes("Empire.Retail.x64.dll\0");
		byte[] bytes2 = Encoding.ASCII.GetBytes("RemasteredCE\\CE.dll\0");
		if (!array6.Skip(58872).Take(bytes.Length).SequenceEqual(bytes))
		{
			throw new InvalidDataException("Unsupported bootstrap DLL-path layout.");
		}
		Array.Clear(array6, 58872, bytes.Length);
		Buffer.BlockCopy(bytes2, 0, array6, 58872, bytes2.Length);
		File.WriteAllBytes(Under(stage, "RemasteredCE_Bootstrap.exe"), array6);
		File.WriteAllBytes(Under(stage, "Launch_Remastered_CE.exe"), release.Launcher);
		bool flag = J.N(release.Manifest, "schema") == 2;
		if (flag)
		{
			Array.Clear(array6, 58872, bytes.Length);
			bytes2 = Encoding.ASCII.GetBytes("CE.dll\0");
			Buffer.BlockCopy(bytes2, 0, array6, 58872, bytes2.Length);
			File.WriteAllBytes(Under(stage, "shogun2_complete_edition.exe"), array6);
			Log("Copying the local NVIDIA DLSS runtimeâ€¦", 92);
			CopyFile(Under(ce, "nvngx_dlss.dll"), Under(stage, "nvngx_dlss.dll"));
			RequireHash(Under(stage, "nvngx_dlss.dll"), J.S(release.Manifest, "dlssRuntimeSha256"));
		}
		Dictionary<string, object> dictionary4 = new Dictionary<string, object>
		{
			{ "schema", 1 },
			{
				"version",
				J.S(release.Manifest, "version")
			},
			{ "packageSha256", release.PackageHash },
			{
				"ceBuild",
				J.S(release.Manifest, "ceBuild")
			},
			{
				"installedUtc",
				DateTime.UtcNow.ToString("o")
			},
			{
				"engineHash",
				Hash(array5)
			},
			{
				"files",
				(from d in J.Arr(release.Manifest["files"]).Select(J.Obj)
					select new Dictionary<string, object>
					{
						{
							"file",
							J.S(d, "destination")
						},
						{
							"sha256",
							J.S(d, "sha256")
						}
					}).ToArray()
			}
		};
		if (flag)
		{
			dictionary4["layoutVersion"] = 2;
			Log("Linking required local base game dataâ€¦", 93);
			dictionary4["baseDataFiles"] = LinkBaseData(ce, stage);
		}
		InstallerLauncher.Stage(release, stage, dictionary4);
		File.WriteAllText(Under(stage, "install-state.json"), J.Json().Serialize(dictionary4));
		Log("All generated files verified.", 94);
	}

	private void CopyFile(string source, string target)
	{
		byte[] array = new byte[8388608];
		using FileStream fileStream = File.OpenRead(source);
		using FileStream fileStream2 = new FileStream(target, FileMode.CreateNew, FileAccess.Write, FileShare.None);
		int count;
		while ((count = fileStream.Read(array, 0, array.Length)) > 0)
		{
			Cancel.ThrowIfCancellationRequested();
			fileStream2.Write(array, 0, count);
		}
		fileStream2.Flush(flushToDisk: true);
	}

	public static bool ApplyUnitCameraPreference(string path)
	{
		if (!File.Exists(path))
		{
			return false;
		}
		byte[] array = File.ReadAllBytes(path);
		Encoding encoding;
		if (array.Length >= 2 && array[0] == byte.MaxValue && array[1] == 254)
		{
			encoding = new UnicodeEncoding(bigEndian: false, byteOrderMark: true, throwOnInvalidBytes: true);
		}
		else
		{
			encoding = ((array.Length < 2 || array[0] != 254 || array[1] != byte.MaxValue) ? ((Encoding)new UTF8Encoding(array.Length >= 3 && array[0] == 239 && array[1] == 187 && array[2] == 191, throwOnInvalidBytes: true)) : ((Encoding)new UnicodeEncoding(bigEndian: true, byteOrderMark: true, throwOnInvalidBytes: true)));
		}
		byte[] preamble = encoding.GetPreamble();
		int num = preamble.Length;
		string text = encoding.GetString(array, num, array.Length - num);
		if (new Regex("(?m)^([ \\t]*proximity_fading[ \\t]+)(?:true|false)([ \\t]*;[^\\r\\n]*)(?=\\r?$)").IsMatch(text))
		{
			return false;
		}
		string text2 = (text.Contains("\r\n") ? "\r\n" : "\n");
		string text3 = text + ((text.Length > 0 && !text.EndsWith("\n")) ? text2 : "") + "proximity_fading false;" + text2;
		if (text3 == text)
		{
			return false;
		}
		string path2 = path + ".remasteredce-unit-fade.bak";
		if (!File.Exists(path2))
		{
			File.WriteAllBytes(path2, array);
		}
		string text4 = path + ".remasteredce-" + Guid.NewGuid().ToString("N") + ".tmp";
		try
		{
			File.WriteAllBytes(text4, preamble.Concat(encoding.GetBytes(text3)).ToArray());
			File.Replace(text4, path, null);
		}
		finally
		{
			if (File.Exists(text4))
			{
				File.Delete(text4);
			}
		}
		return true;
	}

	private void ApplyReleasePreferences(Release release)
	{
		if (!release.Manifest.ContainsKey("disableUnitProximityFading") || !Convert.ToBoolean(release.Manifest["disableUnitProximityFading"]))
		{
			return;
		}
		string path = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "The Creative Assembly\\Shogun2CompleteEdition\\Steam\\scripts\\preferences.script.txt");
		try
		{
			if (ApplyUnitCameraPreference(path))
			{
				Log("Disabled near-camera unit fading; other preferences preserved. A preference backup was saved.", 99);
			}
		}
		catch (IOException)
		{
			Log("Installed successfully. Unit camera preference could not be updated; set proximity_fading false manually.", 99);
		}
		catch (UnauthorizedAccessException)
		{
			Log("Installed successfully. Unit camera preference could not be updated; set proximity_fading false manually.", 99);
		}
		catch (DecoderFallbackException)
		{
			Log("Installed successfully. Preference encoding was not recognized; set proximity_fading false manually.", 99);
		}
	}

	public void Install(Release r, string ce, string legacy)
	{
		ce = Path.GetFullPath(ce);
		NoLinks(ce);
		GameClosed();
		NoLinks(Under(ce, "RemasteredCE"));
		using (new FileStream(Under(ce, ".remastered-install.lock"), FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None))
		{
			string text = DateTime.UtcNow.ToString("yyyyMMdd_HHmmss") + "_" + Guid.NewGuid().ToString("N").Substring(0, 6);
			string text2 = Under(ce, "RemasteredCE.staging_" + text);
			string previous = Under(ce, "RemasteredCE.previous_" + text);
			bool flag = false;
			try
			{
				DriveInfo driveInfo = new DriveInfo(Path.GetPathRoot(ce));
				long num = J.Arr(r.Manifest["files"]).Select(J.Obj).Sum((Dictionary<string, object> f) => J.N(f, "length")) + 536870912;
				if (driveInfo.AvailableFreeSpace < num)
				{
					throw new IOException("Not enough free disk space to stage this update safely.");
				}
				Directory.CreateDirectory(text2);
				Build(r, ce, legacy, text2);
				Cancel.ThrowIfCancellationRequested();
				GameClosed();
				Log("Publishing verified Remastered files...", 96);
				PublishVerified(text2, ce, previous);
				ApplyReleasePreferences(r);
				Log("Installed " + J.S(r.Manifest, "version") + ". Vanilla game files were not replaced.", 100);
			}
			catch (AggregateException)
			{
				flag = true;
				throw;
			}
			finally
			{
				if (!flag && Directory.Exists(text2))
				{
					NoLinks(text2);
					if (!Path.GetFileName(text2).StartsWith("RemasteredCE.staging_", StringComparison.Ordinal))
					{
						throw new IOException("Invalid staging cleanup target.");
					}
					Directory.Delete(text2, recursive: true);
				}
			}
		}
	}

	public void Uninstall(string ce)
	{
		ce = Path.GetFullPath(ce);
		NoLinks(ce);
		GameClosed();
		string text = Under(ce, "RemasteredCE");
		NoLinks(text);
		if (!File.Exists(Under(ce, "shogun2_complete_edition.exe")))
		{
			throw new IOException("Select the Complete Edition game folder first.");
		}
		string path = Under(text, "install-state.json");
		if (!File.Exists(path))
		{
			throw new IOException("No installer-managed Remastered CE installation was found in this folder.");
		}
		using (new FileStream(Under(ce, ".remastered-install.lock"), FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None))
		{
			RejectLinkedFile(path);
			Dictionary<string, object> dictionary = J.Parse(File.ReadAllText(path));
			string[] array = new string[9] { "data/data.pack", "data/shaders.pack", "data/bp_orig.pack", "data/web_content.pack", "data/local_global.pack", "data/models.pack", "data/audio.pack", "data/movies.pack", "data/" + GameLayout.CampaignNightPack };
			if (J.N(dictionary, "schema") != 1 || !dictionary.ContainsKey("engineHash"))
			{
				throw new InvalidDataException("Unrecognized installation record; nothing was removed.");
			}
			string[] array2 = (from x in J.Arr(dictionary["files"]).Select(J.Obj)
				select J.S(x, "file")).ToArray();
			if (array2.Length < 4 || array2.Length > array.Length || !new HashSet<string>(array2, StringComparer.Ordinal).SetEquals(array.Take(array2.Length)))
			{
				throw new InvalidDataException("Unexpected installed file paths; nothing was removed.");
			}
			array = array2;
			Tuple<string, string>[] array3 = new Tuple<string, string>[2]
			{
				Tuple.Create("RemasteredCE_Launcher.exe", "unifiedLauncherSha256"),
				Tuple.Create("release.rce", "offlineReleaseSha256")
			};
			foreach (Tuple<string, string> tuple in array3)
			{
				string text2 = Under(text, tuple.Item1);
				RejectLinkedFile(text2);
				if (File.Exists(text2) && (!dictionary.ContainsKey(tuple.Item2) || FileHash(text2) != J.S(dictionary, tuple.Item2)))
				{
					throw new IOException("An installed launcher or offline package was edited; nothing was removed: " + text2);
				}
			}
			List<string> list = new List<string>();
			string[] array4 = array;
			foreach (string relative in array4)
			{
				list.Add(Under(text, relative));
			}
			list.Add(Under(text, "CE.dll"));
			if (dictionary.ContainsKey("unifiedLauncherSha256"))
			{
				list.Add(Under(text, "RemasteredCE_Launcher.exe"));
			}
			if (dictionary.ContainsKey("offlineReleaseSha256"))
			{
				list.Add(Under(text, "release.rce"));
			}
			if (dictionary.ContainsKey("layoutVersion"))
			{
				if (J.N(dictionary, "layoutVersion") != 2)
				{
					throw new InvalidDataException("Unrecognized installation layout; nothing was removed.");
				}
				list.Add(Under(text, "shogun2_complete_edition.exe"));
				list.Add(Under(text, "nvngx_dlss.dll"));
			}
			if (dictionary.ContainsKey("baseDataFiles"))
			{
				object[] array5 = J.Arr(dictionary["baseDataFiles"]);
				for (int num = 0; num < array5.Length; num++)
				{
					string text3 = Convert.ToString(array5[num]);
					if (!text3.StartsWith("data/", StringComparison.Ordinal) || array.Contains(text3))
					{
						throw new InvalidDataException("Unexpected base data path; nothing was removed.");
					}
					list.Add(Under(text, text3));
				}
			}
			array4 = new string[2] { "Launch_Remastered_CE.exe", "RemasteredCE_Bootstrap.exe" };
			foreach (string text4 in array4)
			{
				string text5 = Under(text, text4);
				string text6 = Under(ce, text4);
				string text7 = Under(text, "previous-launchers/" + text4);
				RejectLinkedFile(text5);
				RejectLinkedFile(text6);
				RejectLinkedFile(text7);
				NoLinks(Path.GetDirectoryName(text7));
				if (File.Exists(text6))
				{
					if (!File.Exists(text5) || FileHash(text6) != FileHash(text5))
					{
						throw new IOException("The launcher differs from the installed Remastered copy; nothing was removed: " + text4);
					}
					list.Add(text6);
				}
				list.Add(text5);
				list.Add(text7);
			}
			foreach (string item in list)
			{
				NoLinks(Path.GetDirectoryName(item));
				RejectLinkedFile(item);
			}
			Log("Removing the active Remastered installation...", 10);
			GameClosed();
			foreach (string item2 in list)
			{
				if (File.Exists(item2))
				{
					File.Delete(item2);
				}
			}
			File.Delete(path);
			string path2 = Under(text, "data");
			if (Directory.Exists(path2))
			{
				foreach (string item3 in from x in Directory.EnumerateDirectories(path2, "*", SearchOption.AllDirectories)
					orderby x.Length descending
					select x)
				{
					if (!Directory.EnumerateFileSystemEntries(item3).Any())
					{
						Directory.Delete(item3);
					}
				}
			}
			array4 = new string[3]
			{
				Under(text, "data"),
				Under(text, "previous-launchers"),
				text
			};
			foreach (string path3 in array4)
			{
				if (Directory.Exists(path3) && !Directory.EnumerateFileSystemEntries(path3).Any())
				{
					Directory.Delete(path3);
				}
			}
			Log(Directory.Exists(text) ? "Uninstalled. Unrecognized files in RemasteredCE were retained." : "Uninstalled Remastered CE. Vanilla files and previous-version backups were retained.", 100);
		}
	}

	private static void RejectLinkedFile(string path)
	{
		if (File.Exists(path) && (File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0)
		{
			throw new IOException("Linked installed files are not supported: " + path);
		}
	}

	private static void PreserveCustomDataPacks(string installed, string stage)
	{
		string data = Under(installed, "data");
		if (!Directory.Exists(data)) return;
		NoLinks(data);
		var owned = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
		foreach (string name in GameLayout.BasePacks) owned.Add("data/" + name);
		string record = Under(installed, "install-state.json");
		RejectLinkedFile(record);
		if (File.Exists(record))
		{
			var state = J.Parse(File.ReadAllText(record));
			var paths = new List<string>();
			if (state.ContainsKey("files")) foreach (var item in J.Arr(state["files"])) paths.Add(J.S(J.Obj(item), "file"));
			if (state.ContainsKey("baseDataFiles")) foreach (var item in J.Arr(state["baseDataFiles"])) paths.Add(Convert.ToString(item));
			foreach (string value in paths)
			{
				string relative = (value ?? "").Replace('\\', '/');
				if (!relative.StartsWith("data/", StringComparison.OrdinalIgnoreCase)) continue;
				string checkedPath = Under(installed, relative);
				owned.Add(checkedPath.Substring(Path.GetFullPath(installed).TrimEnd('\\').Length + 1).Replace('\\', '/'));
			}
		}
		var directories = new Stack<string>();
		directories.Push(data);
		while (directories.Count != 0)
		{
			string folder = directories.Pop();
			NoLinks(folder);
			foreach (string child in Directory.EnumerateDirectories(folder)) { NoLinks(child); directories.Push(child); }
			foreach (string file in Directory.EnumerateFiles(folder, "*.pack", SearchOption.TopDirectoryOnly))
			{
				RejectLinkedFile(file);
				string relative = "data/" + file.Substring(data.TrimEnd('\\').Length + 1).Replace('\\', '/');
				if (owned.Contains(relative)) continue;
				string destination = Under(stage, relative);
				NoLinks(Path.GetDirectoryName(destination));
				RejectLinkedFile(destination);
				if (File.Exists(destination) || Directory.Exists(destination))
					throw new IOException("A custom data pack conflicts with the staged game data. The current installation was retained: " + relative);
				Directory.CreateDirectory(Path.GetDirectoryName(destination));
				string expected = FileHash(file);
				File.Copy(file, destination, false);
				if (FileHash(destination) != expected || FileHash(file) != expected)
					throw new IOException("A custom data pack changed while preserving it: " + relative);
			}
		}
	}

	public static void PublishVerified(string stage, string ce, string previous)
	{
		string text = Under(ce, "RemasteredCE");
		NoLinks(stage);
		NoLinks(text);
		NoLinks(previous);
		if (!Path.GetFullPath(stage).StartsWith(Path.GetFullPath(ce).TrimEnd('\\') + "\\", StringComparison.OrdinalIgnoreCase) || !Path.GetFileName(stage).StartsWith("RemasteredCE.staging_", StringComparison.Ordinal))
		{
			throw new IOException("Invalid publication staging folder.");
		}
		PreserveCustomDataPacks(text, stage);
		HashSet<string> hashSet = new HashSet<string>();
		List<string> list = new List<string>();
		bool flag = false;
		bool flag2 = false;
		bool flag3 = false;
		Directory.CreateDirectory(Under(stage, "previous-launchers"));
		string[] array = new string[2] { "Launch_Remastered_CE.exe", "RemasteredCE_Bootstrap.exe" };
		foreach (string text2 in array)
		{
			if (File.Exists(Under(ce, text2)))
			{
				File.Copy(Under(ce, text2), Under(stage, "previous-launchers/" + text2), overwrite: true);
				hashSet.Add(text2);
			}
		}
		try
		{
			if (Directory.Exists(text))
			{
				Directory.Move(text, previous);
				flag = true;
			}
			Directory.Move(stage, text);
			flag2 = true;
			string text3 = Under(previous, "mods");
			if (flag && Directory.Exists(text3))
			{
				NoLinks(text3);
				string text4 = Under(text, "mods");
				if (Directory.Exists(text4))
				{
					throw new IOException("New staging unexpectedly contains a mods folder.");
				}
				Directory.Move(text3, text4);
				flag3 = true;
			}
			array = new string[2] { "RemasteredCE_Bootstrap.exe", "Launch_Remastered_CE.exe" };
			foreach (string text5 in array)
			{
				string text6 = Under(ce, text5 + ".installing");
				File.Copy(Under(text, text5), text6, overwrite: true);
				if (File.Exists(Under(ce, text5)))
				{
					File.Replace(text6, Under(ce, text5), null);
				}
				else
				{
					File.Move(text6, Under(ce, text5));
				}
				list.Add(text5);
			}
		}
		catch (Exception item)
		{
			List<Exception> list2 = new List<Exception>();
			list2.Add(item);
			foreach (string item4 in list.AsEnumerable().Reverse())
			{
				try
				{
					if (hashSet.Contains(item4))
					{
						File.Copy(Under(text, "previous-launchers/" + item4), Under(ce, item4), overwrite: true);
					}
					else
					{
						File.Delete(Under(ce, item4));
					}
				}
				catch (Exception item2)
				{
					list2.Add(item2);
				}
			}
			try
			{
				if (flag3)
				{
					Directory.Move(Under(text, "mods"), Under(previous, "mods"));
				}
				if (flag2)
				{
					Directory.Move(text, stage);
				}
				if (flag)
				{
					Directory.Move(previous, text);
				}
			}
			catch (Exception item3)
			{
				list2.Add(item3);
			}
			if (list2.Count > 1)
			{
				throw new AggregateException("Update rollback needs attention. Keep the game closed; previous files have been retained.", list2);
			}
			throw;
		}
		finally
		{
			array = new string[2] { "RemasteredCE_Bootstrap.exe", "Launch_Remastered_CE.exe" };
			foreach (string text7 in array)
			{
				string path = Under(ce, text7 + ".installing");
				if (File.Exists(path))
				{
					File.Delete(path);
				}
			}
		}
	}

	public static string InstalledVersion(string game)
	{
		try
		{
			return J.S(J.Parse(File.ReadAllText(Under(game, "RemasteredCE/install-state.json"))), "version");
		}
		catch
		{
			return "not installed";
		}
	}

	public static void LogLauncherError(Exception ex)
	{
		try
		{
			string text = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "RemasteredCE");
			Directory.CreateDirectory(text);
			File.AppendAllText(Path.Combine(text, "launcher-errors.log"), DateTime.UtcNow.ToString("o") + " " + ex?.ToString() + Environment.NewLine);
		}
		catch
		{
		}
	}
}
