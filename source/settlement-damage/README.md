# Campaign particle season source

CE can allocate its battle-terrain service while displaying the campaign map,
without loading a battle map into it. The particle update treated that non-null
service as the season authority. Its uninitialized season can be outside 0â€“3,
which pauses looping particles even when every season is enabled in their XML.

An authorized read-only inspection of a main-campaign reproduction found:

- The damaged castle's smoke attachment and particle handle existed.
- Its GPU particle backend was looped and paused, with zero live particles.
- The battle-terrain service was **unloaded** (`+0x100 == 0`), but its season
  field (`+0x17a4`) contained `467`.
- The campaign source contained the valid autumn season `2`.

`patch_season_source.py` changes the existing 87-byte selection window in
`181b9f130`: battle terrain supplies the season only when its map is loaded.
Otherwise the existing campaign calendar supplies it. Active-battle behavior,
the missing-source default, emitter ownership, repair/removal, shroud checks,
and effect definitions are retained. The PE checksum is regenerated. No additional code section or unwind
metadata is needed. This repairs the source of the seasonal pause; it does not
disable seasonal filtering or add flames to ordinary-damage definitions.

## Reproduce and verify

Use locally installed game files. Generated DLLs and raw game assets must stay
outside the repository. The generator rejects unexpected bytes and refuses an
output path equal to the input path.

```powershell
python patch_season_source.py --input 'F:/private/CE.dll' --output 'F:/private/CE.season-candidate.dll'
python test_native_season.py 'F:/private/CE.dll' 'F:/private/CE.season-candidate.dll' 'F:/private/verification.json'
```

The patch generator uses Python's standard library. The native tests additionally
require `pefile` and `unicorn` on the Python module path. They execute the actual
engine instructions in an emulator, without loading or modifying a game process.

The verification covers 270 selection cases at three image bases and actual
particle-backend recovery at each base. It checks absent, unloaded and loaded
battle terrain; all four campaign seasons; missing campaign terrain; stray
season values; stack restoration and preserved registers. The native backend
changes from paused/zero-live at season `467` to running/ten-live at season `2`.
Only renderer-query/metadata callbacks and the final bounds update use fixtures.

Validated baseline Remastered engine SHA-256:
`c96911015b11f69a4fd8c7ff6e30aba43e61bfe88913dfe64d1f6348f14fe1c1`.
Candidate SHA-256:
`3d596a060f936e57f8ea188c15b8f2cd0b510079c1b7b77b545b3216ee7d115f`.

Installer integration must apply the patch at the pre-injection PE file offset,
then verify the final injected engine hash. The native redirect helper shifts
file offsets by 512 bytes in this baseline; RVAs remain unchanged. The generator
resolves the offset from the input's PE section table instead of assuming it.
