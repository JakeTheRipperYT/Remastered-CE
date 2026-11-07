# Religion switching in the alternate engine

The user authorized integrating their supplied `religion_swap` package into
CE8.dll, and explicitly chose to include its AI conversion change. This private
update does not change CE.dll or the nine normal pack recipes. It does not run
the supplied installer, rewrite user.script.txt, or compile engine code.

`build_religion_sim8.py` captures the seven v5 Old/New ranges and the original
pack in `work/religion-sim8`, recording their provenance hashes. Each original
range must match both the original Steam CE DLL and the installed 0.1.78/79 Sim
engine at its PE-mapped RVA. Original file offsets are not reused against the
private DLL's different raw layout. Conflicts stop the build. Only these seven
ranges and the PE checksum change; length, section layout, relocation table,
existing Sim helpers, farm/agent helpers and their unwind records are retained.

The supplied code changes player conversion to select connected existing
religion records in cyclic table order. A mode-2 leaf eligibility helper enables
the player's conversion button and the campaign action dispatches in mode 2.
The AI code uses mode 3 and selects a different religion whose native support
value exceeds 74, retaining the strongest qualifying candidate. Its original
campaign-specific eligibility logic is retained where the supplied patch calls
it. This is the supplied mod's behavior, not a new gameplay design.

The four supplied incident/option/payload/localization entries are compressed
with the project's existing LZ4 resource and added to data.sim8. The Freedom of
Faith incident carries UNLOCK_STATE_RELIGION_CHANGE. No standalone .pack is
installed. The alternate container preserves every previous record and payload,
including the Sim lobby and gifting entries; its non-.pack extension and the
existing alternate-engine redirects keep it specific to the Sim checkbox.

The resulting normal-to-alternate engine/data recipe is registered in
`source/current-installer.json`; build through `source/Build-Current.ps1`.
Version 0.1.80 uses the signed 0.1.79 package as its cumulative baseline.
The existing launcher layout and bootstrap are inherited.

Verification: `verify_religion_sim8.py` checks all seven native ranges, unchanged
bytes outside them/checksum, native branch targets and embedded strings, and 186
relative-reference cases across three load bases. The actual signed installer
reconstructs the normal DLL from original bytes plus its unchanged helper/post
recipes, then runs EngineMode.Stage and EngineMode.Verify. Its alternate DLL
must equal the candidate byte for byte and its four added assets must decompress
identically. Normal manifest sources/files/engine/post patches/helper remain
identical to .79. All 36 launcher self-tests pass. These are structural and
installer checks, not campaign or multiplayer gameplay acceptance.

Expected alternate SHA256:
35e507fc3adf6893cb78afe346b61d7342594bacc4793827c57ad26d857a4541

Expected mode data SHA256:
fab6bc36fa102990005f67c997f7d9a79d1149c7535d787f05c07adc1e6663ce

Installed local updates use the reconstructed alternate engine/data and matching
signed release/launcher/state records only. No original Steam files, normal
packs, saves, profiles or scripts are replaced. No backups or publication are
authorized by this integration.
