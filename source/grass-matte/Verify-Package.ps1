$ErrorActionPreference='Stop'
$env:TEMP='F:/Codex/Temp';$env:TMP=$env:TEMP
$w='F:/Codex/Remastered-CE-Port/work/grass-matte';$b='F:/Codex/Remastered-CE-Port/work/release-070'
[Reflection.Assembly]::LoadFrom("$b/setup/RemasteredCE_Setup.exe")|Out-Null
$r=[RemasteredCE.Release]::Load($null)
try{
 & 'C:/Program Files/Microsoft Visual Studio/18/Community/MSBuild/Current/Bin/Roslyn/csc.exe' /nologo /target:library "/reference:$b/setup/RemasteredCE_Setup.exe" "/out:$w/GrassFixture.dll" "$w/GrassFixture.cs"
 if($LASTEXITCODE -ne 0){throw 'Fixture compile failed'}
 [Reflection.Assembly]::LoadFrom("$w/GrassFixture.dll")|Out-Null
 [GrassFixture]::Select($r) # Schema-1 fixture avoids hardlinking unrelated vanilla assets into this two-pack verification.
 $r.Manifest['schema']=1
 $e=New-Object RemasteredCE.Engine
 $e.Build($r,'D:/SteamLibrary/steamapps/common/Shogun 2 Complete Edition','C:/Program Files (x86)/Steam/steamapps/common/Total War SHOGUN 2',"$b/acceptance")
 $shader=[RemasteredCE.Engine]::FileHash("$b/acceptance/data/shaders.pack")
 $overlay=[RemasteredCE.Engine]::FileHash("$b/acceptance/data/rce_campaign_night_visuals.pack")
 if($shader -ne [RemasteredCE.Engine]::FileHash("$w/shaders.candidate.pack")){throw 'Shader reconstruction differs'}
 if($overlay -ne [RemasteredCE.Engine]::FileHash("$w/rce_campaign_night_visuals.candidate.pack")){throw 'Overlay reconstruction differs'}
 $engine=[RemasteredCE.Engine]::FileHash("$b/acceptance/CE.dll")
 if($engine -ne [RemasteredCE.Engine]::FileHash('D:/SteamLibrary/steamapps/common/Shogun 2 Complete Edition/RemasteredCE/CE.dll')){throw 'Existing engine must remain identical'}
 @{status='PASS';version='0.1.70-preview';packageSha256=$r.PackageHash;shaderPackSha256=$shader;overlayPackSha256=$overlay;engineSha256=$engine;actualSignedSetupBuild=$true;signedRecipesReconstructed=2;fixtureOmitsUnchangedPacksAndBaseHardlinks=$true;candidatePacksMatch=$true;engineUnchanged=$true}|ConvertTo-Json|Set-Content "$b/reconstruction.json"
 'PASS: actual signed setup reconstructs both exact candidate archives and unchanged engine'
}finally{$r.Dispose()}
