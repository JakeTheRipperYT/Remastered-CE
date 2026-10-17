# Remastered CE 0.1.11 preview

By **JakeTheRipper**.

Fixes the campaign-selection crash in 0.1.10. The packaged Hell label helper tried to write runtime state into protected metadata. Mutable state now uses writable engine data, with label text kept read-only and its string object initialized correctly.

**If you have the 0.1.10 installer, choose Install / Update.** For a fresh installation, download **RemasteredCE_Installer_Preview.zip**, extract it and run the included setup. Installer versions older than 0.1.10 still require replacement with the latest ZIP.

Hell difficulty, tooltip colours, saved Proximity Fading and all earlier content are retained. Game asset recipes are unchanged from 0.1.10. Blood/smoke rework: **Orendiz**.

Verification executed the Hell label, campaign UI-state writes and Hell/Legendary settings from the corrected DLL mapped by Windows, confirming writable state-page permissions. Package signatures and engine construction were checked. A fresh in-game campaign launch of this package has not been claimed.
