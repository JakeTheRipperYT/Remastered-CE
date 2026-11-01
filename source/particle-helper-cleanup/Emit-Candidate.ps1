$ErrorActionPreference='Stop'
$env:TEMP='F:/Codex/Temp';$env:TMP='F:/Codex/Temp'
$taskRoot=$PSScriptRoot
$launcher=(Resolve-Path -LiteralPath 'F:/Codex/Remastered-CE-Port/work/release-067/lean/RemasteredCE_Launcher.exe').ProviderPath
[void][Reflection.Assembly]::LoadFrom($launcher)
$compiler='C:/Program Files/Microsoft Visual Studio/18/Community/MSBuild/Current/Bin/Roslyn/csc.exe'
$library=Join-Path $taskRoot 'CandidateInjector.dll'
& $compiler /nologo /target:library "/reference:$launcher" "/out:$library" (Join-Path $taskRoot 'PePatchCandidate.cs')
if($LASTEXITCODE -ne 0){throw 'Candidate injector compilation failed.'}
[void][Reflection.Assembly]::LoadFrom($library)
$oldManifest=[RemasteredCE.J]::Parse([IO.File]::ReadAllText('F:/Codex/Remastered-CE-Port/work/release-067/manifest.json'))
$oldHelper=[RemasteredCE.J]::Parse([IO.File]::ReadAllText('F:/Codex/Remastered-CE-Port/work/release-067/helper.json'))
$old=[IO.File]::ReadAllBytes('D:/SteamLibrary/steamapps/common/Shogun 2 Complete Edition/empire.retail.x64.dll')
foreach($operation in [RemasteredCE.J]::Arr($oldManifest['enginePatches'])){
    $op=[RemasteredCE.J]::Obj($operation);$bytes=[RemasteredCE.J]::B($op,'data')
    [Buffer]::BlockCopy($bytes,0,$old,[int][RemasteredCE.J]::N($op,'offset'),$bytes.Length)
}
$control=[NightControllerCandidate.PePatch]::Inject($old,$oldHelper)
if([RemasteredCE.Engine]::Hash($control) -ne $oldManifest['engineFinalSha256']){throw 'Backward-compatible injector control mismatch.'}
$manifest=[RemasteredCE.J]::Parse([IO.File]::ReadAllText((Join-Path $taskRoot 'candidate-manifest.json')))
$helper=[RemasteredCE.J]::Parse([IO.File]::ReadAllText((Join-Path $taskRoot 'candidate-helper.json')))
$engine=[IO.File]::ReadAllBytes((Join-Path $taskRoot 'candidate-engine-edited.bin'))
if([RemasteredCE.Engine]::Hash($engine) -ne $manifest['engineEditedSha256']){throw 'Candidate edited engine mismatch.'}
$candidate=[NightControllerCandidate.PePatch]::Inject($engine,$helper)
$manifest['engineFinalSha256']=[RemasteredCE.Engine]::Hash($candidate)
[IO.File]::WriteAllBytes((Join-Path $taskRoot 'CE.campaign-night-candidate.dll'),$candidate)
[IO.File]::WriteAllText((Join-Path $taskRoot 'candidate-manifest.json'),[RemasteredCE.J]::Json().Serialize($manifest))
Write-Output ('Candidate emitted; existing32 compatibility control passed; hash '+$manifest['engineFinalSha256'])
