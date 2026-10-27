# CE 0.1.25 integrated launcher mod fix 2

The released launcher rejects compressed sequential PFH3 indexes, omits `RemasteredCE/data` from discovery, and replaces manual mod commands during profile launches. This patch accepts the CE compression layout without rewriting packs, discovers private-data mods while excluding base packs, and offers an explicit existing-script mode. Selected-profile launches retain script backup/recovery.

The current combined-launcher sources are absent from the historical source tree. The build recovers the exact published managed sources with pinned ILSpy and applies two checked-in patches. The original ZIP is pinned by SHA-256 and retained on the release as `RemasteredCE-0.1.25-original-build-input.zip` for reproducibility. It is a build input, not the recommended installer.

## Build and test

Use Windows x64 with .NET 10 SDK, .NET Framework 4.8 targeting pack, Git and Windows PowerShell 5.1. Close the game and other CE launcher windows before running the installer/deployment checks.

```powershell
.\Build.ps1
```

Use a new `-WorkDirectory` for each clean build. Outputs:

- `_build/RemasteredCE_Installer_Preview.zip`: updated normal installer. Run Install / Update once to install the corrected combined launcher.
- `_build/RemasteredCE-0.1.25-Launcher-Mod-Fix.zip`: optional reversible launcher-only hotfix for an unmodified original 0.1.25 installation.

The recipe runs 37 focused parser/staging/discovery/script/profile/UI assertions, the 33 existing built-in result lines, 20 installer-integration checks and five deployment/restore/failure checks. Tests use temporary fixtures, not a live installation. `--build-only` can additionally verify complete reconstruction in a separate directory from locally installed games.

## Installer integration

`installer-integration.patch` stages the executing fixed launcher for the exact authenticated 0.1.25 package only, records its actual ownership hash and retains the original signed offline `.rce` byte-for-byte. Offline repair with this updated setup also preserves the fix. At the same engine version, an ownership-checked launcher-only transaction updates recognised older launchers, retains game packs and mods, saves backups and rolls back if the state-file replacement fails. Future packages keep their own signed launcher payload; an unexpected launcher in the pinned package is rejected.

The engine recipes, public key, signed package bytes and game data are unchanged. The combined executable remains unsigned. No signing check is weakened and no new private key is introduced. Older installers still deploy the original launcher; users must replace their setup ZIP to receive this update.

The standalone deployment tool checks exact installed hashes, keeps backups, updates ownership and rolls back partial failures. Parser acceptance does not establish compatibility of arbitrary campaign/database/script mods and does not promise to remove antivirus detections.
