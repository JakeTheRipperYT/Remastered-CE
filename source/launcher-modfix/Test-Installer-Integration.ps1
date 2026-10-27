param([Parameter(Mandatory=$true)][string]$Executable)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Web.Extensions
$exe = [IO.Path]::GetFullPath($Executable)
[Reflection.Assembly]::LoadFrom($exe) | Out-Null
$root = Join-Path ([IO.Path]::GetTempPath()) ('RCE-install-integration-' + [Guid]::NewGuid().ToString('N'))
[IO.Directory]::CreateDirectory($root) | Out-Null
$script:passed = 0
function Assert($ok,$message) { if(!$ok) { throw $message }; $script:passed++; "PASS: $message" }
$release = [RemasteredCE.Release]::Load($null)
try {
    $state = New-Object 'Collections.Generic.Dictionary[string,object]'
    [RemasteredCE.InstallerLauncher]::Stage($release,$root,$state)
    $installed = Join-Path $root 'RemasteredCE_Launcher.exe'
    $expected = [RemasteredCE.Engine]::FileHash($exe)
    Assert (([RemasteredCE.Engine]::FileHash($installed)) -eq $expected) 'Install/update stages the executing fixed combined launcher'
    Assert (!(Test-Path -LiteralPath ($installed + '.config'))) 'Fixture matches a fresh installed launcher without a sidecar config'
    $installedLog = Join-Path $root 'installed-launcher-selftest.txt'
    $installedProcess = Start-Process -FilePath $installed -ArgumentList '--self-test',('"' + $installedLog + '"') -WindowStyle Hidden -Wait -PassThru
    Assert ($installedProcess.ExitCode -eq 0 -and (Test-Path -LiteralPath $installedLog)) 'Fresh installed launcher runs its complete built-in self-tests'
    Assert ($state['unifiedLauncherSha256'] -eq $expected) 'Ownership records the installed fixed launcher hash'
    Assert ($state['unifiedLauncherBuild'] -eq '0.1.25-modfix2') 'Installed launcher build is recorded'
    Assert (([RemasteredCE.Engine]::FileHash((Join-Path $root 'release.rce'))) -eq $release.PackageHash) 'Signed offline package remains byte-identical'
    $offline = [RemasteredCE.Release]::Load((Join-Path $root 'release.rce'))
    try { Assert ($offline.PackageHash -eq [RemasteredCE.InstallerLauncher]::PackageHash) 'Preserved offline package still passes signature verification' } finally { $offline.Dispose() }
    Assert (([RemasteredCE.Engine]::Hash($release.ModManager)) -eq [RemasteredCE.InstallerLauncher]::OriginalLauncherHash) 'Signed embedded launcher payload remains unchanged'
    $game = Join-Path $root 'same-version-game'
    $private = Join-Path $game 'RemasteredCE'
    [IO.Directory]::CreateDirectory($private) | Out-Null
    $target = Join-Path $private 'RemasteredCE_Launcher.exe'
    $record = Join-Path $private 'install-state.json'
    [IO.File]::WriteAllBytes($target,$release.ModManager)
    $owned = @{version='0.1.25-preview';packageSha256=$release.PackageHash;unifiedLauncherSha256=[RemasteredCE.InstallerLauncher]::OriginalLauncherHash}
    [IO.File]::WriteAllText($record,($owned | ConvertTo-Json))
    Assert ([RemasteredCE.InstallerLauncher]::NeedsUpdate($game,'0.1.25-preview','0.1.25-preview')) 'Existing original 0.1.25 installation receives the launcher fix at the same engine version'
    Assert (![RemasteredCE.InstallerLauncher]::NeedsUpdate($game,'0.1.26-preview','0.1.25-preview')) 'Same-version launcher repair cannot downgrade a newer engine release'
    [IO.File]::Copy($exe,$target,$true)
    $owned.unifiedLauncherSha256=$expected
    [IO.File]::WriteAllText($record,($owned | ConvertTo-Json))
    Assert (![RemasteredCE.InstallerLauncher]::NeedsUpdate($game,'0.1.25-preview','0.1.25-preview')) 'Already corrected or unknown newer launcher builds are kept'
    $owned.unifiedLauncherSha256=[RemasteredCE.InstallerLauncher]::OriginalLauncherHash
    [IO.File]::WriteAllText($record,($owned | ConvertTo-Json))
    $rejected=$false
    try { [RemasteredCE.InstallerLauncher]::NeedsUpdate($game,'0.1.25-preview','0.1.25-preview') | Out-Null } catch { $rejected=$true }
    Assert $rejected 'An edited launcher is protected during same-version online update checks'
    [IO.File]::WriteAllBytes($target,$release.ModManager)
    [IO.File]::WriteAllText($record,($owned | ConvertTo-Json))
    $data = Join-Path $private 'data'
    [IO.Directory]::CreateDirectory($data) | Out-Null
    [IO.File]::WriteAllText((Join-Path $data 'custom.pack'),'user mod retained')
    Assert ([RemasteredCE.InstallerLauncher]::Repair($game)) 'Same-version online update applies the launcher-only repair'
    Assert (([RemasteredCE.Engine]::FileHash($target)) -eq $expected -and (Get-Content $record -Raw | ConvertFrom-Json).unifiedLauncherSha256 -eq $expected) 'Launcher-only repair publishes matching executable and ownership hashes'
    Assert (([IO.File]::ReadAllText((Join-Path $data 'custom.pack'))) -eq 'user mod retained') 'Same-version repair preserves custom mods without reconstructing game packs'
    Assert (![RemasteredCE.InstallerLauncher]::Repair($game)) 'Repeated same-version repair is idempotent'
    [IO.File]::WriteAllBytes($target,$release.ModManager)
    [IO.File]::WriteAllText($record,($owned | ConvertTo-Json))
    $originalRecord = [IO.File]::ReadAllBytes($record)
    $stateLock = [IO.File]::Open($record,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
    $rejected=$false
    try { [RemasteredCE.InstallerLauncher]::Repair($game) | Out-Null } catch { $rejected=$true } finally { $stateLock.Dispose() }
    Assert ($rejected -and ([RemasteredCE.Engine]::FileHash($target)) -eq [RemasteredCE.InstallerLauncher]::OriginalLauncherHash -and ([RemasteredCE.Engine]::Hash([IO.File]::ReadAllBytes($record))) -eq [RemasteredCE.Engine]::Hash($originalRecord)) 'Ownership-write failure rolls the launcher-only repair back exactly'
    $release.PackageHash = 'future-package'
    Assert (([RemasteredCE.Engine]::Hash([RemasteredCE.InstallerLauncher]::Select($release))) -eq [RemasteredCE.InstallerLauncher]::OriginalLauncherHash) 'Future packages retain their own signed launcher payload'
    $release.PackageHash = [RemasteredCE.InstallerLauncher]::PackageHash
    $release.ModManager = [byte[]]@(1,2,3)
    $rejected = $false
    try { [RemasteredCE.InstallerLauncher]::Select($release) | Out-Null } catch { $rejected = $true }
    Assert $rejected 'Pinned-package launcher mismatch is rejected'
    $release.ModManager = $null
    Assert ($null -eq [RemasteredCE.InstallerLauncher]::Select($release)) 'Packages without a combined launcher remain supported'
    "Passed $script:passed installer integration checks. Fixture: $root"
} finally { $release.Dispose() }
