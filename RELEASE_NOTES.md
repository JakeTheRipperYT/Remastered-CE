# Remastered CE 0.1.16 preview

By **JakeTheRipper**.

This release includes every prior 0.1.12 patch recipe, the newer banner and battle-audio fixes, and the corrected independent Hell mode.

- Restore naval fleet-count banner geometry.
- Correct movement pitch and start-delay controls in 48 infantry/cavalry sound banks.
- Increase 47 combat sound banks by 3 dB and restore 430 matched-combat sound-timing files. The combined stab/kill-move correction was confirmed in local play.
- Add seven-pack installer support while retaining backward-compatible uninstall handling.
- Give Hell its own campaign/human/AI difficulty IDs and 21 copied modifier rows, with battle realism, fame threshold -1 and `auto_save_hell.{clan}` autosaves.
- Restore the original hardest-difficulty starting enemy armies/rebellions for all nine affected clans under Hell. Start a new Hell campaign for the initial spawns; existing campaigns are not retroactively populated.

**Upgrade from 0.1.12:** Download and extract this release's installer ZIP once, then run `RemasteredCE_Setup.exe`. The game launcher itself is unchanged. Automatic installer self-updating remains excluded. Previously withdrawn builds are superseded by this release; the archived original 0.1.12 download remains available.

The final installer rebuild was compared with the tested local installation. Native checks cover Hell's IDs, modifiers, startup/load handling, realism, autosave prefix and fame threshold. Lua 5.1 execution checks cover exact starting-force calls, original difficulties and multiplayer suppression. The user confirmed the corrected local result; these checks do not establish that every possible save/campaign path was played through.

The patch reconstructs files from locally installed original and Complete Edition games. Complete game packs and engine DLLs are not distributed. See CHANGELOG.md for all 40 documented entries and source/hell/ for the inspectable Hell implementation.
