param([Parameter(Mandatory=$true)][string]$Executable,[Parameter(Mandatory=$true)][string]$ExpectedGui,[Parameter(Mandatory=$true)][string]$Package)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Web.Extensions
$exe=[IO.Path]::GetFullPath($Executable)
[Reflection.Assembly]::LoadFrom($exe) | Out-Null
$root=Join-Path ([IO.Path]::GetTempPath()) ('RCE-new-package-fixture-'+[Guid]::NewGuid().ToString('N').Substring(0,8))
[IO.Directory]::CreateDirectory($root) | Out-Null
$script:passed=0
function Assert($ok,$message){if(!$ok){throw $message};$script:passed++;Write-Output ('PASS: '+$message)}
$r=[RemasteredCE.Release]::Load($null)
try{
 Assert ([RemasteredCE.J]::S($r.Manifest,'version') -eq '0.1.28-preview') 'Final setup embeds v28 release'
 Assert ([RemasteredCE.J]::S($r.Manifest,'minimumInstallerVersion') -eq '0.1.28-preview') 'New package requires corrected v28 installer'
 Assert ($r.PackageHash -eq [RemasteredCE.Engine]::FileHash($Package)) 'Embedded signature and package match final release asset'
 Assert ([RemasteredCE.Engine]::Hash($r.ModManager) -eq [RemasteredCE.Engine]::FileHash($ExpectedGui)) 'Signed package embeds corrected lean GUI exactly'
 Assert ([RemasteredCE.Engine]::Hash([RemasteredCE.InstallerLauncher]::Select($r)) -eq [RemasteredCE.Engine]::FileHash($ExpectedGui)) 'v28 uses authenticated GUI payload instead of executing setup'
 Assert ([RemasteredCE.Engine]::FileHash($exe) -ne [RemasteredCE.Engine]::FileHash($ExpectedGui)) 'Setup and lean GUI are distinct, avoiding recursively embedded packages'
 $state=New-Object 'Collections.Generic.Dictionary[string,object]'
 [RemasteredCE.InstallerLauncher]::Stage($r,$root,$state)
 $installed=Join-Path $root 'RemasteredCE_Launcher.exe'
 Assert ([RemasteredCE.Engine]::FileHash($installed) -eq [RemasteredCE.Engine]::FileHash($ExpectedGui)) 'Actual staging installs exact signed fixed GUI'
 Assert ($state['unifiedLauncherSha256'] -eq [RemasteredCE.Engine]::FileHash($ExpectedGui)) 'Installed ownership records correct GUI hash'
 Assert ($state['offlineReleaseSha256'] -eq $r.PackageHash) 'Offline ownership records final package hash'
 Assert ([RemasteredCE.Engine]::FileHash((Join-Path $root 'release.rce')) -eq $r.PackageHash) 'Offline repair package is byte-identical'
 Assert (!(Test-Path -LiteralPath ($installed+'.config'))) 'Installed lean GUI starts without a sidecar config'
 $log=Join-Path $root 'staged-gui-selftests.txt'
 $p=Start-Process -FilePath $installed -ArgumentList '--self-test',('"'+$log+'"') -WindowStyle Hidden -Wait -PassThru
 Assert ($p.ExitCode -eq 0 -and (Test-Path -LiteralPath $log)) 'Fresh staged GUI built-in tests pass'
 $loaded=[RemasteredCE.Release]::Load((Join-Path $root 'release.rce'));try{Assert ($loaded.PackageHash -eq $r.PackageHash) 'Staged offline package reauthenticates'}finally{$loaded.Dispose()}
 Assert ([RemasteredCE.UnifiedLauncher]::ResolveGameHint([string[]]@(), '') -eq '') 'No detected game remains a valid startup state'
 Assert ([RemasteredCE.UnifiedLauncher]::ResolveGameHint([string[]]@('--game','','--'), '') -eq '') 'Empty cached game hint is accepted'
 Assert ([RemasteredCE.UnifiedLauncher]::ResolveGameHint([string[]]@('--game','','--'), 'D:\detected') -eq '') 'Explicit empty hint preserves manual selection'
 Assert ([RemasteredCE.UnifiedLauncher]::ResolveGameHint([string[]]@('--game','D:\Games\Complete Edition','--'), '') -eq 'D:\Games\Complete Edition') 'Paths with spaces remain intact'
 foreach($bad in @([string[]]@('--game'),[string[]]@('--game','--'))){$rejected=$false;try{[RemasteredCE.UnifiedLauncher]::ResolveGameHint($bad,'') | Out-Null}catch{$rejected=$true};Assert $rejected 'Missing argument remains rejected'}
 $result=@{status='PASS';checks=$script:passed;setupSha256=[RemasteredCE.Engine]::FileHash($exe);guiSha256=[RemasteredCE.Engine]::FileHash($ExpectedGui);packageSha256=$r.PackageHash;fixture=$root;scope='Actual new-package authentication, staging, offline repair ownership, staged GUI startup/selftests and empty-hint parser. No game started or installed files changed.'}
 $result | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $root 'new-package-integration.json') -Encoding utf8
 Write-Output ('Passed '+$script:passed+' v28 package integration checks. Fixture: '+$root)
}finally{$r.Dispose()}
