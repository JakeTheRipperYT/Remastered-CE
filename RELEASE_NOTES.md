# Remastered CE 0.1.25 preview

By **JakeTheRipper**.

This cumulative release retains 0.1.20 and adds:

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
