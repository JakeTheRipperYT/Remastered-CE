# Remastered CE 0.1.28 preview

This release adds the firing-audio correction and revised War Is Slaughter trait trigger to the existing cumulative patch. It also includes the corrected combined mod launcher from **0.1.25 mod fix 2**.

- **Firing audio:** prioritize weapon/projectile compatibility when selecting firing sounds, addressing cases where bows, matchlocks or other weapons selected an unrelated cannon sound. The incoming-projectile path and other native scoring/cache behavior retain their rules.
- **War Is Slaughter progression:** a winning general must achieve a **Heroic Victory** with **at least 80% enemy casualties**, followed by the native **chance-10** trait roll. Applies to Shogun/ROTS and FOTS. The own-army-loss condition is removed; existing trait levels, effects and the separate Ikko creation roll remain.
- **Mod launcher:** retains compressed CE/PFH3 mod-pack reading, custom-mod discovery in `RemasteredCE/data`, and **Use existing user.script.txt (ignore selections)** mode. The corrected launcher is included in installation and offline repair.
- **Mod preservation during upgrades:** custom `.pack` files under the managed `data` folder are retained alongside the existing `mods` folder. Base-game archives are replaced by the new release as intended; conflicting or linked custom sources are rejected rather than overwritten.
- **Retained content:** existing night reinforcements, Hell difficulty, gameplay fixes, artwork, blood/smoke and other previously released content remain.

The withdrawn renderer-threading and recent caching/GC/input optimization experiments are **not included**. No new FPS or map-loading gain is claimed.

## Install or update

Download and extract **RemasteredCE_Installer_Preview.zip**. Keep `RemasteredCE_Setup.exe` and its `.config` together, close the game and other launcher windows, then run setup and choose **Install / Update**. Existing users should use the new setup executable so they receive the corrected mod launcher. Both the original Shogun 2 and Complete Edition installations are required.

The installer reconstructs the patch from local game files and checks the generated outputs. Full game packs and engine DLLs are not distributed. Native/asset checks and installer reconstruction/publication verification are documented with the release; these do not establish that every third-party mod or live multiplayer scenario is compatible.
