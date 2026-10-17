# Remastered CE changelog

By **JakeTheRipper**.

1. **Campaign trees:** Replaced CE campaign-tree models with vanilla models while preserving CEâ€™s original placement records.
2. **Campaign terrain:** Applied CE ROTS ground textures and material maps across all four seasons; water assets retained.
3. **Campaign rendering:** Applied ROTS terrain-rendering and seasonal lighting settings to the base campaign.
4. **Spring battles:** Added clear blue skies and neutralised yellow sunlight in spring clear-day profiles.
5. **Screen-space shadows:** Enabled edge rejection, removing the black-bar artifacts.
6. **Banner shadows:** Excluded floating unit banners from screen-space shadow casting.
7. **Building smoke:** Replaced siege smoke with darkened matchlock-derived particles, tuning ascent, expansion, lifetime, wind and particle counts.
8. **Particle performance:** Added wider near-camera fading for the targeted smoke and ember effects.
9. **Unit sprites:** Applied vanillaâ€™s final soldier-to-sprite transition distances; retained CEâ€™s intermediate mesh LODs and foliage distances.
10. **War Is Slaughter traits:** Set enemy-morale penalties to âˆ’1/âˆ’2/âˆ’3 across the three levels.
11. **Brave/Cowardly traits:** Set morale progression to +1/+2/+3 and âˆ’1/âˆ’2/âˆ’3 respectively.
12. **Unit cards:** Restored original artwork, including campaign, frontend and UI skin copies.
13. **General portraits:** Restored original portraits, including the covered ROTS/FOTS variants.
14. **Encyclopedia artwork:** Restored original encyclopedia unit images.
15. **Movement audio:** Restored the short confirmation cue for ungrouped Alt-drag orders; confirmed working.
16. **Development backups and switching:** Preserved original files and baselines in JakeTheRipperâ€™s local development backups, and created vanilla/edited swap batches. Their edited snapshot predates later changes.
17. **Grass/vegetation dithering:** Patched the CE grass shader to remove the broken stationary screen-space dither/jitter effect.
18. **Order queues and siege pathfinding:** Increased order queue limits from 500 to 2000, reducing average siege lockups caused by pathfinding overflow from 30â€“85 seconds to 0â€“3 seconds.
19. **Movement-order feedback:** Fixed the audio bug that caused movement-order feedback audio not to play.

20. **Matchlock smoke:** Ported Better Vanilla Smoke to CE and corrected particle animation-cell sizes to prevent square smoke sprites; retained the existing building-smoke changes.
21. **Blood effects:** Ported GBJ blood effects and ground-splatter textures, restored ground-blood rendering, and corrected decal alpha handling. Ground splatters were confirmed visible in-game.
22. **Unit proximity fading:** Disabled near-camera unit fading with `proximity_fading false;`. The 0.1.7 installer applies this to an existing preferences script, preserves other settings and encoding, and saves a backup. CE and Remastered share this preference.
23. **Diplomacy:** Fixed empty clan-selection lists for demands to break an alliance or impose a trade embargo by correcting which negotiating party the UI queries. Confirmed with Takeda negotiating with Murakami about Jinbo.

**Credit:** Orendiz for his blood and smoke rework used in the 0.1.7 patch.
