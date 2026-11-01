# Remastered CE 0.1.71 Preview

## 🟢 **[DOWNLOAD ONLY THE INSTALLER ZIP — CLICK HERE](https://github.com/JakeTheRipperYT/Remastered-CE/releases/download/v0.1.71-preview/RemasteredCE_Installer_Preview.zip)**

> [!IMPORTANT]
> **📦 THE ONLY FILE YOU NEED TO DOWNLOAD IS `RemasteredCE_Installer_Preview.zip`.**
>
> **🟡 Right-click the ZIP → Extract All → open the extracted folder → run `RemasteredCE_Setup.exe`.**
> **Extract the entire ZIP before running setup.**
> **Keep the extracted setup and its `.config` file together.**
>
> **You do not need to download the separate EXE, `.rce` update package, or other release assets for a normal installation.** The ZIP includes the setup and required installation files; the launcher handles online update downloads.

Retained changes since 0.1.55:

- Unit selection: prevent rapid mouse movement from clearing clicked units, restore the original game's drag threshold, and refresh selection-box contents on release.
- Smoke stability: correct particle depth sampling, emitter draw indices, default normal-map channels and transparent draw ordering to address camera-dependent flashing.
- Particle performance: reduce redundant shader work, replace expensive emitter grouping with sorted source streams, and correct dynamic resolution to use fresh GPU timings and a 3.3 ms particle budget. The adaptive renderer retains its native 30%-100% resolution range.
- Renderer cleanup: remove the superseded particle-batching helper.
- Grass appearance: reduce metallic shine while retaining a wet coating and the existing dithering correction.
- Campaign grass wetness: use the battle's opening ground state, keeping rain-start grass wet and dry-start grass dry through later weather changes.

All previously published campaign weather, night controls, artwork, audio, gameplay and launcher changes remain included. The withdrawn s2fix trial is excluded. No multiplayer pursuit changes are included.

## Install or update

Download and extract RemasteredCE_Installer_Preview.zip. Keep RemasteredCE_Setup.exe and its .config together, close the game and other launcher windows, then choose Install / Update. Use this release's new setup executable. Both original SHOGUN 2 and Complete Edition installations are required. The installer reconstructs and verifies the patch from local files; complete game archives and engine DLLs are not distributed.

The signed offline package is embedded in setup; select Offline > Use included release (offline) to install without GitHub. Custom mods are preserved during updates.

## Verification and remaining limitations

Native selection/renderer checks and hardware/software shader comparisons passed. The weather audit passed 112,640 policy inputs, 144 controller cases, 96 fade cases, 105 unit-card cases, 72 grass GPU draws and 66 sky/ground GPU samples.

Smoke flashing and later battle-performance improvement were user-confirmed during development. Residual downward-camera performance dips remain unresolved. Latest grass appearance and reported puddle behaviour still require live visual confirmation; automated results do not establish that confirmation.
