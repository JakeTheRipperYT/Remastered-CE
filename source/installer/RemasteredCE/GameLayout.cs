namespace RemasteredCE;

public static class GameLayout
{
	public const string Product = "Remastered CE";

	public const string SteamAppId = "3846830";

	public const string Folder = "RemasteredCE";

	public const string GameExe = "shogun2_complete_edition.exe";

	public const string Launcher = "Launch_Remastered_CE.exe";

	public const string ModManager = "RemasteredCE_Launcher.exe";

	public const string OfflineRelease = "release.rce";

	public const string StateFile = "install-state.json";

	public const string CampaignNightPack = "rce_campaign_night_visuals.pack";

	public static readonly string[] BasePacks = new string[15]
	{
		"audio.pack", "boot.pack", "bp_orig.pack", "campaign_streaming.pack", "data_fots.pack", "data.pack", "local_global.pack", "models.pack", "models2.pack", "movies_fots.pack",
		"movies.pack", "movies2.pack", "shaders.pack", "terrain.pack", "web_content.pack"
	};
}
