using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;

namespace RemasteredCE;

public sealed class ModScriptSession : IDisposable
{
	public static ModScriptSession Prepare(string settings, string scriptPath, string active, List<ModPack> packs, bool useExistingScript, Func<bool> gameRunning = null)
	{
		var session = new ModScriptSession(settings, scriptPath, gameRunning);
		// Recover an interrupted managed session before either launch mode.
		session.Recover();
		if (useExistingScript)
		{
			return null;
		}
		session.Begin(active, packs);
		return session;
	}
	private readonly string script;

	private readonly string journal;

	private readonly Func<bool> running;

	public ModScriptSession(string settings, string scriptPath, Func<bool> gameRunning = null)
	{
		script = Path.GetFullPath(scriptPath);
		journal = Path.Combine(settings, "script-session.json");
		running = gameRunning ?? new Func<bool>(Mods.GameRunning);
	}

	public bool Recover()
	{
		if (!File.Exists(journal))
		{
			return false;
		}
		if (running())
		{
			throw new IOException("A game is still using the previous mod session. Close it before restoring its script.");
		}
		Dictionary<string, object> dictionary = J.Parse(File.ReadAllText(journal));
		if (!string.Equals(J.S(dictionary, "script"), script, StringComparison.OrdinalIgnoreCase))
		{
			throw new InvalidDataException("Unexpected script-session path.");
		}
		byte[] second = Convert.FromBase64String(J.S(dictionary, "original"));
		bool flag = Convert.ToBoolean(dictionary["existed"]);
		if ((!flag && !File.Exists(script)) || (flag && File.Exists(script) && File.ReadAllBytes(script).SequenceEqual(second)))
		{
			File.Delete(journal);
			return true;
		}
		if (!File.Exists(script) || Mods.Hash(script) != J.S(dictionary, "generatedSha256"))
		{
			throw new IOException("The game script was edited during a mod session. The original backup is retained; automatic restoration stopped.");
		}
		if (Convert.ToBoolean(dictionary["existed"]))
		{
			Mods.Atomic(script, Convert.FromBase64String(J.S(dictionary, "original")));
		}
		else
		{
			File.Delete(script);
		}
		File.Delete(journal);
		return true;
	}

	public void Begin(string active, List<ModPack> packs)
	{
		Recover();
		if (running())
		{
			throw new IOException("Close Shogun 2 before changing mod selections.");
		}
		byte[] array = (File.Exists(script) ? File.ReadAllBytes(script) : new byte[0]);
		if (array.Length > 8388608)
		{
			throw new IOException("The user script is unexpectedly large.");
		}
		string original;
		using (MemoryStream stream = new MemoryStream(array))
		{
			using StreamReader streamReader = new StreamReader(stream, new UTF8Encoding(encoderShouldEmitUTF8Identifier: false, throwOnInvalidBytes: true), detectEncodingFromByteOrderMarks: true);
			original = streamReader.ReadToEnd();
		}
		byte[] array2 = new UnicodeEncoding(bigEndian: false, byteOrderMark: true).GetPreamble().Concat(new UnicodeEncoding(bigEndian: false, byteOrderMark: true).GetBytes(Mods.ComposeScript(original, active, packs))).ToArray();
		string generatedSha;
		using (SHA256 sHA = SHA256.Create())
		{
			generatedSha = BitConverter.ToString(sHA.ComputeHash(array2)).Replace("-", "").ToLowerInvariant();
		}
		Mods.JsonFile(journal, new
		{
			script = script,
			existed = File.Exists(script),
			original = Convert.ToBase64String(array),
			generatedSha256 = generatedSha
		});
		Mods.Atomic(script, array2);
	}

	public void Dispose()
	{
		Recover();
	}
}
