param([string]$BuildRoot = "$PSScriptRoot/_build")
$ErrorActionPreference = 'Stop'
$root = Join-Path ([IO.Path]::GetTempPath()) ('RCE-deploy-' + [Guid]::NewGuid().ToString('N').Substring(0,8))
$hotfix = Join-Path $BuildRoot 'hotfix'
$original = Join-Path $BuildRoot 'original-manager.exe'
$originalHash = (Get-FileHash $original).Hash
$newHash = (Get-FileHash (Join-Path $hotfix 'RemasteredCE_Launcher.exe')).Hash
$game = Join-Path $root 'game'
$private = Join-Path $game 'RemasteredCE'
New-Item -ItemType Directory -Force $private | Out-Null
[IO.File]::WriteAllText((Join-Path $game 'shogun2_complete_edition.exe'),'fixture only')
Copy-Item $original (Join-Path $private 'RemasteredCE_Launcher.exe')
$record = Join-Path $private 'install-state.json'
$initialState = '{"schema":1,"version":"0.1.25-preview","engineHash":"unchanged","files":[{"file":"data/data.pack","sha256":"unchanged"}],"unifiedLauncherSha256":"' + $originalHash.ToLowerInvariant() + '"}'
[IO.File]::WriteAllText($record,$initialState)
$recordHash = (Get-FileHash $record).Hash
function Apply([bool]$restore = $false) {
    $args = @('-NoProfile','-ExecutionPolicy','Bypass','-File',(Join-Path $hotfix 'Apply-Launcher-Fix.ps1'),'-GameFolder',$game)
    if($restore) { $args += '-Restore' }
    & powershell.exe @args
    if($LASTEXITCODE -ne 0) { throw 'Deployment command failed' }
}
Apply
if((Get-FileHash (Join-Path $private 'RemasteredCE_Launcher.exe')).Hash -ne $newHash) { throw 'Executable replacement failed' }
$state = Get-Content $record -Raw | ConvertFrom-Json
if($state.unifiedLauncherSha256 -ne $newHash.ToLowerInvariant() -or $state.engineHash -ne 'unchanged') { throw 'Ownership update failed' }
'PASS: hotfix replaces verified launcher and updates ownership only'
Apply
'PASS: repeated installation is idempotent'
Apply $true
if((Get-FileHash (Join-Path $private 'RemasteredCE_Launcher.exe')).Hash -ne $originalHash -or (Get-FileHash $record).Hash -ne $recordHash) { throw 'Restore failed' }
if(Test-Path (Join-Path $private 'RemasteredCE_Launcher.exe.config')) { throw 'Restore left a newly introduced config' }
'PASS: restore returns original executable and exact state bytes'
$stateLock = [IO.File]::Open($record,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
try {
    $ErrorActionPreference = 'Continue'
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $hotfix 'Apply-Launcher-Fix.ps1') -GameFolder $game 2>&1 | Out-String | Write-Output
    $ErrorActionPreference = 'Stop'
    if($LASTEXITCODE -eq 0) { throw 'Failure injection did not fail' }
} finally { $stateLock.Dispose() }
if((Get-FileHash (Join-Path $private 'RemasteredCE_Launcher.exe')).Hash -ne $originalHash -or (Get-FileHash $record).Hash -ne $recordHash) { throw 'Rollback failed' }
'PASS: state replacement failure rolls launcher back to original'
[IO.File]::AppendAllText((Join-Path $private 'RemasteredCE_Launcher.exe'),'edited')
$ErrorActionPreference = 'Continue'
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $hotfix 'Apply-Launcher-Fix.ps1') -GameFolder $game 2>&1 | Out-String | Write-Output
$ErrorActionPreference = 'Stop'
if($LASTEXITCODE -eq 0) { throw 'Edited launcher was accepted' }
'PASS: edited installed launcher is protected before replacement'
