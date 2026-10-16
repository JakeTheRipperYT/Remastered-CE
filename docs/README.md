# Remastered CE â€” installer preview 0.1.6

Created by **JakeTheRipper**. Preview images use example paths rather than developer machine paths.

Extract the ZIP, then run RemasteredCE_Setup.exe. Select the installed Complete Edition and original Total War SHOGUN 2 folders, close the games, and choose **Install / Update Remastered CE**. GitHub is selected by default; the newest published signed release is downloaded automatically when you click Install / Update. Use **Launch Remastered CE** after installation. The launcher now has a distinct white-helmet icon, also used by the installer. Existing users can get the launcher icon through the GitHub update flow.

Requires Windows x64, .NET Framework 4.8, Steam, and both games installed. This preview supports CE Steam build 25810990 with the exact source files used for development. The installer verifies source hashes and stops on unsupported or modified files. Do not restore old vanilla backups over a newer Steam build to bypass that check.

## Files and disk space

The application constructs the modified packs and engine from local installations. The distribution contains patch instructions, an original launcher, a redirection helper, and the LZ4 library; it does not include the complete game EXE, engine DLL, or game packs. This describes the distribution format, not a legal clearance.

Generated game files go in <CE folder>\RemasteredCE. The separate game executable keeps its original filename inside this folder, beside the copied NVIDIA DLSS runtime and modified engine. Launch_Remastered_CE.exe remains beside the vanilla executable; a legacy bootstrap is retained for compatibility. The original game EXE, engine DLL, and packs are not replaced. Launch the original game through Steam to play vanilla. Existing third-party mods are not removed or managed. Settings, saves, and caches remain shared with CE.

Required unchanged CE data files are linked locally into the separate data folder, preserving the four modified packs. These hard links require a filesystem supporting Windows hard links (normally NTFS); they do not duplicate the large base packs. Updates recreate the links from the currently installed CE files. Uninstall removes the Remastered links while retaining their vanilla files.

The generated installation uses approximately 4 GiB of additional disk space. Each update requires enough additional space for another complete staged copy; the previous Remastered folder is retained as RemasteredCE.previous_<timestamp>. Keep those previous folders until satisfied with the update. Remove only identified older Remastered folders to reclaim space.

## Uninstall

Open this version of RemasteredCE_Setup.exe, select the Complete Edition folder, and choose **Uninstall Remastered CE**. Confirm to remove the active installation's managed packs, engine, and matching root launchers. This works with installations made by earlier installer previews; reinstalling first is unnecessary. The original Shogun 2 installation is not required for uninstall.

Vanilla files, saves, settings, other mods, previous-version backup folders, and unrecognized files are kept. If a root launcher has been replaced with a different file, uninstall stops before deleting managed files. Close the game before uninstalling. The downloaded installer itself remains available for reinstalling.

## DLSS launch fix

Preview 0.1.5 fixes DLSS being greyed out in the separate Remastered launch when it is available in vanilla CE. The launcher now starts RemasteredCE/shogun2_complete_edition.exe with the original executable filename, and the installer copies the NVIDIA DLSS runtime from your local CE installation beside it. NVIDIA capability checks remain active; this does not enable DLSS on unsupported hardware.

Download the **0.1.5 installer ZIP** once. Earlier installers cannot build this new launch layout and will ask for a newer installer. No NVIDIA DLL or complete game executable is redistributed; both are copied from your installed CE files.

## Updates

Leave **GitHub** selected and click **Install / Update Remastered CE**. The application checks the public GitHub releases, including prereleases, selects the highest published supported version, downloads its `.rce` package, and verifies its signature and advertised version before installation. If the installed version is the same or newer, it reports that you are up to date and leaves the installed files in place. No GitHub account or sign-in is needed.

For offline use, click **Offline...** and choose either the included release or a previously downloaded `.rce` file. Select **GitHub** to return to online updates. Network failures do not silently install an older version or change the game files.

Download this new installer ZIP once to gain online updates; an `.rce` package updates game content and does not replace an older installer application. A future release that requires a newer installer will tell you to download its installer ZIP. The installer EXE itself is not Authenticode-signed; the release package signature is a separate mechanism.

Unknown CA updates are rejected during installation. The untouched Steam installation remains available, including any newer files Steam installs. This preview does not guarantee an already installed Remastered build will remain compatible after a CA update. Stop using that Remastered build until a compatible release is available.

Updates are built and verified in a staging folder before publication. An ordinary publication failure triggers rollback to the previous Remastered installation. If Windows prevents rollback, keep the retained files and follow the reported error; abrupt power loss is not covered by the rollback tests.

## Preview validation

A complete reconstruction from the local CE and original Shogun 2 installations passed all output hashes, including the redirected engine. Self-tests passed source-copy/write reconstruction, LZ4 compression, package signature validation, tamper rejection, and successful/failed update publication with rollback. Every one of the 51,386 decoded packed assets was also compared with the working pre-installer backup and matched. This catches relocated unchanged entries as well as modified assets. The UI preview was inspected. The working launch layout has loaded successfully in-game with DLSS available. The 0.1.5 installer reconstructs that layout; a fresh-install user test is pending.

Installer reconstruction and automated checks passed. A fresh-install user test of this release is pending.

## Included files

RemasteredCE_Setup.exe contains the initial release. Keep its .config file beside it. The separately supplied RemasteredCE-0.1.6-preview.rce is the same release, available for offline updates. THIRD_PARTY_NOTICES.txt contains the LZ4 license. Source code is provided in source/ for inspection; release signing credentials are excluded.

## Vanilla shader reference correction

The vanilla shader reference for 0.1.6 is the supplied shaders.pack (SHA-256 7d6ff45568b25a4c9729fa6df32e1c79ba51ba3ea5a7e35058d77217fd32847f). The installer checks this reference in the local CE installation. Generated Remastered shaders and all other game outputs remain identical to 0.1.5. The reference pack itself is not distributed.
