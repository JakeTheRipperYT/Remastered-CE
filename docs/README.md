# Remastered CE installer 0.1.12

By **JakeTheRipper**.

Extract the installer ZIP and run **RemasteredCE_Setup.exe**, keeping its `.config` file alongside it. Both Steam editions must be installed. The installer detects Steam libraries or accepts selected folders. Close the game, then choose **Install / Update Remastered CE**. Use the white-helmet **Launch Remastered CE** application afterward.

Windows x64, .NET Framework 4.8 and a filesystem supporting Windows hard links (normally NTFS) are required. This release supports CE Steam build 25810990 with matching original file hashes. Unsupported or modified inputs are rejected. Do not restore old vanilla files over a newer Steam build to bypass this check.

The installer builds `<CE folder>/RemasteredCE` from local installations. Unchanged CE data is linked locally; five modified packs are reconstructed separately. Vanilla game files are not replaced. The game executable, engine DLL and NVIDIA runtime are not distributed. Settings, saves and shader caches remain shared with CE. The installation adds approximately 4 GiB; updates require space for another staged copy and retain the previous installation.

The DLSS launch layout and launcher are unchanged from the working release: the separate executable retains its original filename, with the locally copied NVIDIA runtime beside it. Normal hardware capability checks remain active.

## Included changes

0.1.9 adds Hell difficulty after Legendary in the base Shogun 2 campaign, retaining Legendary rules and AI bonuses while setting required Realm Divide fame to -1. Battle-tooltip morale and fatigue labels gain colour coding.

Graphics options now include **Proximity Fading** below SSAO. Checked enables near-camera unit fading; unchecked disables it. Both choices persist across normal restarts. Settings remain shared with vanilla CE. Updates preserve an existing selection.

The previous diplomacy, DLSS, smoke/blood, artwork and rendering changes are retained. Blood and smoke rework: **Orendiz**. Tooltip colours: supplied **Bug fix collection**.

## Updates and verification

Leave GitHub selected and choose Install / Update for the newest signed release. 0.1.10 requires the new installer ZIP because it adds localisation-pack support. An older installer reports that it needs replacing before copying files. Unsupported/newer vanilla builds are rejected instead of overwriting their files.

Production checks replay the three new asset recipes with exact compression, compare relocated native helpers and hooks with the confirmed local implementation, and verify the release signature. Local Hell gameplay and proximity-setting persistence were confirmed; a fresh packaged in-game installation has not been claimed.

See THIRD_PARTY_NOTICES.txt for licensing and source-mod credits.
