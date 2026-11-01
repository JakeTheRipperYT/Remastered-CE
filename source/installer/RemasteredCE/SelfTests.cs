using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Threading;

namespace RemasteredCE;

internal static class SelfTests
{
	public static void Run(string path)
	{
		List<string> list = new List<string>();
		string root = Path.Combine(Path.GetTempPath(), "RCE-test");
		bool flag = false;
		try
		{
			Engine.Under(root, "../escape");
		}
		catch (InvalidDataException)
		{
			flag = true;
		}
		if (!flag)
		{
			throw new Exception("Path traversal test failed.");
		}
		list.Add("PASS: path traversal rejected");
		byte[] bytes = Encoding.ASCII.GetBytes("abcdefgh");
		object[] operations = new object[2]
		{
			new Dictionary<string, object>
			{
				{ "copy", 2 },
				{ "length", 3 }
			},
			new Dictionary<string, object> { 
			{
				"data",
				Convert.ToBase64String(Encoding.ASCII.GetBytes("XYZ"))
			} }
		};
		if (Encoding.ASCII.GetString(Engine.Transform(bytes, operations)) != "cdeXYZ")
		{
			throw new Exception("Transform failed.");
		}
		list.Add("PASS: source-copy and write instructions");
		if (!Lz4.Decode(Lz4.Encode(bytes, "fast", 0), bytes.Length).SequenceEqual(bytes))
		{
			throw new Exception("LZ4 failed.");
		}
		list.Add("PASS: embedded LZ4 roundtrip");
		if (Assembly.GetExecutingAssembly().GetManifestResourceNames().Contains("release"))
		{
			using (Release.Load(null))
			{
				list.Add("PASS: embedded release signature");
				byte[] array = Release.Resource("release");
				array[array.Length - 1] ^= 1;
				string path2 = Path.Combine(Path.GetTempPath(), "RCE-tampered-" + Guid.NewGuid().ToString("N") + ".rce");
				File.WriteAllBytes(path2, array);
				try
				{
					flag = false;
					try
					{
						using (Release.Load(path2))
						{
						}
					}
					catch (InvalidDataException)
					{
						flag = true;
					}
					if (!flag)
					{
						throw new Exception("Tampered package accepted.");
					}
					list.Add("PASS: tampered release rejected");
				}
				finally
				{
					File.Delete(path2);
				}
			}
		}
		string text = Path.Combine(Path.GetTempPath(), "RCE-publication-test-" + Guid.NewGuid().ToString("N"));
		Directory.CreateDirectory(text);
		try
		{
			string text2 = Engine.Under(text, "RemasteredCE");
			string text3 = Engine.Under(text, "RemasteredCE.staging_test");
			string text4 = Engine.Under(text, "RemasteredCE.previous_test");
			Directory.CreateDirectory(text2);
			Directory.CreateDirectory(text3);
			File.WriteAllText(Engine.Under(text2, "old.txt"), "old installation");
			File.WriteAllText(Engine.Under(text, "Launch_Remastered_CE.exe"), "old launcher");
			File.WriteAllText(Engine.Under(text, "RemasteredCE_Bootstrap.exe"), "old bootstrap");
			File.WriteAllText(Engine.Under(text3, "RemasteredCE_Bootstrap.exe"), "new bootstrap");
			flag = false;
			try
			{
				Engine.PublishVerified(text3, text, text4);
			}
			catch (FileNotFoundException)
			{
				flag = true;
			}
			if (!flag || !File.Exists(Engine.Under(text2, "old.txt")) || File.ReadAllText(Engine.Under(text, "RemasteredCE_Bootstrap.exe")) != "old bootstrap" || File.ReadAllText(Engine.Under(text, "Launch_Remastered_CE.exe")) != "old launcher")
			{
				throw new Exception("Publication rollback failed.");
			}
			list.Add("PASS: failed update restores previous folder and already-replaced bootstrap");
			File.WriteAllText(Engine.Under(text3, "Launch_Remastered_CE.exe"), "new launcher");
			Engine.PublishVerified(text3, text, text4);
			if (!File.Exists(Engine.Under(text4, "old.txt")) || File.ReadAllText(Engine.Under(text, "Launch_Remastered_CE.exe")) != "new launcher")
			{
				throw new Exception("Publication commit failed.");
			}
			list.Add("PASS: verified update publishes and preserves previous installation");
		}
		finally
		{
			Engine.NoLinks(text);
			if (!Path.GetFileName(text).StartsWith("RCE-publication-test-", StringComparison.Ordinal))
			{
				throw new Exception("Invalid self-test cleanup target.");
			}
			Directory.Delete(text, recursive: true);
		}
		string[] array3;
		for (int i = 4; i <= 8; i++)
		{
			string text5 = Path.Combine(Path.GetTempPath(), "RCE-uninstall-test-" + Guid.NewGuid().ToString("N"));
			Directory.CreateDirectory(text5);
			try
			{
				string live = Engine.Under(text5, "RemasteredCE");
				string path3 = Engine.Under(live, "install-state.json");
				Directory.CreateDirectory(Engine.Under(live, "data"));
				Directory.CreateDirectory(Engine.Under(live, "previous-launchers"));
				string[] array2 = new string[8] { "data/data.pack", "data/shaders.pack", "data/bp_orig.pack", "data/web_content.pack", "data/local_global.pack", "data/models.pack", "data/audio.pack", "data/movies.pack" }.Take(i).ToArray();
				File.WriteAllText(Engine.Under(text5, "shogun2_complete_edition.exe"), "vanilla executable");
				Directory.CreateDirectory(Engine.Under(text5, "data"));
				File.WriteAllText(Engine.Under(text5, "data/data.pack"), "vanilla pack");
				Directory.CreateDirectory(Engine.Under(text5, "RemasteredCE.previous_test"));
				File.WriteAllText(Engine.Under(text5, "RemasteredCE.previous_test/keep.txt"), "previous version");
				array3 = array2;
				foreach (string relative in array3)
				{
					File.WriteAllText(Engine.Under(live, relative), "modified pack");
				}
				File.WriteAllText(Engine.Under(live, "CE.dll"), "modified engine");
				array3 = new string[2] { "Launch_Remastered_CE.exe", "RemasteredCE_Bootstrap.exe" };
				foreach (string text6 in array3)
				{
					File.WriteAllText(Engine.Under(live, text6), text6);
					File.WriteAllText(Engine.Under(text5, text6), text6);
					File.WriteAllText(Engine.Under(live, "previous-launchers/" + text6), "previous launcher");
				}
				File.WriteAllText(Engine.Under(live, "shogun2_complete_edition.exe"), "copied bootstrap");
				File.WriteAllText(Engine.Under(live, "nvngx_dlss.dll"), "copied NVIDIA runtime");
				File.WriteAllText(Engine.Under(text5, "nvngx_dlss.dll"), "vanilla NVIDIA runtime");
				Directory.CreateDirectory(Engine.Under(text5, "data/subfolder"));
				File.WriteAllText(Engine.Under(text5, "data/subfolder/base.txt"), "base data");
				string[] array4 = new Engine().LinkBaseData(text5, live);
				if (array4.Length != 1 || File.ReadAllText(Engine.Under(live, "data/subfolder/base.txt")) != "base data" || File.ReadAllText(Engine.Under(live, "data/data.pack")) != "modified pack")
				{
					throw new Exception("Base data linking failed.");
				}
				list.Add("PASS: base data links include nested files and preserve modified packs");
				Dictionary<string, object> dictionary = new Dictionary<string, object>
				{
					{ "schema", 1 },
					{ "layoutVersion", 2 },
					{ "engineHash", "fixture" },
					{
						"files",
						array2.Select((string x) => new Dictionary<string, object> { { "file", x } }).ToArray()
					}
				};
				dictionary["baseDataFiles"] = array4;
				Dictionary<string, object> dictionary2 = new Dictionary<string, object>(dictionary);
				dictionary2["files"] = new Dictionary<string, object>[1]
				{
					new Dictionary<string, object> { { "file", "../shogun2_complete_edition.exe" } }
				};
				File.WriteAllText(path3, J.Json().Serialize(dictionary2));
				flag = false;
				try
				{
					new Engine().Uninstall(text5);
				}
				catch (InvalidDataException)
				{
					flag = true;
				}
				if (!flag || !File.Exists(Engine.Under(live, "CE.dll")))
				{
					throw new Exception("Unsafe uninstall record was accepted.");
				}
				list.Add("PASS: uninstall rejects unexpected file paths before removing anything");
				File.WriteAllText(path3, J.Json().Serialize(dictionary));
				File.WriteAllText(Engine.Under(text5, "Launch_Remastered_CE.exe"), "unrecognized replacement");
				flag = false;
				try
				{
					new Engine().Uninstall(text5);
				}
				catch (IOException)
				{
					flag = true;
				}
				if (!flag || !File.Exists(Engine.Under(live, "CE.dll")))
				{
					throw new Exception("Unrecognized launcher was removed.");
				}
				list.Add("PASS: uninstall preserves an unrecognized root launcher and stops before deletion");
				File.WriteAllText(Engine.Under(text5, "Launch_Remastered_CE.exe"), "Launch_Remastered_CE.exe");
				File.WriteAllText(Engine.Under(live, "keep-user-file.txt"), "user file");
				new Engine().Uninstall(text5);
				if (File.Exists(Engine.Under(live, "data/subfolder/base.txt")) || File.Exists(Engine.Under(live, "shogun2_complete_edition.exe")) || File.Exists(Engine.Under(live, "nvngx_dlss.dll")) || File.Exists(path3) || File.Exists(Engine.Under(live, "CE.dll")) || array2.Any((string x) => File.Exists(Engine.Under(live, x))) || File.Exists(Engine.Under(text5, "Launch_Remastered_CE.exe")) || File.Exists(Engine.Under(text5, "RemasteredCE_Bootstrap.exe")))
				{
					throw new Exception("Uninstall left managed files.");
				}
				if (File.ReadAllText(Engine.Under(text5, "data/subfolder/base.txt")) != "base data" || File.ReadAllText(Engine.Under(text5, "nvngx_dlss.dll")) != "vanilla NVIDIA runtime" || File.ReadAllText(Engine.Under(text5, "shogun2_complete_edition.exe")) != "vanilla executable" || File.ReadAllText(Engine.Under(text5, "data/data.pack")) != "vanilla pack" || !File.Exists(Engine.Under(text5, "RemasteredCE.previous_test/keep.txt")) || !File.Exists(Engine.Under(live, "keep-user-file.txt")))
				{
					throw new Exception("Uninstall removed unrelated files.");
				}
				list.Add("PASS: " + i + "-pack uninstall preserves vanilla, user files and previous versions");
			}
			finally
			{
				Engine.NoLinks(text5);
				if (!Path.GetFileName(text5).StartsWith("RCE-uninstall-test-", StringComparison.Ordinal))
				{
					throw new Exception("Invalid uninstall-test cleanup target.");
				}
				Directory.Delete(text5, recursive: true);
			}
		}
		if (!OnlineUpdates.NeedsUpdate("0.1.9-preview", "0.1.10-preview") || OnlineUpdates.NeedsUpdate("0.1.10-preview", "0.1.9-preview") || OnlineUpdates.NeedsUpdate("0.1.3-preview", "0.1.3-preview") || ReleaseVersion.Parse("1.0.0-preview.10").CompareTo(ReleaseVersion.Parse("1.0.0-preview.2")) <= 0 || ReleaseVersion.Parse("1.0.0").CompareTo(ReleaseVersion.Parse("1.0.0-preview")) <= 0)
		{
			throw new Exception("Release version ordering failed.");
		}
		list.Add("PASS: updater orders versions numerically and avoids same-version installs and downgrades");
		List<object> list2 = new List<object>();
		array3 = new string[3] { "0.1.9-preview", "0.1.10-preview", "0.1.11-preview" };
		foreach (string text7 in array3)
		{
			list2.Add(new Dictionary<string, object>
			{
				{
					"tag_name",
					"v" + text7
				},
				{
					"draft",
					text7 == "0.1.11-preview"
				},
				{ "prerelease", true },
				{
					"assets",
					new Dictionary<string, object>[1]
					{
						new Dictionary<string, object>
						{
							{
								"name",
								"RemasteredCE-" + text7 + ".rce"
							},
							{ "state", "uploaded" },
							{ "size", 123 },
							{
								"browser_download_url",
								"https://github.com/JakeTheRipperYT/Remastered-CE/releases/download/v" + text7 + "/RemasteredCE-" + text7 + ".rce"
							}
						}
					}
				}
			});
		}
		string text8 = J.Json().Serialize(list2);
		OnlineRelease onlineRelease = OnlineUpdates.Select(text8);
		if (onlineRelease.Version != "0.1.10-preview")
		{
			throw new Exception("Release selection failed.");
		}
		list.Add("PASS: updater selects newest published package including prereleases and excludes drafts");
		flag = false;
		try
		{
			OnlineUpdates.Select(text8.Replace("https://github.com/", "https://untrusted.invalid/"));
		}
		catch (InvalidDataException)
		{
			flag = true;
		}
		if (!flag)
		{
			throw new Exception("External update URL accepted.");
		}
		list.Add("PASS: updater rejects download addresses outside the release repository");
		if (Assembly.GetExecutingAssembly().GetManifestResourceNames().Contains("release"))
		{
			string path4 = Path.Combine(Path.GetTempPath(), "RCE-version-test-" + Guid.NewGuid().ToString("N") + ".rce");
			File.WriteAllBytes(path4, Release.Resource("release"));
			try
			{
				flag = false;
				try
				{
					OnlineUpdates.ValidatePackage(path4, new OnlineRelease
					{
						Version = "9.9.9"
					});
				}
				catch (InvalidDataException)
				{
					flag = true;
				}
				if (!flag)
				{
					throw new Exception("Mismatched signed release version accepted.");
				}
			}
			finally
			{
				File.Delete(path4);
			}
			list.Add("PASS: updater rejects a signed package that differs from the advertised version");
		}
		flag = false;
		try
		{
			OnlineUpdates.Download(onlineRelease, Path.Combine(Path.GetTempPath(), "RCE-cancelled-download"), new CancellationToken(canceled: true), null);
		}
		catch (OperationCanceledException)
		{
			flag = true;
		}
		if (!flag)
		{
			throw new Exception("Download cancellation failed.");
		}
		list.Add("PASS: cancelled update download stops before making a request or changing game files");
		byte[] array5 = (from num in Enumerable.Range(0, 5242927)
			select (byte)(num * 31)).ToArray();
		using (MemoryStream memoryStream = new MemoryStream())
		{
			memoryStream.Write(array5, 0, array5.Length);
			memoryStream.SetLength(array5.Length + 97);
			Engine.ShiftPackBody(memoryStream, 53L, 97L, array5.Length);
			byte[] source = memoryStream.ToArray();
			if (!source.Take(53).SequenceEqual(array5.Take(53)) || source.Skip(53).Take(97).Any((byte x) => x != 0) || !source.Skip(150).SequenceEqual(array5.Skip(53)))
			{
				throw new Exception("Overlapping pack index expansion corrupted payload.");
			}
			flag = false;
			try
			{
				Engine.ShiftPackBody(memoryStream, 53L, 0L, array5.Length);
			}
			catch (InvalidDataException)
			{
				flag = true;
			}
			if (!flag)
			{
				throw new Exception("Invalid body shift accepted.");
			}
		}
		list.Add("PASS: overlapping multi-chunk pack expansion preserves original bytes and rejects invalid shifts");
		File.WriteAllLines(path, list);
	}
}
