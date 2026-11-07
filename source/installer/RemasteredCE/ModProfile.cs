namespace RemasteredCE;

public sealed class ModProfile
{
	public bool UseExistingScript;
	public bool UseSimTurns;
	public string[] Order = new string[0];

	public string[] Enabled = new string[0];

	public string[] Folders = new string[0];

	public string Name { get; set; } = "Default";
}
