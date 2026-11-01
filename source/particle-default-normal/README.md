# Default particle normal packing correction (private 0.1.63)

Live result: the user confirmed0.1.63 did NOT resolve smoke flashing. The user confirmed 0.1.62 did not resolve close-camera strafe flashing.

CE particle_volumetric.hlsl changes the first normal read from RGB to RAB (red/alpha/blue). The shipped default_pfx_packed_normal.dds is byte-identical to OG: its RGB contains the normal and its alpha is constant one. CE therefore loses the green component. Other effect maps use RAB, so changing the shared shader to RGB would break correctly packed custom maps.

Repack only this default DDS: preserve all decoded RGB bytes and copy green into alpha for each of its eight mip levels. Store it as conventional legacy DDS A8R8G8B8/BGRA8, avoiding another lossy compression step. The texture grows from87520 to349648 bytes. Diffuse smoke opacity, particle shader bytecode, native engine, custom maps and the other eight archive recipes remain unchanged. No shader cache update is needed.

Correction to earlier investigation: OG already decoded its RGB normal twice (the OG unpack_normal helper returns2*x-1 without normalization). Double decoding is inherited, not a new CE regression. The earlier62-degree metric compared CE to an intended once-decoded normal, not actual OG output. This patch preserves the inherited decode math and corrects only CE's channel mismatch.

Verification executes installed pixel shaders with real source BC3 and candidate BGRA8 textures on D3D11 WARP and hardware, comparing against the same shader with an RGB reader.376 cases per device cover mip/UV scales, particle rotations, SH term counts, probe blending, fog, depth, shroud and alpha blending. Alpha/coverage are unchanged. RGB reference residual maxima:0.001689 WARP and0.004108 hardware, reflecting BC3 decoder rounding differences when converting to bytes; original wrong-channel errors reach0.1167 in these fixtures. CPU checks preserve RGB exactly and map alpha to original green at every texel of all eight mips. Tests do not establish that this resolves the reported flashing.

Work and signed package verification: F:/Codex/Remastered-CE-Port/work/particle-default-normal and work/release-063. No public release or update feed changes.
