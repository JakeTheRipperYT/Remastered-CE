# Campaign naval fleet-count bars

Complete Edition shortened `rigidmodels/flags/sho_char_flag_naval.rigid_model_v2`, removing the bottom section of the flag. The remaining indexed geometry ends at vertical UV coordinate 0.86181640625; the original reaches 0.9990234375. The lower model bound also moved upward from Y 1.72994518 to 2.00629926.

The original and CE ship-count formula is unchanged: reveal the count texture where UV Y is at least `1 - ships / 32`. Four ships require Y >= 0.875, entirely outside the CE mesh. Larger fleets lose approximately 4.42 ship intervals from the visible bottom of the banner.

The original and CE strength-bar texture and atlas mapping are identical. The shader's count-blending expression is unchanged. The repair restores original vertices, indices and bounds, retaining CE's version-2 format and material descriptor. The installer reconstructs this asset from the user's local original-game archive.

Static model/pack verification and a full signed-package installer rebuild passed. Local in-game testing of the repaired four-ship player and ten-ship enemy fleets remains pending.
