# Remastered CE 0.1.13 preview

By **JakeTheRipper**.

- **Campaign fleet banners:** Restores the lower section of the naval banner model removed in CE. That missing section hid the bars for fleets with up to four ships and truncated the indicators for larger fleets. The repair restores the original geometry while retaining CE's model format and material settings.
- **Installer self-updates:** Future updates can download a signed installer bundle, restart setup, and continue installing the patch automatically. Existing game-folder selections are retained, and the previous installer is kept for rollback.
- **Model archive support:** The installer now builds and verifies a private `models.pack` for the remaster. Vanilla CE remains unchanged. Uninstall supports both earlier installations and the new six-archive layout.

**One-time installer download:** If you have installer 0.1.12 or older, download **RemasteredCE_Installer_Preview.zip**, extract it, and run **RemasteredCE_Setup.exe** with its `.config` file alongside it. Those versions cannot update themselves. Starting with 0.1.13, use **Install / Update Remastered CE** for future installer and patch updates.

All prior fixes and content are retained. The regular game launcher is unchanged. The additional private model archive needs approximately 5 GiB beyond the previous installation size; updates also stage a new copy and retain the previous installation.

Validation: all six archives and the engine rebuilt successfully from the signed package; signed updater replacement, automatic restart, tamper rejection and rollback checks passed; uninstall compatibility passed for four-, five- and six-archive installations. The naval banner repair is installed for local gameplay testing; in-game confirmation remains pending.
