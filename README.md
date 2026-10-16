# Remastered CE

By **JakeTheRipper**.

Installer, updates, and release notes for Remastered CE for Shogun 2 Complete Edition.

## Download

[Download the installer preview](https://github.com/JakeTheRipperYT/Remastered-CE/releases/tag/v0.1.2-preview).

Extract the installer ZIP and run RemasteredCE_Setup.exe. Both Complete Edition and original Total War SHOGUN 2 must be installed. Select both game folders, close the game, and choose **Install / Update Remastered CE**.

**Use 0.1.1 or newer. Version 0.1.0 had a shader reconstruction bug and should not be installed.**

Fresh installation and in-game launch have been tested successfully. Full file reconstruction and update rollback tests also passed.

The installer builds the separate RemasteredCE folder using local game files. Vanilla game files are not replaced. No complete game EXE, engine DLL, or game packs are supplied here.

To uninstall an existing installation, open the new installer and choose **Uninstall Remastered CE**. Vanilla files, saves, settings, unrecognized files, and previous-version backups are kept.

For updates, download a signed `.rce` package, select **Update file...**, and install it. Automatic download checks are not implemented in this preview.

See [installation details and limitations](docs/README.md), [validation results](docs/self-tests.txt), and [third-party notices](THIRD_PARTY_NOTICES.txt).

![Installer preview](docs/preview.png)
