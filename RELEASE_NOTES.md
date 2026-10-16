# Remastered CE 0.1.5 preview

By JakeTheRipper.

Restores the working DLSS launch layout. The white-helmet launcher starts RemasteredCE/shogun2_complete_edition.exe, with CE.dll and the NVIDIA runtime copied and modified locally as needed. The launcher binary is the same one used in the successful game launch.

Includes the required base-game data links that were missing from the earlier installer build. The installer links unchanged local CE data files into the separate data folder and preserves the four modified packs. Uninstall removes those links while keeping the vanilla files. Updates rebuild the links from the current CE installation. A filesystem supporting Windows hard links (normally NTFS) is required.

Download **RemasteredCE_Installer_Preview.zip**, extract it, and run **RemasteredCE_Setup.exe**. Older installers cannot build this layout; downloading the .rce alone does not upgrade the installer.

Full file reconstruction and automated checks passed, including base-data linking, uninstall preservation of vanilla files, signature verification, and rollback. The working layout has loaded in-game with DLSS selectable; a fresh-install user test of this installer is pending.

Game pack contents and engine modifications are unchanged. Vanilla files are not replaced. Game assets, the complete game executable, engine DLL, and NVIDIA runtime are obtained from local installations rather than distributed here. Settings and saves remain shared with CE.
