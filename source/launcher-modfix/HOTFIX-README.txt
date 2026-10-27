Remastered CE 0.1.25 - launcher mod compatibility fix 2

INSTALL
1. Extract this whole ZIP into a normal folder.
2. Close Remastered CE, the game, and all setup/launcher windows.
3. Run "Apply Launcher Fix.cmd" and choose the Complete Edition game folder containing shogun2_complete_edition.exe. Do not choose its RemasteredCE subfolder.
4. Open Launch_Remastered_CE.exe as usual. The combined UI displays "0.1.25 mod fix 2".

FIXES
- Reads S2CE compressed PFH3 pack indexes, with or without timestamps, alongside aligned PFHs and legacy PFH0/2/3 layouts. Keeps stored and uncompressed sizes separate and retains bounds checks.
- Discovers third-party packs in RemasteredCE/data, excluding reconstructed base-game packs.
- Adds "Use existing user.script.txt (ignore selections)" beside Play. Check it to use your previous manual mod configuration without changing its bytes. Leave it unchecked to use the selected launcher profile. The preference is saved with the profile.
- Existing manual commands are not silently combined with a selected profile; the selected mode is explicit.

Your original S2CE packs can stay in S2CE format. No conversion to original S2 is required for the corrected parser.

BACKUP AND RESTORE
The installer verifies the original 0.1.25 launcher hash, backs up the launcher and ownership record beside RemasteredCE, then replaces only the managed combined launcher/config and its ownership hash. Original game files, engine packs, saves and user scripts are not changed by applying this hotfix. A failed replacement rolls back.
Run "Restore Original Launcher.cmd" to restore the verified backup.

This is a separately built launcher hotfix for the existing 0.1.25-preview installation. It is not a new signed .rce release. The original embedded signed package is unchanged. Offline repair with this updated launcher preserves the corrected launcher; older setup executables still reinstall their original launcher. A later official update can replace this hotfix.

TESTING
37 focused parser, staging, discovery, manual-script, profile and UI assertions pass, plus the existing built-in installer checks, 20 installer-integration checks and five deployment/restore/failure checks. No live campaign or the affected user's actual mod files were available for in-game testing. Parser acceptance alone does not establish that every database/script mod is compatible with the game or other enabled mods.

The hotfix executable is unsigned, as are the original launchers. It does not claim to resolve the separate antivirus report against the original-Shogun-2 Ultimate Patch.
