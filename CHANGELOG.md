# Remastered CE changelog

By **JakeTheRipper**.

## 0.1.25 launcher mod fix 2 — October 27, 2026

- Read compressed sequential CE/PFH3 mod indexes with correct stored-size accounting and existing bounds checks.
- Discover custom packs in `RemasteredCE/data` while excluding base archives.
- Add an explicit existing-user-script mode; retain profile-based script backup and recovery.
- Include the corrected combined launcher in normal installation and offline repair with the updated installer.
- Let existing 0.1.25 users receive the launcher-only correction through Install / Update without reconstructing game packs or moving mods. Verify ownership, keep a backup, and roll back a failed state-file replacement.
- Preserve the signed 0.1.25 engine/data package unchanged. Older installers must be replaced to receive this launcher update.

## Included patch changes

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

41. **Recruitment videos (0.1.17):** Restored 41 original unit recruitment videos from the original game.
42. **Parrott gun smoke (0.1.17):** Added the missing launch smoke effect to the Boshin Parrott gun.
43. **Close-camera combat audio (0.1.17):** Combat sounds are no longer rejected when the camera is close.

44. **Fire by Rank startup (0.1.20):** Remove unnecessary standing-idle delays before the first ranked volley, retaining the existing firing drill and movement rules.
45. **Fear and trait progression (0.1.20):** Combine trait, item and skill fear numerically. Set War Is Slaughter/Bloodthirsty/Blood Soaked enemy-morale contributions to -4/-5/-6, Sword of Amaterasu and Dreaded Force to -4, both Intimidating levels to -4, and ROTS Dreaded to -1/-2. Existing Brave/Cowardly progression is retained.
46. **Single-unit battle groups (0.1.20):** Retain groups containing one land unit or ship, handle their compact frames safely, and remove empty engine group records so ungrouping and regrouping with the same number continues to work. CE already allowed initial singleton creation.
47. **Locked formation spacing (0.1.20):** Preserve authored overlap when capturing, saving, moving and rotating player land-group layouts. Apply the matching correction to direct, copied and composite dragging while retaining other-group obstacles, path mode and terrain checks.
48. **Artillery centre aim (0.1.20):** Aim land siege equipment, including cannons and mangonels, at formation centres consistently in target scoring and final range/arc checks. Retain target height and projectile spread; ordinary infantry, crew, rockets and naval targeting keep their existing rules.
49. **Ranged difficulty bonuses (0.1.20):** Neutralize Hard/Very Hard AI core marksmanship multipliers and loading-skill additions for land and naval combat, including the Very Hard battle tier used by Legendary/Hell. Preserve earned unit bonuses, player/Easy behaviour and other difficulty effects.
50. **Yari abilities (0.1.20):** Add missing Yari Square links for ordinary, Hattori, dojo and multiplayer Yari Samurai, using CE's existing Spear Expertise/custom-battle unlocks. Give Yari Ronin Rapid Advance.
51. **Ikko Warrior Nuns (0.1.20):** Add campaign recruitment at the Jodo Shinshu Fortified Monastery after Scholarship and Honganji after Neo-Confucianism, with 2/3 recruitment XP. Add an Ikko variant to custom/multiplayer rosters, preserving CE combat stats and assets, with the appropriate display name.
52. **Kisho Ninja ammunition (0.1.20):** Correct missing two-shot ammunition values across the affected variants, including Hattori and Tokugawa. Preserve CE's existing combat stats and already-correct ammunition values.
53. **Bow accuracy and recruitment XP (0.1.20):** Add missing general bow-accuracy links for Bow Cavalry and Takeda Bow Cavalry, and missing Ikko monk recruitment-XP bonuses at five holy-site buildings. Retain links already present in CE.
54. **Naval balance corrections (0.1.20):** Port the missing ship bailing, flooding, sinking and hull-section critical thresholds across the affected roster, and Sengoku Bune fire-risk corrections. Restore the missing Mori campaign ship-movement effect binding and bonus. Existing Mori Medium Bune recruitment and Nanban movement fixes are retained.
55. **Status tooltip colours (0.1.20):** Add 75 missing colour-formatting corrections while preserving CE wording and the 18 strings that already matched the OG fixes.
56. **Oda banner (0.1.20):** Correct the Oda banner using CE-native model format and materials, following the original correction's model substitution. Retain the previously released naval-banner repair.
57. **Setup build verification (0.1.20):** Include the cumulative signed reconstruction recipe and update the setup version. Build-only staging on another drive copies required base data when Windows cannot create cross-volume hard links; normal same-drive installs retain hard links. Installer self-updating remains excluded.

Version 0.1.20 includes all released 0.1.17 content and the cumulative local 0.1.18-0.1.20 corrections. Loading-screen changes and the unproven Heavy Bune placement addition are excluded; CE's native oar meshes and animations are retained. No Sekigahara campaign build is changed. Existing CE fatigue and Mori fixes were checked rather than duplicated.

Validation: native instruction/ABI/unwind checks and asset/recipe checks passed. Release setup reconstruction and updater verification are recorded in docs/release-verification-0.1.20.json. Automated checks do not establish complete live battle, pathfinding or multiplayer acceptance.


## 0.1.25 preview - night reinforcements and combined launcher

- Land night battles allow normally eligible reinforcing armies on either side when their own leading general has the effective night-battle ability. The attacking army and direct target remain included. Normal range, alliance, army-limit and naval restrictions remain in place.
- Preview strength, final participant handling, allied voting and deployment portraits, unit cards, availability text and counters use the same reinforcement policy.
- A larger combined setup/mod launcher with matching blue-grey colours, green accents and a single Play button. The redundant setup-panel Mods & Launch button is removed.
- CE Workshop/local/custom-folder discovery, profiles, dependency sorting, PFHs metadata support, optional pack staging and recoverable mod-script restoration.
- An installed launcher beside the managed mods folder and a signed offline package for repair. Startup handoff arguments are accepted correctly; the actual installed window was checked.
- PNG previews and CE base archives, including the stock movie packs, are excluded from the mod list.

**Install/update:** download and extract the new installer ZIP. Keep `RemasteredCE_Setup.exe` and its `.config` together. Close the game and other launcher windows, then run setup and choose Install / Update. Older installers must be replaced for this release. After installation, use Play Remastered CE on the right, with Steam running.

The installer reconstructs all eight existing packs from your locally installed original and Complete Edition games, verifies the output and retains the previous installation during updates. Complete game packs and engine DLLs are not distributed.

The OG audio and tooltip-wrapping changes were not ported. All eight existing pack recipes remain unchanged from 0.1.20. This release contains no multiplayer-desync fix and no Sekigahara update.

Native policy/UI, Windows unwind, mod-loader, script-parser, setup, rollback and signed-package checks passed. A complete installation using the final setup executable is verified before publication. Live CE night-battle entry/results and multiplayer acceptance remain pending. Dependency sorting does not guarantee mod compatibility.
