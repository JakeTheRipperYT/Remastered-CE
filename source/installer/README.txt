# Remastered CE 0.1.80 Preview — Sim Turns and Campaign Fixes

This cumulative update retains the earlier Remastered CE fixes and adds:

- Optional 8-player simultaneous turns, selected in the launcher's Launch options. It uses a separate engine and isolated lobby/gifting UI data. Leave the checkbox off for normal Remastered CE.
- Repeatable religion/allegiance switching in Sim Turns mode through Clan Summary: Shinto-Buddhism/Christianity/Ikko in Sengoku, Fujiwara/Minamoto/Taira in Rise, and Emperor/Independent/Shogun in Fall. Includes the Freedom of Faith incident/tooltips and AI conversion at at least 75% native population support, subject to the supplied eligibility rules. Normal mode's religion behavior is unchanged.
- Fleet agents accompany a bulk army landing, and FOTS farm hover cards display contextual fertility-dependent wealth. Both engines include these fixes; actual farm income is unchanged.
- An auto-sized Launch options section fixes clipped checkboxes.
- Missing original animation sound timing restored, with corrected CE compression: 2,035 missing timing files and 430 corrected earlier matched-combat restorations.
- Ten seasonal fog profiles adjusted, and opening-ground weather state retained through Start Battle, weather transitions and result/quit stages, including native snow coating strength.

## Install or update

Download **RemasteredCE_Installer_Preview.zip**, extract the entire ZIP, and keep setup and its .config together. Close the game and other launcher windows, then run the new setup and choose Install / Update. Both original SHOGUN 2 and Complete Edition installations are required. Older published installers need this replacement setup for the new package format/version. The signed offline release is embedded in setup.

Normal and Sim Turns engines are reconstructed locally from supported game files and guarded recipes. Complete game DLLs and game archives are not distributed. Existing launcher profiles and custom mods are preserved by the installer.

## Verification and testing limits

The signed installer reconstructed the normal engine and alternate engine; the alternate output matches the installed tested candidate byte for byte. All four new religion assets decode identically, all 25,234 previous alternate data entries are preserved, and normal engine/pack recipes are unchanged from the preceding local build. 36 launcher self-tests and 186 native relative-reference cases passed. The exact published launcher/setup source is supplied with a checked rebuild script.

These checks do not establish campaign or multiplayer gameplay acceptance. Sim Turns multiplayer and the new CE campaign behavior still need live testing. The integrated upstream Sim helpers retain their existing unwind-metadata limitation. Earlier reported downward-camera performance dips remain unresolved; broader visual/audio playback acceptance remains pending.

Sim Turns is based on the supplied SimTurnsBeta8P 1.1 work by njn313 (MIT license, included). Religion switching integrates the user-supplied religion_swap v5 package. These contributions are credited separately from Remastered CE's integration work.
