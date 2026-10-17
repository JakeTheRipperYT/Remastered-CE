# Remastered CE 0.1.7 preview

By JakeTheRipper.

Blood and smoke rework: Orendiz. Thank you for the original effects used in this patch.

Includes the Better Vanilla Smoke matchlock port with corrected animation-cell sizes, GBJ blood effects and visible ground splatters, the ground-blood alpha compatibility fix, and the confirmed diplomacy fix for empty break-alliance and trade-embargo clan lists. Existing building-smoke changes are retained.

The 0.1.7 installer also disables near-camera unit fading in an existing CE preferences script. It changes only `proximity_fading`, preserves the file encoding and other settings, and saves a `.remasteredce-unit-fade.bak` backup. This preference is shared with vanilla CE. If no preferences script exists yet, launch the game once and set `proximity_fading false;` afterward.

Download **RemasteredCE_Installer_Preview.zip**, extract it, and run **RemasteredCE_Setup.exe**. Both installed Steam games are required. Vanilla game files remain untouched. Complete game files and the NVIDIA runtime are reconstructed or copied from local installations.

Existing 0.1.5/0.1.6 installer applications can download the signed 0.1.7 game update through **Install / Update**. Their application code does not upgrade itself, so use the new installer ZIP for automatic unit-fading preference handling, or set that preference manually. The working white-helmet launcher and DLSS launch layout are unchanged.

The failed naval-wake shader experiment was reverted and is excluded. Wake investigation remains local; this release makes no naval-wake fix claim.

Individual local fixes were tested during development, including visible ground blood, disabled unit proximity fading, and populated diplomacy demand lists. Release reconstruction and signature validation are checked separately; a fresh in-game run of the newly packaged installer is not claimed.

See [CHANGELOG.md](https://github.com/JakeTheRipperYT/Remastered-CE/blob/main/CHANGELOG.md) for the complete mod changelog and THIRD_PARTY_NOTICES.txt for credits.
