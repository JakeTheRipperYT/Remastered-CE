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

35. **Campaign fleet-count banners (0.1.13):** Restored the naval banner's missing lower geometry, which hid the first four to five ship-count bars in CE. Original geometry is rebuilt locally with CE's model format and materials. Static checks passed; in-game confirmation pending.
36. **Automatic installer updates (0.1.13):** Install / Update can now verify a signed installer update, restart setup and resume the patch installation. Keeps previous setup for rollback. Adds private models.pack reconstruction and uninstall compatibility with earlier layouts. A one-time installer ZIP download is required for 0.1.12 and older.
