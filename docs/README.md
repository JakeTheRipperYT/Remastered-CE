# Remastered CE installer 0.1.25

Extract the installer ZIP, keep the setup EXE and .config together, and run setup. Both Steam editions are required. Windows x64, .NET Framework 4.8 and a filesystem supporting Windows hard links are required. Supported CE build: 25810990, with matching original hashes; unsupported inputs are rejected.

The combined window keeps installation on the left and mods/Play on the right. Download this new ZIP once: older installers cannot install the new launcher layout. GitHub updates and signed offline packages remain supported. Automatic installer self-updating is excluded.

The installer reconstructs eight private packs (about22 GiB), builds the private engine/bootstrap, links unchanged local base data, and verifies the result before publication. Updates retain the previous installation. Vanilla game files are not replaced. Mod folders survive updates and are retained by uninstall; edited launcher/package files are protected.

Mod discovery uses CE Workshop ID3846830, game data, RemasteredCE/mods and explicitly added folders. Base game archives and PNG thumbnails are excluded. Auto-sort follows declared dependencies; it does not solve arbitrary mod incompatibilities. The original CE user mod script is journaled and restored after play, with interrupted-session recovery and external-edit protection.

Use Launch_Remastered_CE.exe or the installed RemasteredCE_Launcher.exe to open the combined window, then Play Remastered CE. Steam is required to play.

See release-verification-0.1.25.json, the main README and CHANGELOG for current validation and limitations. Historical verification and source files remain in the repository; they describe their original releases. Current implementation changes are not added to the source directory in this release.
