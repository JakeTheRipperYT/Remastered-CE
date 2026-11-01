# Particle depth stability — private 0.1.61 candidate

The user reports pre-existing gun-smoke flashing when strafing the camera close
to particles. This candidate corrects a proven CE depth-addressing error. It does
not claim to establish that this is the only cause of the reported flashing.

CE computes particle depth UVs as `SV_Position.xy / render_target_dimensions`,
then its legacy depth helper fetches `int2(uv * (screen_size - 1))`. At matching
resolutions this can read a neighbouring pixel. If the readable-depth texture
differs in size, the fetch can address the wrong region or go out of bounds.
Particle visibility and soft fading then use unrelated scene depth as geometry
moves across pixels.

OG's non-MSAA helper instead samples the texture using its sampler, and its
particle UV calculation also differs. The CE non-MSAA integer-fetch combination
is therefore not a direct equivalent of OG's sampling path.

The fix queries the readable-depth texture's actual dimensions, computes
`floor(uv * dimensions)`, clamps to valid texel coordinates, and retains the
existing depth reconstruction, occlusion comparison and soft fade. The source
also supports the MSAA sample-zero path. Two legacy Texture2D overloads are now
excluded from the MSAA branch because they reference a function declared only
in the non-MSAA branch; without that guard the original source fails compilation
with the MSAA macros enabled.

## Validation

- Five installed pixel shader instruction streams are reproduced before editing.
- Interfaces, constant layouts, bindings and engine wrappers are retained.
- 880 uniform-depth cases per device match the original output exactly.
- 435 moving-depth-edge cases per device exercise depth textures at half,
  matching and double the render-target size. The old shaders make 57,080
  incorrect visibility decisions across these cases; the candidate makes zero.
- Render comparisons run on hardware and D3D11 WARP. They are synthetic depth
  tests, not a recording of the user's flashing smoke.
- Source compilation passes for MSAA 2/4/8; multisample rendering is not tested.
- The signed installer reconstructs 786 main shader assets and 59 campaign
  override assets. The engine, helper, all vertex shaders and seven other
  archives retain their previous content. Earlier performance and selection
  changes are preserved.
- Close-camera gun-smoke flashing requires live confirmation. Sorting,
  transparency overlap, near-plane effects and temporal fog noise remain
  possible separate sources of instability if the symptom persists.

## Reproduction

Requires Windows, Python 3, D3DCompiler 47, Windows SDK headers for the GPU test,
and the installer's x64 `lz4.dll`. No original game sources are distributed here.
Supply local 0.1.60 files:

- `data/shaders.pack`: `bdad67a5548b3b181dd28acc589b8875bc0f1bf2cac8d4e1432a3f8551e12459`
- `data/rce_campaign_night_visuals.pack`: `703dc62e15c5931f7d797df70743db1e290070364a55826d23a5e4e0b1fe9a4f`

The two main smoke shaders use the current weather-aware source. The other three
pixel shaders retained older compiled bodies, so the builder control-matches
their vanilla CE sources and applies only the depth fix to those binaries.
The published HLSL source retains all cumulative changes.

```powershell
py -3 -B build_camera.py --game-root F:/path/to/0.1.60/RemasteredCE --vanilla D:/path/to/original/CE/data/shaders.pack --work F:/Codex/Temp/particle-camera --lz4 F:/path/to/lz4.dll --check-msaa
py -3 -B test_camera_gpu.py --baseline F:/path/to/0.1.60/RemasteredCE/data/shaders.pack --overlay F:/path/to/0.1.60/RemasteredCE/data/rce_campaign_night_visuals.pack --work F:/Codex/Temp/particle-camera --lz4 F:/path/to/lz4.dll --hardware
```

Omit `--hardware` for WARP. `build_candidate.py` provides shared compiler and
pack utilities; this release's builder is `build_camera.py`.

## Remaining renderer work

OG's particle VS outputs `fog_factors` at TEXCOORD6 and calls
`calc_vertex_volume_fog`; its PS consumes those factors. CE removed that varying
and evaluates the newer fog model in the pixel shader. Reusing fog across
particles or restoring a suitable precomputed stage remains separate work.

Native alpha/additive techniques are registered in `181a21620`; both currently
select `particle_vertex_30`. Splitting a new fog-producing vertex technique from
the additive path requires checking native material registration and resource
binding, not just inserting a varying. The shared shader base `181ab1730`
attaches fourteen global parameter-block pointers from its registry object.
This identifies a binding path to investigate; it is not proof that new fog
resources would automatically bind correctly in another shader stage.
