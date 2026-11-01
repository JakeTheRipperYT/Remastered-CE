 Remastered CE 0.1.55 Preview

This cumulative release includes all previously published content and the changes tested in the private previews through0.1.54.

- Restore campaign settlement damage smoke, flames and siege effects when an unloaded battle terrain previously supplied an invalid season.
- Add smooth main-campaign day/night transitions when toggling the pre-battle Night attack option.
- Add a saved Always night campaign map setting in Graphics → Advanced. It overrides the temporary campaign preview and renders battles using their night scene without granting night-battle traits or changing reinforcement rules.
- Add small warm amber floating lantern particles to the main campaign's night appearance in all four seasons; retain normal seasonal particles by day.
- Add campaign-battle weather forecasts with constant weather or repeating combinations of clear, rain, heavy rain, fog and seasonal snow. The Wait button keeps its existing limit; weather cycles in the order described by the forecast until battle end. Custom and historical battles retain their existing weather behavior.
- Blend sky, rain/snow, lighting, colour and exposure through weather changes with synchronized rain/sky timing. Keep the sky heading fixed and avoid abrupt scene flashes. Rainy weather includes native lightning and thunder.
- Preserve the battle's starting puddle layout and materials throughout combat. Rain-start battles retain their puddles; dry-start battles do not gain puddles or lose grass later. Other wet shading can still respond to weather.
- Update campaign-battle unit information cards' Accuracy and Reload Skill values and modifier bars using native current-weather effects. Red penalty bars recover from UI refreshes and remain while the penalty applies. Fatigue is outside this display change.
- Repair sound-bank unit references for CE's changed registry, including affected garrison and Ikko warrior-nun memberships.
- Add an arrow control for the collapsible Spacebar battle-options panel.

The retained grass dithering correction, firing-audio fix, Heroic Victory trait trigger, night reinforcements, Hell difficulty, artwork, blood/smoke, corrected mod launcher and other earlier content remain included. Withdrawn renderer/threading/caching/GC/input experiments remain excluded; no new performance gain is claimed.

 Install or update

Download and extract RemasteredCE_Installer_Preview.zip. Keep setup and its .config together, close the game and launcher windows, then choose Install / Update. Use the new setup for this release: older setup versions cannot install its nine-pack layout. Both original SHOGUN2 and Complete Edition installations are required. The installer reconstructs and verifies the patch from local files; complete game archives and engine DLLs are not distributed.

The signed offline package is embedded in setup; select Offline → Use included release (offline) to install without GitHub. New and existing users receive the same cumulative release. Custom mods are preserved by the installer; compatibility with every third-party mod is not claimed.
