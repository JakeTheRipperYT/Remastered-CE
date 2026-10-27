# CE 0.1.25 custom-mod launcher fix

The released launcher rejects compressed sequential PFH3 indexes produced for S2CE, omits `RemasteredCE/data` from discovery, and replaces manual mod commands during profile launches. This patch accepts the CE compression index layout without rewriting packs, discovers private-data mods while excluding base packs, and offers an explicit existing-script launch mode that leaves manual commands unchanged. Selected-profile launches retain script backup/recovery.

The current combined-launcher source is not published in the historical `source/` tree. To make this fix reviewable and buildable, the recipe recovers the exact published 0.1.25 managed sources using pinned ILSpy, then applies the small checked-in source patch. The original ZIP is pinned by SHA-256. Binary resources, game reconstruction recipes, public key and package signature are unchanged. No private signing key is required for this standalone replacement.

## Build and test

On Windows x64, install the .NET 10 SDK, .NET Framework 4.8 targeting pack and Git. Windows PowerShell 5.1 is used for tests. Run:

```powershell
.\Build.ps1
```

The build downloads the pinned official ZIP, installs ILSpy 11.2.0.10050 locally in `_build`, recovers and patches the managed project, builds the combined launcher, runs 37 focused checks plus built-in checks and five deployment checks, and produces `_build/RemasteredCE-0.1.25-Launcher-Mod-Fix.zip`. Use a new `-WorkDirectory` for a subsequent clean build. No files are installed into a live game by the build or tests.

`launcher-modfix.patch` contains the implementation. `Test-Launcher.ps1` tests compressed/uncompressed, aligned/sequential and timestamp layouts, byte-identical staging, malformed bounds, discovery, script preservation/recovery, profile persistence and UI mode switching. `Test-Deployment.ps1` tests exact-hash replacement, ownership updates, idempotency, restoration and rollback on a locked state file.

## Distribution limits

The included deployment tool supports only the verified original 0.1.25 launcher, keeps recoverable backups, and updates `unifiedLauncherSha256` so ownership-aware uninstall remains valid. It does not change the game engine, data packs or signed `.rce`. Offline reinstalling the original signed package reinstates the old launcher. Publishing a full integrated release still requires the canonical build and release signing key.

No actual affected mod or live-game database/script override test was available. The patch fixes demonstrated launcher-side defects; arbitrary mod compatibility is not claimed. The replacement is unsigned and makes no promise to clear antivirus detections.
