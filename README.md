# Remastered CE

By **JakeTheRipper**.

Installer, updates, and release notes for Remastered CE for Shogun 2 Complete Edition.

See the [full mod changelog](CHANGELOG.md) for gameplay, graphics, artwork, and audio changes.

Version 0.1.8 fixes hidden alliance-demand lists, confirmed locally across multiple clans. It retains the smoke and blood ports, ground-splatter rendering, diplomacy party-selection changes and unit-fading preference handling. The failed naval-wake experiment is excluded.

## Download

[Download the installer preview](https://github.com/JakeTheRipperYT/Remastered-CE/releases/tag/v0.1.8-preview).

Extract the installer ZIP and run RemasteredCE_Setup.exe. Both Complete Edition and original Total War SHOGUN 2 must be installed. Select both game folders, close the game, and choose **Install / Update Remastered CE**.

**Use the 0.1.8 installer ZIP for the current release and automatic unit-fading preference handling.**

The working DLSS launch layout is retained. The 0.1.8 update passed targeted UI recipe, engine-helper and signature checks. It retains the installer implementation checked in 0.1.7. The local diplomacy correction was confirmed across multiple clans; a fresh in-game run of the newly packaged installer has not been claimed.

DLSS availability has been restored in the separate Remastered launch by preserving the original executable filename and copying the locally installed NVIDIA runtime beside it. The working launch layout was tested in-game.

The Remastered launcher and installer use a distinct white-helmet icon. Existing users can receive the launcher icon through Install / Update.

The installer builds the separate RemasteredCE folder using local game files. Vanilla game files are not replaced. No complete game EXE, engine DLL, or game packs are supplied here.

To uninstall an existing installation, open the new installer and choose **Uninstall Remastered CE**. Vanilla files, saves, settings, unrecognized files, and previous-version backups are kept.

For updates, leave **GitHub** selected and click **Install / Update Remastered CE**. The application downloads and verifies the newest signed update automatically, or reports that you are already up to date. Use **Offline...** for the included release or a downloaded `.rce` file. No GitHub sign-in is needed.

Existing 0.1.5/0.1.6 installers can obtain the 0.1.8 game update. Download the new installer ZIP to also apply the unit-fading preference automatically, or set `proximity_fading false;` manually. An `.rce` file does not upgrade the installer application itself. The preference is shared with vanilla CE; other preferences are preserved.

See [installation details and limitations](docs/README.md), [validation results](docs/self-tests.txt), and [third-party notices](THIRD_PARTY_NOTICES.txt).

![Installer preview](docs/preview.png)
