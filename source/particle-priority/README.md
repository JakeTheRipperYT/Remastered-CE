# Further particle cost reductions — private 0.1.60

Builds on the user-accepted 0.1.59 particle fixes. No complete game assets or
compiled game shaders are included here. The tools read local originals and
produce reviewable candidate sources and DXBC on F:.

## Priority pass

1. **Fog:** separate noise-density integration from atmospheric scattering.
   The native shader's shadow visibility is always 1 and its fog mask is disabled.
   Preserve the original density samples and scattering accumulation, but skip
   atmospheric work once the final fog completely obscures its contribution.
   This is a bounded shader optimization, not a shared cross-particle fog cache.
2. **Invisible pixels:** discard exactly zero alpha after soft-depth fading,
   exclusively for alpha-blended particle techniques. Do not raise an opacity
   cutoff or apply this change to additive techniques.
3. **Ambient lighting:** when the probe blend is exactly zero, evaluate only the
   previous probe set. The original evaluates both and discards the current
   contribution in its final lerp. Preserve all other blend values.
4. **Quality plumbing:** traced the native constructor. It registers full-quality
   alpha and additive techniques, not the unused `_lq` source entry points. No
   graphics setting, quality reduction or invented native quality mapping is added.
5. **Vertex calculations:** share equal X/Y scale exponents, and bypass powers
   for gamma 1. Screen splats use an X-only identity fast path, preserving their
   original input-component usage. No native particle-record or sorting change.

Full shared fog buffers and computing all per-particle invariants once for the
four vertices remain renderer architecture work. This release does not claim
to implement either of those larger changes.

## Native blend proof

`181a21620` registers alpha main/offscreen and additive main/offscreen techniques.
Alpha RGB blending is `SRC_ALPHA / INV_SRC_ALPHA`. Alpha blending also has a
zero-source-alpha identity. The 64-bit depth-state assignment sets depth-enable
and clears the adjacent depth-write mask; offscreen techniques disable both.
Consequently a zero-alpha fragment has no colour, alpha or depth contribution
in these alpha passes. The additive shaders retain their previous behaviour.
`181a211f0` registers corresponding screen-splat techniques. These findings were
checked against the original CE pseudocode and native shader entry names.

## Validation

- Compiler control reproduces each accepted 0.1.59 shader instruction stream.
- All shader resources, constant layouts and stage signatures remain unchanged.
- 352 pixel cases per device match the original exactly, including native alpha
  blending, zero/near-zero soft fades, opaque fog, density/noise variations,
  probe blends, and campaign-weather markers.
- Actual vertex DXBC is executed through D3D11 stream output: 252 vertices for
  each of three shaders, covering lifetime boundaries, all billboard corners,
  equal/unequal scale exponents and gamma 1. Outputs match exactly in these cases.
- The pixel and vertex checks pass on both D3D11 WARP and the hardware GPU.
- The signed installer reconstructs all 786 main shader assets and all 59
  campaign override assets. Engine/helper and seven other archives are retained.
- Local cache refresh verifies the old bytecode before updating two existing
  particle cache entries. Nothing is published or pushed to GitHub.

Synthetic GPU timestamps, 512x512 with 16 draws, alternating old/new shader:
at probe blend zero, candidate time was approximately 60–66% of baseline time.
The fog-only change was modest: around 3% less time with noise off and essentially
neutral in the other sampled cases. These figures are not battle FPS measurements.
Battle confirmation for 0.1.60 remains pending.

## Reproduction

Windows, Python 3, D3DCompiler 47, Windows SDK headers and the installer's x64
`lz4.dll` are required. Supply an extracted 0.1.59 RemasteredCE directory with:

- `data/shaders.pack`: `72f63419db64ce21fab8b4c03e3d9a2dd1ffa41735ea2857f9578add2f9429e6`
- `data/rce_campaign_night_visuals.pack`: `069d979bcc8ed47465bad1a416fc2c37a21111ed31ffc5798c56b4456607d112`

```powershell
py -3 -B build_priority.py --game-root F:/path/to/0.1.59/RemasteredCE --work F:/Codex/Temp/particle-060 --lz4 F:/path/to/lz4.dll
py -3 -B test_vertex_gpu.py --baseline F:/path/to/0.1.59/RemasteredCE/data/shaders.pack --overlay F:/path/to/0.1.59/RemasteredCE/data/rce_campaign_night_visuals.pack --work F:/Codex/Temp/particle-060 --lz4 F:/path/to/lz4.dll --hardware
```

Omit `--hardware` to use WARP. The vertex test also runs the pixel comparisons.
`build_candidate.py` supplies shared compiler/pack utilities; use `build_priority.py`
as this release's entry point. Repository-source reproduction matched all ten
payloads in the signed and installed 0.1.60 candidate.
