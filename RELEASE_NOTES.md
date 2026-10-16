# Remastered CE 0.1.6 preview

By JakeTheRipper.

Corrects only the installer’s vanilla shader reference to the supplied shaders.pack. No changes to Remastered shader output, other game packs, the engine, launcher behavior, or settings.

The vanilla shader reference for 0.1.6 is the supplied shaders.pack (SHA-256 7d6ff45568b25a4c9729fa6df32e1c79ba51ba3ea5a7e35058d77217fd32847f). The installer checks this reference in the local CE installation. Generated Remastered shaders and all other game outputs remain identical to 0.1.5. The reference pack itself is not distributed.

Download **RemasteredCE_Installer_Preview.zip**, extract it, and run **RemasteredCE_Setup.exe**. Existing 0.1.5 installers can obtain the signed 0.1.6 package through Install / Update. The update requires the matching vanilla shader source in the local CE data folder.

The complete shader reconstruction was replayed against the supplied reference and matched the existing Remastered shader hash exactly. External and embedded package signatures passed verification. Installer application code is unchanged from 0.1.5; its previously tested safeguards remain in place.

The local Better Vanilla Smoke / GBJ blood port and its animation-cell correction are not included in this release. No installed game files were replaced while preparing this reference correction.

## Mod changelog

1. **Campaign trees:** Replaced CE campaign-tree models with vanilla models while preserving CE’s original placement records.
2. **Campaign terrain:** Applied CE ROTS ground textures and material maps across all four seasons; water assets retained.
3. **Campaign rendering:** Applied ROTS terrain-rendering and seasonal lighting settings to the base campaign.
4. **Spring battles:** Added clear blue skies and neutralised yellow sunlight in spring clear-day profiles.
5. **Screen-space shadows:** Enabled edge rejection, removing the black-bar artifacts.
6. **Banner shadows:** Excluded floating unit banners from screen-space shadow casting.
7. **Building smoke:** Replaced siege smoke with darkened matchlock-derived particles, tuning ascent, expansion, lifetime, wind and particle counts.
8. **Particle performance:** Added wider near-camera fading for the targeted smoke and ember effects.
9. **Unit sprites:** Applied vanilla’s final soldier-to-sprite transition distances; retained CE’s intermediate mesh LODs and foliage distances.
10. **War Is Slaughter traits:** Set enemy-morale penalties to −1/−2/−3 across the three levels.
11. **Brave/Cowardly traits:** Set morale progression to +1/+2/+3 and −1/−2/−3 respectively.
12. **Unit cards:** Restored original artwork, including campaign, frontend and UI skin copies.
13. **General portraits:** Restored original portraits, including the covered ROTS/FOTS variants.
14. **Encyclopedia artwork:** Restored original encyclopedia unit images.
15. **Movement audio:** Restored the short confirmation cue for ungrouped Alt-drag orders; confirmed working.
16. **Development backups and switching:** Preserved original files and baselines in JakeTheRipper’s local development backups, and created vanilla/edited swap batches. Their edited snapshot predates later changes.
17. **Grass/vegetation dithering:** Patched the CE grass shader to remove the broken stationary screen-space dither/jitter effect.
18. **Order queues and siege pathfinding:** Increased order queue limits from 500 to 2000, reducing average siege lockups caused by pathfinding overflow from 30–85 seconds to 0–3 seconds.
19. **Movement-order feedback:** Fixed the audio bug that caused movement-order feedback audio not to play.
