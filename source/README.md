# Source notes

Engine.cs, OnlineUpdates.cs and Program.cs target x64 .NET Framework 4.8 WinForms. app.manifest uses asInvoker. launcher.c is the unchanged native game launcher. redirect_portable.c is historical original routing source; the current combined native patch is represented by the signed package's manifest.json and helper.json. See hell/README.md for the Hell generator, preserved baseline helper and additional model/audio routing wrapper.

The installer embeds the signed release as `release`, its public verification key as `publicKey`, and the native LZ4 library as `lz4`. It reconstructs seven modified packs from local game inputs, expands the private staging pack index in bounded chunks, and supports four-, five-, six- and seven-pack uninstall records. Automatic installer self-updating is excluded. The application does not patch game process memory.

OnlineUpdates.cs selects public releases without account credentials, restricts download URLs to this repository, checks numeric versions and validates package signatures. Its cancellation, version, signature, rollback, link and uninstall checks run through `RemasteredCE_Setup.exe --self-test OUTPUT.txt` using temporary fixtures.

Generating a newly signed release additionally requires the developer's private signing key, which is deliberately excluded. The signed .rce file contains the complete combined reconstruction instructions. Source/hell includes an inspectable and reproducible generator for the new native Hell instructions and the campaign script correction without redistributing the game's script.
