# Source notes

Engine.cs and Program.cs target x64 .NET Framework 4.8 WinForms. app.manifest uses asInvoker. launcher.c is the original native bootstrap launcher; redirect_portable.c is the native file-open redirection helper compiled into patch instructions.

The compiled application embeds the signed release as `release`, its public verification key as `publicKey`, and the native LZ4 DLL as `lz4`. The source files here are for inspection; generating a new supported release additionally requires the developer release tooling, audited local game inputs, and private signing key. The private key is deliberately excluded. The application does not patch game process memory.

OnlineUpdates.cs selects releases and verifies online downloads. It uses the public GitHub API without account credentials, accepts only this repository's release asset addresses, checks version ordering, and validates the package signature before exposing a download for installation. Network and cancellation tests run without changing the game installation.

Installer 0.1.14 supports seven private modified packs. Signed data-pack recipes may expand the index by moving the original payload in bounded chunks inside the private staging file. Four-, five-, six- and seven-pack uninstall records are supported. Automatic installer self-updating is not included.
