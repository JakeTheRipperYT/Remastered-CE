# Source notes

Engine.cs and Program.cs target x64 .NET Framework 4.8 WinForms. app.manifest uses asInvoker. launcher.c is the original native bootstrap launcher; redirect_portable.c is the native file-open redirection helper compiled into patch instructions.

The compiled application embeds the signed release as `release`, its public verification key as `publicKey`, and the native LZ4 DLL as `lz4`. The source files here are for inspection; generating a new supported release additionally requires the developer release tooling, audited local game inputs, and private signing key. The private key is deliberately excluded. The application does not patch game process memory.
