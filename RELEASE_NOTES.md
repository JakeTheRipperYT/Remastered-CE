# Remastered CE 0.1.2 preview

By JakeTheRipper.

Adds **Uninstall Remastered CE** to the installer. It removes the active installation's managed packs, engine, and matching launchers after confirmation. Vanilla game files, saves, settings, unrecognized files, and previous-version backups are retained. The game must be closed. No original Shogun 2 folder is required for uninstall.

The new installer can uninstall existing 0.1.0 and 0.1.1 installations without reinstalling them first. If a root launcher differs from the installed copy, uninstall stops before deleting anything.

Uninstall tests passed for normal removal, preservation of vanilla and unrelated files, rejection of unsafe installation records, and preservation of an unrecognized root launcher. Existing signature and update rollback tests also passed.

Retains the 0.1.1 shader reconstruction fix. Generated game contents are unchanged; all 51,386 packed assets were previously verified against the working backup. In-game validation is still pending.

Download **RemasteredCE_Installer_Preview.zip**, extract it, and run **RemasteredCE_Setup.exe**. The `.rce` file alone updates game content and does not replace the installer application.
