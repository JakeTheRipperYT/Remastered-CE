# Remastered CE 0.1.12 preview

By **JakeTheRipper**.

- **Hell difficulty:** Enforces Legendary battle realism after deployment and restores Legendary-style automatic saving, using `auto_save_hell.{clan}` names. Hell keeps instant Realm Divide and Legendary AI difficulty values.
- **Yari wall:** Engaged units now process movement orders without requiring the player to disable yari wall. Confirmed working in-game.
- **Kneel fire:** Removed the kneel-fire-specific movement eligibility block. Other eligibility checks and firing-drill behaviour remain in place; packaged native checks passed, with fresh in-game confirmation still pending.
- **Naval AI:** Replaced the naval holding group with CE's normal naval attack group so defending fleets engage. Confirmed working in-game. This changes tactical group behaviour, not campaign battle ownership or victory conditions.
- **Drop-in battles:** Pre-battle selection respects the campaign's saved setting; changes on that screen are also saved.

Existing installer versions **0.1.10 and newer** can obtain this release through **Install / Update**. For a fresh installation, download **RemasteredCE_Installer_Preview.zip**, extract it and run the included setup. Older installer applications need replacement with the current ZIP.

All earlier content is retained. **Orendiz** is credited for the blood/smoke rework. The naval attacker-group approach was also reported by **pad345654** in the [Shogun 2 Bugfix Mod](https://www.moddb.com/mods/shogun-2-bugfix-mod/downloads/total-war-shogun-2-bugfix-mod); this release implements it against CE's own engine.

Release validation compares the reconstructed engine code/data against the locally tested build, checks relocated helper targets and native rules, and rebuilds all five packs from the signed package. A fresh launcher uninstall/reinstall gameplay test remains pending.
