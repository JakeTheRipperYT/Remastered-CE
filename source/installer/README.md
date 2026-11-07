# Current 0.1.80 installer and launcher

Exact source files used for the current setup and lean launcher, including nine-pack campaign visual integration and retained mod support. No private signing key, game DLL or complete game archive is included.

Rebuild on Windows x64 with .NET SDK 10.0.401, .NET Framework 4.8 targeting pack and Windows PowerShell 5.1. Close the game for self-tests. Obtain RemasteredCE-0.1.80-preview.rce from the matching GitHub release, then run:

```powershell
.\Build.ps1 -WorkDirectory 'F:/Codex/Builds/RemasteredCE80' -Package 'F:/Codex/Inputs/RemasteredCE-0.1.80-preview.rce'
```

Choose a new work directory. All builds, temporary files, NuGet and .NET state go there. The recipe checks the signed package hash/signature, compiles both executables, requires exact published binary hashes and runs 19 package integration checks. It does not install into a game, change preferences, sign a release or start the game. Output contains verified executables and the offline package; the public installer ZIP bundles setup, its config and the two text documents.

The public setup ZIP embeds the signed offline package in setup; use Offline → Use included release (offline). Verification scope and complete reconstruction results are in docs/release-verification-0.1.80.json.
