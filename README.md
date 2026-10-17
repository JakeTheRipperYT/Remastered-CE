# Remastered CE

By **JakeTheRipper**.

Remastered CE is a community remaster and repair patch for **Total War: SHOGUN 2 Complete Edition**. It keeps the Complete Edition as the base game while restoring and improving visuals, effects, artwork and behaviour that were changed or broken in CE.

The patch installs as a **separate Remastered CE copy** beside your normal Complete Edition installation. Your normal game files are not replaced, so you can continue to use vanilla Complete Edition separately.

## Download

**[Download Remastered CE 0.1.8](https://github.com/JakeTheRipperYT/Remastered-CE/releases/tag/v0.1.8-preview)**

Download the installer ZIP, extract the whole ZIP to a normal folder, and keep `RemasteredCE_Setup.exe` and its `.config` file together.

See the **[full changelog](CHANGELOG.md)** for all included fixes, restorations and improvements.

## Before installing

You need:

1. **Total War: SHOGUN 2 Complete Edition** installed through Steam.
2. **Original Total War: SHOGUN 2** installed through Steam.
3. Several GB of free disk space. The installed Remastered CE copy uses roughly 4 GiB, and updates temporarily need extra space while the new version is built.

The installer uses files from both games that are already installed on your PC. It does **not** download or distribute a complete game executable, engine DLL or game data packs.

## How to install

1. Download and extract the installer ZIP.
2. Close both SHOGUN 2 and Complete Edition if either is running.
3. Run **`RemasteredCE_Setup.exe`**.
4. The installer will try to find both Steam installations automatically. If either path is blank or incorrect, use **Browse** and select the correct game folder.
5. Leave **GitHub - latest release** selected.
6. Click **Install / Update Remastered CE**.
7. Wait until the installer reports that the installation is ready.
8. Click **Launch Remastered CE**.

The installer verifies that your local game files match the supported version before making anything. It then builds the Remastered CE installation locally and verifies the completed files before publishing the new version.

## How to launch Remastered CE

After installation, use either:

- the **Launch Remastered CE** button inside the installer, or
- the white-helmet **`Launch_Remastered_CE.exe`** placed in your Complete Edition folder.

**Steam must be running.**

The launcher starts the separate Remastered CE executable inside the `RemasteredCE` folder with the correct Complete Edition Steam App ID. For normal use, launch Remastered CE through this launcher rather than opening the executable inside the `RemasteredCE` folder directly.

Your normal Complete Edition installation remains available separately through Steam.

## Updating

Updating is the same as installing:

1. Run **`RemasteredCE_Setup.exe`**.
2. Leave **GitHub** selected.
3. Click **Install / Update Remastered CE**.

The installer checks this GitHub repository for the newest supported release, downloads the signed `.rce` update package, verifies it, and installs it only if a newer version is available. No GitHub account or sign-in is required.

The installer builds updates in a temporary staging folder first. Your previous Remastered CE installation is retained during the update so it can be restored if publication fails.

You can also use **Offline...** to install the included release or a downloaded `.rce` package without using the automatic GitHub updater.

## Uninstalling

Run **`RemasteredCE_Setup.exe`** and choose **Uninstall Remastered CE**.

This removes the managed Remastered CE installation and launchers while keeping your normal game files, saves and settings intact.

## How the installer works

Remastered CE is built from your own local game installations rather than distributing replacement copies of the game.

The installer:

1. Verifies the supported Complete Edition executable, engine and required source files.
2. Extracts the required original assets from your locally installed games.
3. Reconstructs the four modified game packs used by Remastered CE.
4. Builds a separate Remastered CE engine and executable layout.
5. Hard-links unchanged Complete Edition data into the separate `RemasteredCE` folder instead of needlessly duplicating everything.
6. Verifies the finished files before switching the completed build into place.
7. Uses signed `.rce` update packages so downloaded updates are checked before installation.

Vanilla Complete Edition game files are not overwritten.

### Unit fading setting

The current installer also sets `proximity_fading false;` in your existing Complete Edition preferences file to stop units fading away when the camera gets close. That preferences file is shared by vanilla CE and Remastered CE, so this one setting also affects normal Complete Edition. The installer preserves the rest of your settings and creates a backup before changing it.

## More information

- **[Full changelog](CHANGELOG.md)**
- **[Detailed installer notes](docs/README.md)**
- **[Validation results](docs/self-tests.txt)**
- **[Third-party notices](THIRD_PARTY_NOTICES.txt)**

![Remastered CE installer](docs/preview.png)
