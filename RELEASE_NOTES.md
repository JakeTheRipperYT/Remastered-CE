# Remastered CE 0.1.1 preview

By JakeTheRipper.

Fixes the shader compile error reported in 0.1.0. The original installer reconstructed the pack index but did not move 766 unchanged shader assets to the offsets listed in that index. This release reconstructs those entries from the local vanilla pack too.

All 51,386 decoded assets in all four generated packs match the working pre-installer backup. Full reconstruction and update rollback tests passed. The installer-generated build still needs an in-game smoke test.

Requires CE Steam build 25810990 and original Shogun 2 installed locally. Vanilla game files remain untouched. Existing installations can select the signed 0.1.1 `.rce` file using **Update file...**, then choose **Install / Update Remastered CE**. New users should extract **RemasteredCE_Installer_Preview.zip** and run **RemasteredCE_Setup.exe**.

Automatic update downloads are not implemented. Settings, saves, caches, and third-party mods remain shared with CE.
