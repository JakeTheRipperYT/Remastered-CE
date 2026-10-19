# Remastered CE changelog

By **JakeTheRipper**.

1. **Campaign trees:** Replaced CE campaign-tree models with vanilla models while preserving CE's original placement records.
2. **Campaign terrain:** Applied CE ROTS ground textures and material maps across all four seasons; water assets retained.
3. **Campaign rendering:** Applied ROTS terrain-rendering and seasonal lighting settings to the base campaign.
4. **Spring battles:** Added clear blue skies and neutralised yellow sunlight in spring clear-day profiles.
5. **Screen-space shadows:** Enabled edge rejection, removing the black-bar artifacts.
6. **Banner shadows:** Excluded floating unit banners from screen-space shadow casting.
7. **Building smoke:** Replaced siege smoke with darkened matchlock-derived particles, tuning ascent, expansion, lifetime, wind and particle counts.
8. **Particle performance:** Added wider near-camera fading for the targeted smoke and ember effects.
9. **Unit sprites:** Applied vanilla's final soldier-to-sprite transition distances; retained CE's intermediate mesh LODs and foliage distances.
10. **War Is Slaughter traits:** Set enemy-morale penalties to -1/-2/-3 across the three levels.
11. **Brave/Cowardly traits:** Set morale progression to +1/+2/+3 and -1/-2/-3 respectively.
12. **Unit cards:** Restored original artwork, including campaign, frontend and UI skin copies.
13. **General portraits:** Restored original portraits, including the covered ROTS/FOTS variants.
14. **Encyclopedia artwork:** Restored original encyclopedia unit images.
15. **Movement audio:** Restored the short confirmation cue for ungrouped Alt-drag orders; confirmed working.
16. **Development backups and switching:** Preserved original files and baselines in JakeTheRipper's local development backups, and created vanilla/edited swap batches. Their edited snapshot predates later changes.
17. **Grass/vegetation dithering:** Patched the CE grass shader to remove the broken stationary screen-space dither/jitter effect.
18. **Order queues and siege pathfinding:** Increased order queue limits from 500 to 2000, reducing average siege lockups caused by pathfinding overflow from 30-85 seconds to 0-3 seconds.
19. **Movement-order feedback:** Fixed the audio bug that caused movement-order feedback audio not to play.

20. **Matchlock smoke:** Ported Better Vanilla Smoke to CE and corrected particle animation-cell sizes to prevent square smoke sprites; retained the existing building-smoke changes.
21. **Blood effects:** Ported GBJ blood effects and ground-splatter textures, restored ground-blood rendering, and corrected decal alpha handling. Ground splatters were confirmed visible in-game.
22. **Unit proximity fading:** Disabled near-camera unit fading with `proximity_fading false;`. The 0.1.7 installer applies this to an existing preferences script, preserves other settings and encoding, and saves a backup. CE and Remastered share this preference.
23. **Diplomacy:** Fixed empty clan-selection lists for demands to break an alliance or impose a trade embargo by correcting which negotiating party the UI queries. Confirmed with Takeda negotiating with Murakami about Jinbo.

**Credit:** Orendiz for his blood and smoke rework used in the 0.1.7 patch.

24. **Alliance demand-list visibility (0.1.8):** Fixed hidden offer/demand list boxes in the Demand Break Alliance menu. Runtime tracing confirmed the allied-clan row was populated but its parent list was hidden. Confirmed working across multiple clans. Temporary diagnostics are excluded.

25. **Morale and fatigue tooltip colours (0.1.9):** Added colour coding to 21 battle-tooltip state labels while retaining CE wording. Adapted from the supplied Bug fix collection.
26. **Hell difficulty (0.1.9):** Added a sixth difficulty position after Legendary for the base Shogun 2 campaign. Hell retains Legendary campaign and battle rules and AI difficulty bonuses, with the Realm Divide fame threshold set to -1. The Hell label displays correctly and battle realism, battle difficulty and Realm Divide controls lock as they do on Legendary.
27. **Proximity Fading control (0.1.9):** Added a graphics-menu checkbox below SSAO for near-camera unit fading. The setting now saves as On or Off across restarts, and updates preserve the player's choice.

28. **Hell realism and autosaves (0.1.12):** Hell now enforces Legendary battle realism after deployment and automatically saves as `auto_save_hell.{clan}`, retaining Legendary AI bonuses and instant Realm Divide.
29. **Yari-wall movement (0.1.12):** Units engaged in melee can now follow movement orders without disabling yari wall.
30. **Kneel-fire movement (0.1.12):** Units can receive movement orders while kneel fire remains enabled, with other eligibility checks and the firing drill retained.
31. **Naval defenders (0.1.12):** Defending fleets now use the normal naval attack group and engage the player. Attacker-group approach also reported by pad345654's Shogun 2 Bugfix Mod.
32. **Drop-in setting (0.1.12):** The pre-battle checkbox respects the saved campaign setting; changes on that screen are saved too.


33. **Campaign fleet-count banners (0.1.16):** Restored naval-banner geometry so the ship-count bars can display. Reconstructed from original assets in CE's model format and materials.
34. **Movement pitch variation (0.1.16):** Corrected the pitch-control scale in 48 infantry and cavalry movement sound banks. Retains the initial variation level selected in local testing.
35. **Movement start delay (0.1.16):** Corrected start-delay conversion curves in those 48 movement sound banks, reducing synchronized movement audio.
36. **Combat impact volume (0.1.16):** Increased 47 close-combat impact, weapon-swing and body-fall sound banks by 3 dB.
37. **Matched-combat audio timing (0.1.16):** Restored 430 original animation sound-timing files for byte-identical CE animations. The combined stab/kill-move audio correction was confirmed working by the user.
38. **Installer pack support (0.1.16):** Added private model/audio pack reconstruction, bounded pack-index expansion and compatible uninstall handling. Upgrade the installer ZIP once from 0.1.12; the game launcher executable is unchanged. Automatic installer self-updating remains excluded.
39. **Independent Hell difficulty (0.1.16):** Replaced the previous Legendary-ID alias with campaign mode 4, human handicap -4 and AI handicap +4 at the sixth slider position. Copied Legendary modifier values into 21 separate Hell database rows and extended native lookup bounds. Added independent startup/load handling, battle realism, fame threshold -1 and `auto_save_hell.{clan}` naming. Modifier data is LZ4 encoded for the compressed pack; the earlier local splash-crash packaging error is corrected.
40. **Hell starting enemies (0.1.16):** The Japan campaign script now recognizes Hell and uses the original hardest-difficulty starting rebellion/army branches for all nine affected clans. Exact armies, generals and spawn locations are retained. Hell's script flag has save/load support. Existing saves do not receive missing starting armies retroactively.

Entries 26 and 28 describe the earlier implementation's intent; entry 39 records the independent-mode correction now included. The withdrawn 0.1.13/0.1.14 builds are superseded by 0.1.16. Version 0.1.15 was local development only.
