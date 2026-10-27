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
