# Installer self-updates

Installer 0.1.13 adds application updates to the existing Install / Update flow. Earlier installers require one manual ZIP download to gain this capability. The game launcher is unchanged.

Each published version provides the signed patch recipe (`.rce`) and a separately signed installer bundle (`.rceu`). A separate bundle avoids circular hashes between an installer and its embedded patch recipe. Both signatures use the existing pinned RSA public key. Installer bundles contain exactly a version/hash manifest, setup executable and setup configuration.

Update discovery accepts matching assets only from the project's own GitHub release. Downloads have size limits. Setup verifies the bundle signature, selected release version, file hashes and fixed entry names before launching an updater helper.

The helper is a copy of the already-running installer. It waits for the parent to close, verifies the signed bundle again, and checks that the target setup still matches the original executable hash. Replacement is serialized with an exclusive update lock. Setup and configuration are staged beside the target, replaced with backup copies, verified, and restarted with the resume argument. A replacement or restart failure restores the prior executable and configuration. A permission failure reports the error and preserves the previous installer.

Game-folder selections are saved before handoff. The restarted installer uses those saved selections and resumes the normal online patch flow. Offline .rce selection remains supported; offline users must obtain a compatible installer separately.

Signed update bundles are built after compiling the final installer. The installer embeds the signed .rce, public verification key and LZ4 runtime; the outer .rceu signs the final setup and configuration. Neither signing keys nor complete game archives/engine DLLs are distributed.

Tests cover signed-bundle verification, version mismatch, tamper rejection, repository URL restrictions, an actual parent/helper/restart sequence at a path with spaces, preservation of prior setup, changed-target rejection, rollback after restart failure, and uninstall compatibility for four-, five- and six-archive installations.
