# Remastered CE 0.1.0 preview

By JakeTheRipper.

- Initial installer and patch manager for CE Steam build 25810990.
- Requires local installations of Complete Edition and original Shogun 2.
- Constructs modified files separately and preserves vanilla game files.
- Supports signed `.rce` update packages and staged installation with rollback.
- Full reconstruction, signature/tamper checks, and update rollback tests passed.

**Testing preview:** the installer-generated build still requires an in-game smoke test. Automatic update downloads are not implemented. Source hash checks reject unsupported builds. Settings, saves, caches, and existing third-party mods remain shared with CE.

Download **RemasteredCE_Installer_Preview.zip** for the initial installation. The `.rce` asset contains the same included release and can be used to test the update selector.
