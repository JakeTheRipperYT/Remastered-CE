using System;
using System.Collections.Generic;

namespace RemasteredCE;

public sealed class ModPack
{
	public string Path;

	public string Name;

	public string Source;

	public string WorkshopId;

	public string Error;

	public string Format;

	public int Type;

	public bool Enabled;

	public bool AutoLoaded;

	public long Bytes;

	public string[] Dependencies = new string[0];

	public HashSet<string> Files = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
}
