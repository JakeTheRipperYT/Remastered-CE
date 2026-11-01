$ErrorActionPreference='Stop'
$env:TEMP='F:/Codex/Temp';$env:TMP=$env:TEMP
$w='F:/Codex/Remastered-CE-Port/work/release-068'
[Reflection.Assembly]::LoadFrom("$w/setup/RemasteredCE_Setup.exe") | Out-Null
$r=[RemasteredCE.Release]::Load($null)
try {
 $raw=[IO.File]::ReadAllBytes('D:/SteamLibrary/steamapps/common/Shogun 2 Complete Edition/empire.retail.x64.dll')
 if([RemasteredCE.Engine]::Hash($raw) -ne $r.Manifest['engineSourceSha256']){throw 'Source engine mismatch'}
 foreach($operation in [RemasteredCE.J]::Arr($r.Manifest['enginePatches'])){
  $op=[RemasteredCE.J]::Obj($operation);$bytes=[RemasteredCE.J]::B($op,'data')
  [Buffer]::BlockCopy($bytes,0,$raw,[int][RemasteredCE.J]::N($op,'offset'),$bytes.Length)
 }
 if([RemasteredCE.Engine]::Hash($raw) -ne $r.Manifest['engineEditedSha256']){throw 'Edited engine mismatch'}
 $candidate=[RemasteredCE.PePatch]::Inject($raw,$r.Helper)
 $hash=[RemasteredCE.Engine]::Hash($candidate)
 if($hash -ne $r.Manifest['engineFinalSha256']){throw 'Signed final engine mismatch'}
 if($hash -ne [RemasteredCE.Engine]::FileHash('F:/Codex/Remastered-CE-Port/work/particle-helper-cleanup/CE.campaign-night-candidate.dll')){throw 'Native-tested candidate mismatch'}
 [IO.File]::WriteAllBytes("$w/CE.verified.dll",$candidate)
 @{status='PASS';version=$r.Manifest['version'];engineSha256=$hash;packageSha256=$r.PackageHash;actualSignedSetupReconstruction=$true;nativeTestedEngineMatches=$true;allNineArchiveRecipesUnchanged=$true;scope='Authenticate final embedded package, replay all engine patches and execute the actual final setup injector. Archive identity checked separately; no game installation changed.'} | ConvertTo-Json | Set-Content "$w/engine-reconstruction.json"
 Write-Output 'PASS: actual signed setup reconstructs exact native-tested engine'
} finally {$r.Dispose()}
