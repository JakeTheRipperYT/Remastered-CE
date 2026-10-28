param([string]$WorkDirectory="$PSScriptRoot/_build-028",[string]$PackagePath="")
$ErrorActionPreference='Stop'
$WorkDirectory=[IO.Path]::GetFullPath($WorkDirectory)
New-Item -ItemType Directory -Force $WorkDirectory | Out-Null
$env:TEMP=Join-Path $WorkDirectory 'temp';$env:TMP=$env:TEMP
$env:DOTNET_CLI_HOME=Join-Path $WorkDirectory 'dotnet-home'
$env:NUGET_PACKAGES=Join-Path $WorkDirectory 'nuget-packages'
$env:NUGET_HTTP_CACHE_PATH=Join-Path $WorkDirectory 'nuget-http'
$env:DOTNET_NOLOGO='1';$env:DOTNET_SKIP_FIRST_TIME_EXPERIENCE='1';$env:DOTNET_GENERATE_ASPNET_CERTIFICATE='false';$env:DOTNET_CLI_TELEMETRY_OPTOUT='1'
New-Item -ItemType Directory -Force $env:TEMP | Out-Null
function Run($program,[string[]]$arguments){& $program @arguments;if($LASTEXITCODE -ne 0){throw "$program failed: $LASTEXITCODE"}}
if(((& dotnet --version | Select-Object -Last 1).Trim()) -ne '10.0.401'){throw 'Use the pinned .NET SDK 10.0.401 for byte-identical builds.'}
$zip=Join-Path $WorkDirectory 'original-installer.zip'
if(!(Test-Path -LiteralPath $zip)){Invoke-WebRequest 'https://github.com/JakeTheRipperYT/Remastered-CE/releases/download/v0.1.25-preview/RemasteredCE-0.1.25-original-build-input.zip' -OutFile $zip}
if((Get-FileHash -LiteralPath $zip).Hash.ToLowerInvariant() -ne '2920f295cd764837787b2308d7fb2a1803538ec1d87cf8b6f1c8f35f8012d1de'){throw 'Original build input hash mismatch'}
$original=Join-Path $WorkDirectory 'original-installer'
if(!(Test-Path -LiteralPath $original)){Expand-Archive -LiteralPath $zip -DestinationPath $original}
$tools=Join-Path $WorkDirectory 'tools';$shim=@(Get-ChildItem -Path "$tools/ilspycmd.*" -ErrorAction SilentlyContinue | Where-Object Extension -In @('.exe','.cmd')) | Select-Object -First 1
if(!$shim){
 Run 'dotnet' @('tool','install','ilspycmd','--version','11.2.0.10050','--tool-path',$tools)
 $shim=@(Get-ChildItem -Path "$tools/ilspycmd.*" | Where-Object Extension -In @('.exe','.cmd')) | Select-Object -First 1
}
$source=Join-Path $WorkDirectory 'source'
if(Test-Path -LiteralPath $source){throw 'Source already exists; choose a fresh WorkDirectory'}
Run $shim.FullName @('-p','-o',$source,(Join-Path $original 'RemasteredCE_Setup.exe'))
$utf8=[Text.UTF8Encoding]::new($false)
foreach($p in @((Get-ChildItem -LiteralPath $source -Recurse -Filter '*.cs'))+@((Get-ChildItem -LiteralPath $source -Filter '*.csproj'))){[IO.File]::WriteAllText($p.FullName,[IO.File]::ReadAllText($p.FullName).Replace("`r`n","`n"),$utf8)}
Run 'git' @('-C',$source,'init','--quiet')
foreach($patch in @('launcher-modfix.patch','installer-integration.patch','release-028.patch')){
 Run 'git' @('-C',$source,'apply','--check',(Join-Path $PSScriptRoot $patch))
 Run 'git' @('-C',$source,'apply',(Join-Path $PSScriptRoot $patch))
}
$lean=Join-Path $WorkDirectory 'lean'
Run 'dotnet' @('build',(Join-Path $source 'RemasteredCE_Setup.csproj'),'-c','Release','-o',$lean,'-p:IncludeRelease=false')
$gui=Join-Path $lean 'RemasteredCE_Launcher.exe'
if((Get-FileHash -LiteralPath $gui).Hash.ToLowerInvariant() -ne 'f08687c9c73f471b30360b46f5a35ff32ae11cf6eac5b723b3c7b7623a0ad5dc'){throw 'Lean GUI differs; check pinned compiler and framework targeting pack'}
if(!$PackagePath){$PackagePath=Join-Path $WorkDirectory 'RemasteredCE-0.1.28-preview.rce';Invoke-WebRequest 'https://github.com/JakeTheRipperYT/Remastered-CE/releases/download/v0.1.28-preview/RemasteredCE-0.1.28-preview.rce' -OutFile $PackagePath}
$PackagePath=[IO.Path]::GetFullPath($PackagePath)
if((Get-FileHash -LiteralPath $PackagePath).Hash.ToLowerInvariant() -ne 'da44d366cc3e0f96d1ff6c12b5a0c21abb48b6152eaf01ccddc4b2dd005ad752'){throw 'Signed v28 package hash mismatch'}
[Reflection.Assembly]::LoadFrom($gui) | Out-Null
$release=[RemasteredCE.Release]::Load($PackagePath)
try{if([RemasteredCE.Engine]::Hash($release.ModManager) -ne [RemasteredCE.Engine]::FileHash($gui)){throw 'Authenticated package does not contain the reproduced GUI'}}finally{$release.Dispose()}
Copy-Item -LiteralPath $PackagePath -Destination (Join-Path $source 'release')
$setup=Join-Path $WorkDirectory 'setup'
Run 'dotnet' @('build',(Join-Path $source 'RemasteredCE_Setup.csproj'),'-c','Release','-o',$setup,'-p:IncludeRelease=true','-p:AssemblyName=RemasteredCE_Setup')
$exe=Join-Path $setup 'RemasteredCE_Setup.exe'
if((Get-FileHash -LiteralPath $exe).Hash.ToLowerInvariant() -ne '260bec731cc26a768d6f96ae8fa960d6dc2111f49188fcd49d79f5e6dc65d07b'){throw 'Setup differs from verified release build'}
Run 'powershell.exe' @('-NoProfile','-ExecutionPolicy','Bypass','-File',(Join-Path $PSScriptRoot 'Test-Launcher.ps1'),'-Executable',$exe)
Run 'powershell.exe' @('-NoProfile','-ExecutionPolicy','Bypass','-File',(Join-Path $PSScriptRoot 'Test-New-Release.ps1'),'-Executable',$exe,'-ExpectedGui',$gui,'-Package',$PackagePath)
$log=Join-Path $WorkDirectory 'setup-selftests.txt';$p=Start-Process -FilePath $exe -ArgumentList '--self-test',('"'+$log+'"') -WindowStyle Hidden -Wait -PassThru
if($p.ExitCode -ne 0){throw 'Setup built-in self-tests failed'}
Write-Output "Reproduced and tested release: $exe"
