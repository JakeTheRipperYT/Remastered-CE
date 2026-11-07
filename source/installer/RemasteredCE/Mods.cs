using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using Microsoft.Win32;

namespace RemasteredCE;

public static class Mods
{
	public const string ManagerName = "RemasteredCE_Launcher.exe";

	public static readonly StringComparer Names = StringComparer.OrdinalIgnoreCase;

	public static string SessionRoot => Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "RemasteredCE", "mods");

	public static string UserScript => Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "The Creative Assembly", "Shogun2CompleteEdition", "Steam", "scripts", "user.script.txt");

	public static string Identity(string text)
	{
		using SHA256 sHA = SHA256.Create();
		return BitConverter.ToString(sHA.ComputeHash(Encoding.UTF8.GetBytes(text))).Replace("-", "").ToLowerInvariant();
	}

	public static string Hash(string path)
	{
		using FileStream inputStream = File.OpenRead(path);
		using SHA256 sHA = SHA256.Create();
		return BitConverter.ToString(sHA.ComputeHash(inputStream)).Replace("-", "").ToLowerInvariant();
	}

	public static string SettingsRoot(string game)
	{
		return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "RemasteredCE", "mods", Identity(Path.GetFullPath(game).TrimEnd('\\').ToLowerInvariant()).Substring(0, 16));
	}

	public static bool GameRunning()
	{
		return new string[3] { "shogun2_complete_edition", "RemasteredCE_Bootstrap", "RemasteredCE_Sim8" }.Any((string n) => Process.GetProcessesByName(n).Length != 0);
	}

	public static void Atomic(string path, byte[] bytes)
	{
		Directory.CreateDirectory(Path.GetDirectoryName(path));
		string text = path + ".tmp_" + Guid.NewGuid().ToString("N");
		try
		{
			File.WriteAllBytes(text, bytes);
			if (File.Exists(path))
			{
				File.Replace(text, path, null);
			}
			else
			{
				File.Move(text, path);
			}
		}
		finally
		{
			if (File.Exists(text))
			{
				File.Delete(text);
			}
		}
	}

	public static void JsonFile(string path, object value)
	{
		Atomic(path, new UTF8Encoding(encoderShouldEmitUTF8Identifier: false).GetBytes(J.Json().Serialize(value)));
	}

	private static string CString(byte[] raw, ref int cursor)
	{
		int num = cursor;
		while (cursor < raw.Length && raw[cursor] != 0 && cursor - num <= 4096)
		{
			cursor++;
		}
		if (cursor >= raw.Length || cursor - num > 4096)
		{
			throw new InvalidDataException("Invalid pack string.");
		}
		string result = new UTF8Encoding(encoderShouldEmitUTF8Identifier: false, throwOnInvalidBytes: true).GetString(raw, num, cursor - num);
		cursor++;
		return result;
	}

	public static ModPack ReadPack(string path, string source, bool gameData)
	{
		ModPack modPack = new ModPack
		{
			Path = Path.GetFullPath(path),
			Name = Path.GetFileName(path),
			Source = source
		};
		try
		{
			if (modPack.Name.IndexOfAny(new char[4] { '"', ';', '\r', '\n' }) >= 0)
			{
				throw new InvalidDataException("Unsupported characters in pack name.");
			}
			using FileStream fileStream = File.Open(modPack.Path, FileMode.Open, FileAccess.Read, FileShare.Read);
			using BinaryReader binaryReader = new BinaryReader(fileStream);
			modPack.Bytes = fileStream.Length;
			byte[] array = binaryReader.ReadBytes(4);
			if (array.Length == 4 && Encoding.ASCII.GetString(array).StartsWith("MFH", StringComparison.Ordinal))
			{
				throw new InvalidDataException("Legacy Workshop container: use its extracted PFH pack.");
			}
			modPack.Format = Encoding.ASCII.GetString(array);
			bool flag = modPack.Format == "PFHs";
			if (!flag && modPack.Format != "PFH3" && modPack.Format != "PFH2" && modPack.Format != "PFH0")
			{
				throw new InvalidDataException("Not a supported Shogun 2 pack (PFHs or PFH0/2/3).");
			}
			uint num = binaryReader.ReadUInt32();
			uint num2 = binaryReader.ReadUInt32();
			uint num3 = binaryReader.ReadUInt32();
			uint num4 = binaryReader.ReadUInt32();
			uint num5 = binaryReader.ReadUInt32();
			modPack.Type = (int)(num & 0xF);
			modPack.AutoLoaded = gameData && modPack.Type == 4;
			bool compressed = (flag || modPack.Format == "PFH3") && (num & 0x20) != 0;
			if ((num & (uint)(~((flag || modPack.Format == "PFH3") ? 111 : 79))) != 0 || modPack.Type > 4 || num3 > 2097152 || num5 > 67108864 || num4 > 1000000 || num2 > 10000)
			{
				throw new InvalidDataException("Unsupported or oversized pack index.");
			}
			if (modPack.Format != "PFH0")
			{
				binaryReader.ReadUInt64();
			}
			byte[] array2 = binaryReader.ReadBytes((int)num3);
			if (array2.Length != num3)
			{
				throw new EndOfStreamException();
			}
			List<string> list = new List<string>();
			int cursor = 0;
			for (uint num6 = 0u; num6 < num2; num6++)
			{
				string text = CString(array2, ref cursor);
				if (Path.GetFileName(text) != text || text.IndexOfAny(new char[4] { '"', ';', '\r', '\n' }) >= 0)
				{
					throw new InvalidDataException("Invalid dependency pack name.");
				}
				list.Add(text);
			}
			if (cursor != array2.Length)
			{
				throw new InvalidDataException("Invalid dependency index.");
			}
			modPack.Dependencies = list.ToArray();
			byte[] array3 = binaryReader.ReadBytes((int)num5);
			if (array3.Length != num5)
			{
				throw new EndOfStreamException();
			}
			cursor = 0;
			long num7 = fileStream.Position;
			List<Tuple<ulong, ulong>> list2 = new List<Tuple<ulong, ulong>>();
			for (uint num8 = 0u; num8 < num4; num8++)
			{
				ulong num9 = 0uL;
				if (flag)
				{
					if (cursor + 8 > array3.Length)
					{
						throw new EndOfStreamException();
					}
					num9 = BitConverter.ToUInt64(array3, cursor);
					cursor += 8;
				}
				if (cursor + 4 > array3.Length)
				{
					throw new EndOfStreamException();
				}
				uint num10 = BitConverter.ToUInt32(array3, cursor);
				cursor += 4;
				uint num11 = num10;
				if (compressed)
				{
					if (cursor + 4 > array3.Length)
					{
						throw new EndOfStreamException();
					}
					num11 = BitConverter.ToUInt32(array3, cursor);
					cursor += 4;
				}
				if ((num & 0x40) != 0)
				{
					cursor += 8;
				}
				if (cursor > array3.Length)
				{
					throw new EndOfStreamException();
				}
				string item = CString(array3, ref cursor).Replace('/', '\\');
				modPack.Files.Add(item);
				if (flag)
				{
					if (num9 < (ulong)fileStream.Position || num9 > (ulong)fileStream.Length || (ulong)num11 > (ulong)(fileStream.Length - (long)num9))
					{
						throw new InvalidDataException("Pack data range escapes the file.");
					}
					list2.Add(Tuple.Create(num9, num9 + num11));
				}
				else
				{
					num7 = checked(num7 + num11);
				}
			}
			if (cursor != array3.Length || (!flag && num7 != fileStream.Length))
			{
				throw new InvalidDataException("Pack index or data bounds do not match the file.");
			}
			if (flag)
			{
				ulong num12 = (ulong)fileStream.Position;
				foreach (Tuple<ulong, ulong> item2 in list2.OrderBy((Tuple<ulong, ulong> x) => x.Item1))
				{
					if (item2.Item1 < num12)
					{
						throw new InvalidDataException("Overlapping pack payload ranges.");
					}
					num12 = item2.Item2;
				}
			}
		}
		catch (Exception ex) when (ex is IOException || ex is InvalidDataException || ex is UnauthorizedAccessException || ex is ArgumentException || ex is OverflowException)
		{
			modPack.Error = ex.Message;
		}
		return modPack;
	}

	public static List<string> SteamApps(string game)
	{
		HashSet<string> hashSet = new HashSet<string>(Names);
		DirectoryInfo parent = Directory.GetParent(game);
		if (parent != null && parent.Parent != null)
		{
			hashSet.Add(parent.Parent.FullName);
		}
		string text = Convert.ToString(Registry.GetValue("HKEY_CURRENT_USER\\Software\\Valve\\Steam", "SteamPath", ""));
		if (Directory.Exists(text))
		{
			hashSet.Add(Path.Combine(text, "steamapps"));
			string path = Path.Combine(text, "steamapps", "libraryfolders.vdf");
			if (File.Exists(path))
			{
				foreach (Match item in Regex.Matches(File.ReadAllText(path), "\\\"path\\\"\\s+\\\"([^\\\"]+)\\\""))
				{
					hashSet.Add(Path.Combine(item.Groups[1].Value.Replace("\\\\", "\\"), "steamapps"));
				}
			}
		}
		return (from p in hashSet.Where(Directory.Exists)
			select Path.GetFullPath(p).TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar)).Distinct(Names).OrderBy((string x) => x, Names).ToList();
	}

	private static IEnumerable<string> Packs(string folder, int depth)
	{
		if (!Directory.Exists(folder) || (File.GetAttributes(folder) & FileAttributes.ReparsePoint) != 0)
		{
			yield break;
		}
		string[] files;
		string[] dirs;
		try
		{
			files = Directory.GetFiles(folder, "*.pack");
			dirs = ((depth > 0) ? Directory.GetDirectories(folder) : new string[0]);
		}
		catch (IOException)
		{
			yield break;
		}
		catch (UnauthorizedAccessException)
		{
			yield break;
		}
		string[] array = files;
		foreach (string text in array)
		{
			if ((File.GetAttributes(text) & FileAttributes.ReparsePoint) == 0)
			{
				yield return text;
			}
		}
		array = dirs;
		foreach (string folder2 in array)
		{
			foreach (string item in Packs(folder2, depth - 1))
			{
				yield return item;
			}
		}
	}

	public static List<ModPack> Discover(string game, IEnumerable<string> extra, IEnumerable<string> steamApps = null)
	{
		Dictionary<string, ModPack> found = new Dictionary<string, ModPack>(Names);
		Action<string, string, int, bool> action = (string dir, string label, int depth, bool data) =>
		{
			foreach (string item in Packs(dir, depth))
			{
				if (found.Count >= 15000)
				{
					throw new IOException("Too many packs. Choose a more specific mods folder.");
				}
				string fullPath = Path.GetFullPath(item);
				bool baseData = GameDataFolders(game).Any(folder => Names.Equals(Path.GetDirectoryName(fullPath), Path.GetFullPath(folder)));
				if ((!baseData || (!GameLayout.BasePacks.Contains(Path.GetFileName(fullPath), Names) && !Names.Equals(Path.GetFileName(fullPath), GameLayout.CampaignNightPack))) && !found.ContainsKey(fullPath))
				{
					ModPack modPack = ReadPack(fullPath, label, data);
					if (!data || modPack.Error != null || modPack.Type == 3 || modPack.Type == 4)
					{
						if (!data && modPack.Error == null && modPack.Type != 3 && modPack.Type != 4)
						{
							modPack.Error = "This pack is not a mod/movie pack.";
						}
						found.Add(fullPath, modPack);
					}
				}
			}
		};
		action(Path.Combine(game, "data"), "Game data", 0, arg4: true);
		action(Path.Combine(game, "RemasteredCE", "data"), "Remastered CE data", 0, arg4: true);
		action(Path.Combine(game, "RemasteredCE", "mods"), "Remastered CE mods", 4, arg4: false);
		foreach (string item2 in steamApps ?? SteamApps(game))
		{
			string path = Path.Combine(item2, "workshop", "content", "3846830");
			if (!Directory.Exists(path))
			{
				continue;
			}
			string[] directories = Directory.GetDirectories(path);
			foreach (string text in directories)
			{
				string fileName = Path.GetFileName(text);
				if (fileName.All(char.IsDigit))
				{
					action(text, "Workshop " + fileName, 3, arg4: false);
				}
			}
		}
		foreach (string item3 in extra ?? new string[0])
		{
			action(item3, "Custom folder", 4, arg4: false);
		}
		return found.Values.OrderBy((ModPack x) => x.Name, Names).ThenBy((ModPack x) => x.Path, Names).ToList();
	}

	public static string[] GameDataFolders(string game)
	{
		return new[] { Path.Combine(game, "RemasteredCE", "data"), Path.Combine(game, "data") };
	}

	public static void ApplyProfile(List<ModPack> packs, ModProfile profile)
	{
		HashSet<string> hashSet = new HashSet<string>(profile.Enabled ?? new string[0], Names);
		foreach (ModPack pack in packs)
		{
			pack.Enabled = pack.AutoLoaded || hashSet.Contains(pack.Path);
		}
		Dictionary<string, int> ranks = (profile.Order ?? new string[0]).Select((string p, int i) => new { p, i }).GroupBy(x => x.p, Names).ToDictionary(g => g.Key, g => g.First().i, Names);
		packs.Sort((ModPack a, ModPack b) =>
		{
			if (!ranks.TryGetValue(a.Path, out var value))
			{
				value = int.MaxValue;
			}
			if (!ranks.TryGetValue(b.Path, out var value2))
			{
				value2 = int.MaxValue;
			}
			int num = value.CompareTo(value2);
			return (num == 0) ? Names.Compare(a.Name, b.Name) : num;
		});
	}

	public static List<ModPack> AutoSort(IEnumerable<ModPack> items)
	{
		List<ModPack> list = items.ToList();
		Dictionary<string, List<ModPack>> dictionary = list.GroupBy((ModPack p) => p.Name, Names).ToDictionary((IGrouping<string, ModPack> g) => g.Key, (IGrouping<string, ModPack> g) => g.ToList(), Names);
		Dictionary<ModPack, List<ModPack>> dictionary2 = list.ToDictionary((ModPack p) => p, (ModPack p) => new List<ModPack>());
		Dictionary<ModPack, int> degree = list.ToDictionary((ModPack p) => p, (ModPack p) => 0);
		foreach (ModPack item in list)
		{
			foreach (string item2 in item.Dependencies.Distinct(Names))
			{
				if (dictionary.TryGetValue(item2, out var value) && value.Count == 1)
				{
					dictionary2[item].Add(value[0]);
					degree[value[0]]++;
				}
			}
		}
		List<ModPack> result = new List<ModPack>();
		while (result.Count < list.Count)
		{
			ModPack modPack = list.Where((ModPack p) => degree[p] == 0 && !result.Contains(p)).OrderBy((ModPack p) => p.Name, Names).ThenBy((ModPack p) => p.Path, Names)
				.FirstOrDefault();
			if (modPack == null)
			{
				throw new InvalidDataException("These packs declare a dependency cycle. Keep the manual order and review their dependencies.");
			}
			result.Add(modPack);
			foreach (ModPack item3 in dictionary2[modPack])
			{
				degree[item3]--;
			}
		}
		return result;
	}

	public static List<string> Issues(IEnumerable<ModPack> items, string game)
	{
		List<ModPack> list = items.Where((ModPack p) => p.Enabled).ToList();
		List<string> list2 = new List<string>();
		foreach (ModPack item in list)
		{
			if (item.Error != null)
			{
				list2.Add(item.Name + ": " + item.Error);
			}
		}
		foreach (IGrouping<string, ModPack> item2 in from g in list.GroupBy((ModPack p) => p.Name, Names)
			where g.Count() > 1
			select g)
		{
			list2.Add("Choose one copy of " + item2.Key + "; duplicate enabled filenames are ambiguous.");
		}
		foreach (ModPack item3 in list.Where((ModPack p) => !p.AutoLoaded))
		{
			string path = Path.Combine(game, "data", item3.Name);
			if (File.Exists(path) && !Names.Equals(Path.GetFullPath(path), Path.GetFullPath(item3.Path)))
			{
				list2.Add(item3.Name + ": a pack with this filename already exists in game data. Select that Game data copy, or move the conflicting data copy out before using this one.");
			}
		}
		HashSet<string> hashSet = new HashSet<string>(list.Select((ModPack p) => p.Name), Names);
		foreach (ModPack item4 in list)
		{
			string[] dependencies = item4.Dependencies;
			foreach (string text in dependencies)
			{
				if (!hashSet.Contains(text))
				{
					string path2 = Path.Combine(game, "data", text);
					bool flag = false;
					if (File.Exists(path2))
					{
						ModPack modPack = ReadPack(path2, "Game data", gameData: true);
						flag = modPack.Error == null && modPack.Type <= 2;
					}
					if (!flag)
					{
						list2.Add(item4.Name + " requires enabling " + text + ".");
					}
				}
			}
		}
		try
		{
			AutoSort(list);
		}
		catch (InvalidDataException ex)
		{
			list2.Add(ex.Message);
		}
		return list2;
	}

	public static string OverlapSummary(IEnumerable<ModPack> items)
	{
		HashSet<string> hashSet = new HashSet<string>(Names);
		int num = 0;
		foreach (ModPack item in items.Where((ModPack x) => x.Enabled))
		{
			foreach (string file in item.Files)
			{
				if (!hashSet.Add(file))
				{
					num++;
				}
			}
		}
		if (num != 0)
		{
			return num + " overlapping file paths. Load order determines priority; database/script conflicts may need author guidance.";
		}
		return "No identical file paths overlap. This does not establish full mod compatibility.";
	}

	public static void SaveProfile(string folder, ModProfile profile, List<ModPack> packs)
	{
		if (string.IsNullOrWhiteSpace(profile.Name) || profile.Name.Length > 80)
		{
			throw new ArgumentException("Choose a profile name of 1-80 characters.");
		}
		profile.Order = packs.Select((ModPack p) => p.Path).ToArray();
		profile.Enabled = (from p in packs
			where p.Enabled && !p.AutoLoaded
			select p.Path).ToArray();
		JsonFile(Path.Combine(folder, "profiles", Identity(profile.Name) + ".json"), profile);
		JsonFile(Path.Combine(folder, "selected-profile.json"), new
		{
			name = profile.Name
		});
	}

	public static ModProfile[] Profiles(string folder)
	{
		string path = Path.Combine(folder, "profiles");
		if (!Directory.Exists(path))
		{
			return new ModProfile[1]
			{
				new ModProfile()
			};
		}
		List<ModProfile> list = new List<ModProfile>();
		string[] files = Directory.GetFiles(path, "*.json");
		foreach (string path2 in files)
		{
			try
			{
				ModProfile modProfile = J.Json().Deserialize<ModProfile>(File.ReadAllText(path2));
				if (modProfile != null && modProfile.Name != null)
				{
					modProfile.Folders = modProfile.Folders ?? new string[0];
					modProfile.Order = modProfile.Order ?? new string[0];
					modProfile.Enabled = modProfile.Enabled ?? new string[0];
					list.Add(modProfile);
				}
			}
			catch (Exception ex) when (ex is IOException || ex is ArgumentException || ex is InvalidOperationException)
			{
			}
		}
		if (list.Count != 0)
		{
			return list.OrderBy((ModProfile p) => p.Name, Names).ToArray();
		}
		return new ModProfile[1]
		{
			new ModProfile()
		};
	}

	public static string Stage(List<ModPack> packs, string folder, Action<string> progress)
	{
		string text = Path.Combine(folder, "active");
		Directory.CreateDirectory(text);
		Engine.NoLinks(text);
		string path = Path.Combine(folder, "active-files.json");
		Dictionary<string, string> dictionary = (File.Exists(path) ? new Dictionary<string, string>(J.Json().Deserialize<Dictionary<string, string>>(File.ReadAllText(path)), Names) : new Dictionary<string, string>(Names));
		Dictionary<string, string> dictionary2 = new Dictionary<string, string>(Names);
		string[] files = Directory.GetFiles(text, "*.pack");
		foreach (string text2 in files)
		{
			if (!dictionary.ContainsKey(Path.GetFileName(text2)))
			{
				throw new IOException("Unrecognized pack in the managed active cache: " + text2);
			}
		}
		foreach (ModPack item in packs.Where((ModPack p) => p.Enabled && !p.AutoLoaded))
		{
			progress("Preparing " + item.Name + "…");
			string text3 = Hash(item.Path);
			string text4 = Path.Combine(text, item.Name);
			if (File.Exists(text4) && (!dictionary.TryGetValue(item.Name, out var value) || Hash(text4) != value))
			{
				throw new IOException("A staged pack was edited; keep it and review: " + text4);
			}
			if (!File.Exists(text4) || Hash(text4) != text3)
			{
				string text5 = text4 + ".building_" + Guid.NewGuid().ToString("N");
				try
				{
					File.Copy(item.Path, text5);
					if (Hash(text5) != text3)
					{
						throw new IOException("Mod changed while being copied: " + item.Name);
					}
					if (File.Exists(text4))
					{
						File.Replace(text5, text4, null);
					}
					else
					{
						File.Move(text5, text4);
					}
				}
				finally
				{
					if (File.Exists(text5))
					{
						File.Delete(text5);
					}
				}
			}
			dictionary2.Add(item.Name, text3);
			dictionary[item.Name] = text3;
			JsonFile(path, dictionary);
		}
		KeyValuePair<string, string>[] array = dictionary.ToArray();
		for (int i = 0; i < array.Length; i++)
		{
			KeyValuePair<string, string> keyValuePair = array[i];
			if (dictionary2.ContainsKey(keyValuePair.Key))
			{
				continue;
			}
			if (Path.GetFileName(keyValuePair.Key) != keyValuePair.Key)
			{
				throw new InvalidDataException("Invalid active cache ownership record.");
			}
			string text6 = Path.Combine(text, keyValuePair.Key);
			if (File.Exists(text6))
			{
				if (Hash(text6) != keyValuePair.Value)
				{
					throw new IOException("An old staged pack was edited: " + text6);
				}
				File.Delete(text6);
			}
		}
		JsonFile(path, dictionary2);
		return text;
	}

	public static string WithoutModCommands(string text)
	{
		List<Tuple<int, int>> list = new List<Tuple<int, int>>();
		bool flag = false;
		bool flag2 = false;
		int num = -1;
		string text2 = "";
		for (int i = 0; i < text.Length; i++)
		{
			char c = text[i];
			if (flag2)
			{
				if (c == '#')
				{
					flag2 = false;
				}
				continue;
			}
			if (!flag && c == '#')
			{
				flag2 = true;
				continue;
			}
			if (c == '"')
			{
				flag = !flag;
				continue;
			}
			if (!flag && num < 0 && !char.IsWhiteSpace(c))
			{
				num = i;
				int j;
				for (j = i; j < text.Length && (char.IsLetter(text[j]) || text[j] == '_'); j++)
				{
				}
				text2 = text.Substring(i, j - i);
			}
			if (!flag && c == ';')
			{
				if (num >= 0 && (text2 == "mod" || text2 == "add_working_directory"))
				{
					list.Add(Tuple.Create(num, i + 1));
				}
				num = -1;
				text2 = "";
			}
		}
		if ((flag | flag2) || num >= 0)
		{
			throw new InvalidDataException("The existing user script has an incomplete command, quote or paired # comment. Review it before launching.");
		}
		StringBuilder stringBuilder = new StringBuilder(text);
		foreach (Tuple<int, int> item in list.AsEnumerable().Reverse())
		{
			stringBuilder.Remove(item.Item1, item.Item2 - item.Item1);
		}
		return stringBuilder.ToString();
	}

	public static string ComposeScript(string original, string active, List<ModPack> packs)
	{
		if (active.IndexOfAny(new char[4] { '"', ';', '\r', '\n' }) >= 0)
		{
			throw new IOException("Unsupported characters in the mod cache path.");
		}
		StringBuilder stringBuilder = new StringBuilder(WithoutModCommands(original));
		stringBuilder.AppendLine().AppendLine("# Remastered CE mod profile (restored after this game session) #");
		if (packs.Any((ModPack p) => p.Enabled && !p.AutoLoaded))
		{
			stringBuilder.Append("add_working_directory \"").Append(active.Replace('\\', '/')).AppendLine("\";");
		}
		foreach (ModPack item in packs.Where((ModPack p) => p.Enabled && !p.AutoLoaded && p.Type == 3))
		{
			stringBuilder.Append("mod \"").Append(item.Name).AppendLine("\";");
		}
		return stringBuilder.ToString();
	}

	public static string QuoteArgument(string value)
	{
		if (value.Length > 0 && !value.Any((char ch) => char.IsWhiteSpace(ch) || ch == '"'))
		{
			return value;
		}
		StringBuilder stringBuilder = new StringBuilder("\"");
		int num = 0;
		foreach (char c in value)
		{
			switch (c)
			{
			case '\\':
				num++;
				continue;
			case '"':
				stringBuilder.Append('\\', num * 2 + 1);
				stringBuilder.Append(c);
				break;
			default:
				stringBuilder.Append('\\', num);
				stringBuilder.Append(c);
				break;
			}
			num = 0;
		}
		stringBuilder.Append('\\', num * 2).Append('"');
		return stringBuilder.ToString();
	}
}
