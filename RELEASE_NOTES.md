# Remastered CE 0.1.3 preview

By JakeTheRipper.

**Install / Update Remastered CE now downloads updates directly from GitHub.** Leave GitHub selected, then click Install / Update. The installer checks published releases (including prereleases), downloads the newest signed `.rce` package, verifies its signature and version, and installs through the existing staged update process. It reports when the installed version is already current and does not downgrade it automatically.

The **Offline...** menu lets you use the bundled release or select a downloaded `.rce` file. Network failures leave the game installation untouched. No GitHub sign-in is required.

Download and extract **RemasteredCE_Installer_Preview.zip** once to get this new application. The `.rce` package alone does not add online updating to an older installer.

Uninstall remains available. Generated game contents retain the shader fix and match the previously tested build. Fresh installation and in-game launch were tested on that build. Online updater tests cover version ordering, current-version/downgrade handling, prerelease/draft selection, download address restrictions, signed package version matching, and cancellation. A live GitHub download and signature check also passed without changing the installed game.
