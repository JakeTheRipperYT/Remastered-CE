# Remastered CE

By **JakeTheRipper**.

Installer, updates, and release notes for Remastered CE for Shogun 2 Complete Edition.

See the [full mod changelog](CHANGELOG.md) for gameplay, graphics, artwork, and audio changes.

The 0.1.6 update corrects only the vanilla shader reference; Remastered game outputs are unchanged from 0.1.5.

## Download

[Download the installer preview](https://github.com/JakeTheRipperYT/Remastered-CE/releases/tag/v0.1.6-preview).

Extract the installer ZIP and run RemasteredCE_Setup.exe. Both Complete Edition and original Total War SHOGUN 2 must be installed. Select both game folders, close the game, and choose **Install / Update Remastered CE**.

**Use the 0.1.5 installer ZIP for the current DLSS launch layout.**

The working launch layout has loaded successfully with DLSS available. The 0.1.5 installer recreates its required base-data links as well as its modified files. Automated reconstruction, uninstall, and rollback checks passed; a fresh-install user test is pending.

DLSS availability has been restored in the separate Remastered launch by preserving the original executable filename and copying the locally installed NVIDIA runtime beside it. The working launch layout was tested in-game.

The Remastered launcher and installer use a distinct white-helmet icon. Existing users can receive the launcher icon through Install / Update.

The installer builds the separate RemasteredCE folder using local game files. Vanilla game files are not replaced. No complete game EXE, engine DLL, or game packs are supplied here.

To uninstall an existing installation, open the new installer and choose **Uninstall Remastered CE**. Vanilla files, saves, settings, unrecognized files, and previous-version backups are kept.

For updates, leave **GitHub** selected and click **Install / Update Remastered CE**. The application downloads and verifies the newest signed update automatically, or reports that you are already up to date. Use **Offline...** for the included release or a downloaded `.rce` file. No GitHub sign-in is needed.

**Download the 0.1.5 installer ZIP once for the DLSS launch fix.** Older installers cannot build this new layout and will prompt you to get the newer installer. An `.rce` file alone does not upgrade an installer application.

See [installation details and limitations](docs/README.md), [validation results](docs/self-tests.txt), and [third-party notices](THIRD_PARTY_NOTICES.txt).

![Installer preview](docs/preview.png)
