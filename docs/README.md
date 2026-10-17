# Remastered CE installer 0.1.7

By **JakeTheRipper**.

Extract the installer ZIP and run **RemasteredCE_Setup.exe**, keeping its `.config` file alongside it. Both Steam editions must be installed. The installer detects Steam libraries or accepts selected folders. Close the game, then choose **Install / Update Remastered CE**. Use the white-helmet **Launch Remastered CE** application afterward.

Windows x64, .NET Framework 4.8 and a filesystem supporting Windows hard links (normally NTFS) are required. This release supports CE Steam build 25810990 with matching original file hashes. Unsupported or modified inputs are rejected. Do not restore old vanilla files over a newer Steam build to bypass this check.

The installer builds `<CE folder>/RemasteredCE` from local installations. Unchanged CE data is linked locally; four modified packs are reconstructed separately. Vanilla game files are not replaced. The game executable, engine DLL and NVIDIA runtime are not distributed. Settings, saves and shader caches remain shared with CE. The installation adds approximately 4 GiB; updates require space for another staged copy and retain the previous installation.

The DLSS launch layout and launcher are unchanged from the working release: the separate executable retains its original filename, with the locally copied NVIDIA runtime beside it. Normal hardware capability checks remain active.

## Included changes

0.1.7 includes the Better Vanilla Smoke matchlock port and atlas-cell correction, GBJ blood effects and ground-splatter artwork, the ground-decal alpha correction, and the confirmed diplomacy party-selection fix for break-alliance and trade-embargo lists. Existing campaign, artwork, audio, building-smoke, grass and queue changes remain included. See [the changelog](../CHANGELOG.md).

The failed wake shader experiment is excluded. Naval-wake seams remain under investigation.

## Unit camera preference

The new installer sets `proximity_fading false;` in an existing CE preferences script. This removes near-camera unit fading. It preserves graphics, camera/control values, comments and file encoding, and saves the original script as `preferences.script.txt.remasteredce-unit-fade.bak`. The setting is shared with vanilla CE. Uninstall retains settings and this backup.

If there is no preferences script yet, launch the game once and set `proximity_fading false;` in the script afterward. A preference-write failure does not undo a successful game installation; the installer reports the manual setting instead.

## Updates and uninstall

Leave **GitHub** selected and click **Install / Update Remastered CE** to download the newest published signed package. Prereleases are included; drafts are excluded. No GitHub sign-in is needed. Package signature and version checks run before installation. **Offline...** accepts the included or downloaded `.rce` package.

Existing 0.1.5/0.1.6 installer applications can install this game update, including the diplomacy and effects fixes. Their application code does not replace itself: use the 0.1.7 installer ZIP for automatic unit-fading preference handling, or set the preference manually. Applications older than 0.1.5 require the new installer ZIP.

**Uninstall Remastered CE** removes managed Remastered files and links while preserving vanilla files, settings, saves, unrecognized files and previous-version backups. Updates stage and verify files before publication, with rollback on ordinary publication failures. If Windows blocks rollback, retain the reported backups. The installer EXE is not Authenticode-signed; update-package signing is separate.

## Validation

The signed release passed a full production-installer reconstruction in a separate folder, including all four output-pack hashes, the modified engine, original-name executable, NVIDIA runtime and base-data links. Installer self-checks passed signature/tamper, updater-selection, rollback and uninstall checks. Unit-preference checks preserved unrelated graphics and controls and the original backup across UTF-8 with/without BOM and both UTF-16 byte orders.

The component fixes were tested locally during development. A new in-game launch of this exact packaged release has not been claimed. See [release verification](release-verification-0.1.7.json) and [self-check results](self-tests.txt).

The vanilla shader reference remains SHA-256 `7d6ff45568b25a4c9729fa6df32e1c79ba51ba3ea5a7e35058d77217fd32847f`. The reference pack itself is not distributed. THIRD_PARTY_NOTICES.txt includes LZ4 licensing and source-mod credits.
