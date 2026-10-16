# Remastered CE â€” installer preview 0.1.2

Created by **JakeTheRipper**. Preview images use example paths rather than developer machine paths.

Extract the ZIP, then run RemasteredCE_Setup.exe. Select the installed Complete Edition and original Total War SHOGUN 2 folders, close the games, and choose **Install / Update Remastered CE**. The included release is already selected. Use **Launch Remastered CE** after installation.

Requires Windows x64, .NET Framework 4.8, Steam, and both games installed. This preview supports CE Steam build 25810990 with the exact source files used for development. The installer verifies source hashes and stops on unsupported or modified files. Do not restore old vanilla backups over a newer Steam build to bypass that check.

## Files and disk space

The application constructs the modified packs and engine from local installations. The distribution contains patch instructions, an original launcher, a redirection helper, and the LZ4 library; it does not include the complete game EXE, engine DLL, or game packs. This describes the distribution format, not a legal clearance.

Generated game files go in <CE folder>\RemasteredCE. Two custom launcher files, Launch_Remastered_CE.exe and RemasteredCE_Bootstrap.exe, go beside the vanilla executable. The original game EXE, engine DLL, and packs are not replaced. Launch the original game through Steam to play vanilla. Existing third-party mods are not removed or managed. Settings, saves, and caches remain shared with CE.

The generated installation is approximately 4 GiB. Each update requires enough additional space for another complete staged copy; the previous Remastered folder is retained as RemasteredCE.previous_<timestamp>. Keep those previous folders until satisfied with the update. Remove only identified older Remastered folders to reclaim space.

## Uninstall

Open this version of RemasteredCE_Setup.exe, select the Complete Edition folder, and choose **Uninstall Remastered CE**. Confirm to remove the active installation's managed packs, engine, and matching root launchers. This works with installations made by previews 0.1.0 and 0.1.1; reinstalling first is unnecessary. The original Shogun 2 installation is not required for uninstall.

Vanilla files, saves, settings, other mods, previous-version backup folders, and unrecognized files are kept. If a root launcher has been replaced with a different file, uninstall stops before deleting managed files. Close the game before uninstalling. The downloaded installer itself remains available for reinstalling.

## Updates

For this first preview, download an .rce release file separately, choose **Update file...**, then **Install / Update Remastered CE**. The application verifies its release signature before accepting it. There is no configured download server or automatic online update check yet. The installer EXE itself is not Authenticode-signed; the release package signature is a separate mechanism.

Unknown CA updates are rejected during installation. The untouched Steam installation remains available, including any newer files Steam installs. This preview does not guarantee an already installed Remastered build will remain compatible after a CA update. Stop using that Remastered build until a compatible release is available.

Updates are built and verified in a staging folder before publication. An ordinary publication failure triggers rollback to the previous Remastered installation. If Windows prevents rollback, keep the retained files and follow the reported error; abrupt power loss is not covered by the rollback tests.

## Preview validation

A complete reconstruction from the local CE and original Shogun 2 installations passed all output hashes, including the redirected engine. Self-tests passed source-copy/write reconstruction, LZ4 compression, package signature validation, tamper rejection, and successful/failed update publication with rollback. Every one of the 51,386 decoded packed assets was also compared with the working pre-installer backup and matched. This catches relocated unchanged entries as well as modified assets. The UI preview was inspected. The installer-generated build still needs an in-game smoke test.

The previous manually installed build was tested in-game. Treat this package as a local test preview before sharing it with followers.

## Included files

RemasteredCE_Setup.exe contains the initial release. Keep its .config file beside it. The separately supplied RemasteredCE-0.1.2-preview.rce is the same release, useful for testing the update selector. THIRD_PARTY_NOTICES.txt contains the LZ4 license. Source code is provided in source/ for inspection; release signing credentials are excluded.
