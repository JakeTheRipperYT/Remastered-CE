# Remastered CE launcher icon

White-helmet edit of the locally extracted CE application icon, made using the built-in image generation tool. The original unmodified CE icon is not included here.

Prompt: Change only the helmet's black lacquer dome and dark side/neck armor plates to ivory-white lacquer with silver-grey shading. Preserve its silhouette, viewing angle, gold crest and decorations, purple ties, rendered style, and transparent background. No text or added elements.

RemasteredCE.ico contains 16, 24, 32, 48, 64, 128, and 256 pixel sizes. launcher.rc embeds it and JakeTheRipper creator metadata in the native launcher. The installer also uses this icon.

See ICON_PROMPT.txt for the complete final image-edit prompt. Compile launcher.rc with the Windows SDK resource compiler, then link that .res with launcher.c compiled using /Od /GS-, /entry:entry, /nodefaultlib, /subsystem:windows, kernel32.lib and user32.lib. The launcher has no CRT dependency.
