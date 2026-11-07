using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;

namespace RemasteredCE;

public sealed class Release : IDisposable
{
	public Dictionary<string, object> Manifest;

	public Dictionary<string, object> Helper;
	public Dictionary<string, object> SimTurns;

	public byte[] Launcher;

	public byte[] ModManager;

	public byte[] PackageBytes;

	public string PackageHash;

	public static byte[] Resource(string name)
	{
		using Stream stream = Assembly.GetExecutingAssembly().GetManifestResourceStream(name);
		if (stream == null)
		{
			throw new InvalidDataException("Missing application resource: " + name);
		}
		using MemoryStream memoryStream = new MemoryStream();
		stream.CopyTo(memoryStream);
		return memoryStream.ToArray();
	}

	public static Release Load(string path)
	{
		byte[] array = (string.IsNullOrEmpty(path) ? Resource("release") : File.ReadAllBytes(path));
		if (array.Length > 67108864 || array.Length < 16 || Encoding.ASCII.GetString(array, 0, 8) != "RCEPKG01")
		{
			throw new InvalidDataException("This is not a supported Remastered CE package.");
		}
		int num = BitConverter.ToInt32(array, 8);
		if (num < 256 || num > 1024 || array.Length <= 12 + num)
		{
			throw new InvalidDataException("Invalid package signature length.");
		}
		byte[] array2 = new byte[num];
		byte[] array3 = new byte[array.Length - 12 - num];
		Buffer.BlockCopy(array, 12, array2, 0, num);
		Buffer.BlockCopy(array, 12 + num, array3, 0, array3.Length);
		using (RSACryptoServiceProvider rSACryptoServiceProvider = new RSACryptoServiceProvider())
		{
			rSACryptoServiceProvider.FromXmlString(Encoding.UTF8.GetString(Resource("publicKey")));
			if (!rSACryptoServiceProvider.VerifyData(array3, CryptoConfig.MapNameToOID("SHA256"), array2))
			{
				throw new InvalidDataException("The update signature is invalid. Nothing was installed.");
			}
		}
		Release release = new Release();
		release.PackageBytes = array;
		release.PackageHash = Engine.Hash(array);
		using (ZipArchive zip = new ZipArchive(new MemoryStream(array3), ZipArchiveMode.Read))
		{
			release.Manifest = J.Parse(Encoding.UTF8.GetString(ReadEntry(zip, "manifest.json", 33554432)));
			release.Helper = J.Parse(Encoding.UTF8.GetString(ReadEntry(zip, "helper.json", 1048576)));
			if (release.Manifest.ContainsKey("simTurnsSha256"))
			{
				byte[] mode = ReadEntry(zip, "sim-turns.json", 16 * 1024 * 1024);
				if (Engine.Hash(mode) != J.S(release.Manifest, "simTurnsSha256"))
					throw new InvalidDataException("Sim Turns recipe hash mismatch.");
				release.SimTurns = J.Parse(Encoding.UTF8.GetString(mode));
			}
			release.Launcher = ReadEntry(zip, "launcher.exe", 1048576);
			if (release.Manifest.ContainsKey("unifiedLauncherSha256"))
			{
				release.ModManager = ReadEntry(zip, "mod-manager.exe", 8388608);
				if (Engine.Hash(release.ModManager) != J.S(release.Manifest, "unifiedLauncherSha256"))
				{
					throw new InvalidDataException("Combined launcher hash mismatch.");
				}
			}
		}
		if (J.N(release.Manifest, "schema") != 1 && J.N(release.Manifest, "schema") != 2)
		{
			throw new InvalidDataException("This update requires a newer installer. Download the installer ZIP from the Remastered CE GitHub releases page.");
		}
		if (release.Manifest.ContainsKey("minimumInstallerVersion") && ReleaseVersion.Parse(OnlineUpdates.AppVersion).CompareTo(ReleaseVersion.Parse(J.S(release.Manifest, "minimumInstallerVersion"))) < 0)
		{
			throw new InvalidDataException("This release needs a newer installer. Download the latest installer ZIP from the Remastered CE GitHub releases page.");
		}
		return release;
	}

	private static byte[] ReadEntry(ZipArchive zip, string name, int limit)
	{
		ZipArchiveEntry entry = zip.GetEntry(name);
		if (entry == null || entry.Length > limit)
		{
			throw new InvalidDataException("Invalid package component: " + name);
		}
		using Stream stream = entry.Open();
		using MemoryStream memoryStream = new MemoryStream();
		stream.CopyTo(memoryStream);
		return memoryStream.ToArray();
	}

	public void Dispose()
	{
	}
}
