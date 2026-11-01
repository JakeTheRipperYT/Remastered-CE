# Particle shader cost reduction — private 0.1.59 candidate

The alpha-particle fog shader evaluates ambient spherical harmonics at the fixed
normal `(0,1,0)`. Five of nine coefficients are zero, but the original compiled
loop still fetches their textures. This patch processes only coefficients
`0,2,7,8`, preserving their order and the runtime coefficient count. General
particle lighting retains the original loop.

Particle fog is bypassed when `g_fog_lerp` is exactly zero. The normal-map path
reuses its first sample when both interpolated UV pairs are identical; distinct
animation frames still receive two samples. The conditional second sample uses
explicit gradients. Scene-depth rejection remains ahead of normal sampling.

The fog model, scattering steps, particle counts, opacity and lifetime remain
unchanged. Low-quality lighting plumbing and moving particle simulation between
CPU/GPU are outside this candidate. The user confirmed steadier frame rates in
battle, including heavy particle fog; no numerical FPS delta was measured.

## Reproduction

Requires Windows, Python 3, `d3dcompiler_47.dll`, and Windows SDK headers for the
D3D11 comparison harness. No third-party Python packages are needed. Reading the
campaign override pack also requires the installer's x64 `lz4.dll` (use `--lz4`). Supply the
0.1.58 installed shader archive, SHA256
`557b8609be67db84a06369970b276b6eb3c4a4e8ddba803f5aa64544f17ff228`.
The tool rejects other baselines. Game assets and binaries are read locally;
this directory contains no complete game shader sources or compiled game shaders.

For the installed remaster, also supply `--overlay` with its 0.1.58
`rce_campaign_night_visuals.pack`, SHA256
`55b0baa62325ffce2a16533a8bc0605b687ede93e3c3b79b4319823d1d9ec097`.
The override contains the active weather-aware particle shaders. Its changes
must be retained; optimizing only the lower-priority main archive is insufficient.

```powershell
$common = @('--baseline','F:/path/to/0.1.58/shaders.pack','--overlay','F:/path/to/0.1.58/rce_campaign_night_visuals.pack','--lz4','F:/path/to/lz4.dll','--work','F:/Codex/Temp/particle-build')
py -3 -B build_candidate.py @common
py -3 -B test_candidate_gpu.py @common
py -3 -B test_candidate_gpu.py @common --hardware
```

The builder reproduces the installed instruction stream before editing, checks
all shader interfaces, preserves engine wrappers, and verifies all 786 archive
entries. In overlay mode, two compiled pixel shaders and four HLSL include files
change; 780 main archive payloads retain their exact bytes. The two include files
and two pixel shaders owned by the override must also be updated there. All other
55 override payloads and every vertex shader remain unchanged. Without overlay
mode the tool also supports the five vanilla particle pixel shaders.

Local verification of the active weather-aware candidate: 272 render comparisons
on D3D11 WARP and another 272 on the hardware GPU, comparing 156,672 float pixels
per device with zero differences. The five vanilla shaders also passed 620
comparisons per device during development.
Coverage includes all coefficient counts 0–9, current/previous probe blends,
SH enabled/disabled, animated/default normal UVs, mip scales, fog off/partial/on,
both fog modes, noise on/off, shroud, readable depth, alpha rejection and all
reserved campaign-weather particle lighting markers at three night strengths.
These are controlled shader comparisons, not a complete in-game visual test.

The signed private installer reconstructs all 786 shader assets and all 59
campaign override assets, matching the GPU-tested payloads. The 0.1.58 selection-fixed engine, helper and seven other
archives are retained. Local deployment also refreshes the two existing particle
shader cache entries after verifying their old instruction streams. No public
release or update feed has been changed.
