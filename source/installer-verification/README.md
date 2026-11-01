# Installer acceptance verification

These C# harnesses load the final setup assembly and call its real reconstruction, publication, rollback and uninstall code. Compile for x64 .NET Framework with System.Web.Extensions.dll.

VerifyReleaseInstall.exe takes five arguments: setup executable, signed RCE package, Complete Edition root, original SHOGUN 2 root, and a new isolated F-drive target. It verifies every completed pack and engine against the signed manifest, preserves synthetic user mods and a previous installation during publication, and forces a separate publication failure to check rollback.

VerifyActualUninstall.exe takes the setup, isolated acceptance root and output JSON path. Its root guard is intentionally limited to the developer's F:/Codex/Remastered-CE-Port/work/github-release-071/acceptance-full fixture. Run it only after installation verification passes. It verifies that owned files are removed and synthetic custom mods/settings remain.

These tests leave the original games and live Remastered CE installation intact. They do not exercise the Install wrapper, mutate real user preferences or establish live battle visual acceptance. See docs/release-verification-0.1.71.json for results.
