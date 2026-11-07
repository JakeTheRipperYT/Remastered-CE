param([Parameter(Mandatory=$true)][string]$WorkDirectory,[Parameter(Mandatory=$true)][string]$Package)
$ErrorActionPreference='Stop'
$env:DOTNET_NOLOGO='1';$env:DOTNET_SKIP_FIRST_TIME_EXPERIENCE='1'
$env:DOTNET_GENERATE_ASPNET_CERTIFICATE='false';$env:DOTNET_CLI_TELEMETRY_OPTOUT='1'
$work=[IO.Path]::GetFullPath($WorkDirectory)
if(Test-Path -LiteralPath $work){throw 'Use a new work directory.'}
[IO.Directory]::CreateDirectory($work)|Out-Null
$env:TEMP=Join-Path $work 'Temp';$env:TMP=$env:TEMP
$env:DOTNET_CLI_HOME=Join-Path $work 'dotnet-home';$env:NUGET_PACKAGES=Join-Path $work 'packages'
[IO.Directory]::CreateDirectory($env:TEMP)|Out-Null
Add-Type -AssemblyName System.Web.Extensions
$json=New-Object Web.Script.Serialization.JavaScriptSerializer
$meta=$json.DeserializeObject([IO.File]::ReadAllText((Join-Path $PSScriptRoot 'release-build.json')))
function AssertHash($path,$expected){if((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected){throw ('Hash mismatch: '+$path)}}
$Package=[IO.Path]::GetFullPath($Package);AssertHash $Package $meta.packageSha256
$src=Join-Path $work 'source';[IO.Directory]::CreateDirectory($src)|Out-Null
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'RemasteredCE'),(Join-Path $PSScriptRoot 'Properties') -Destination $src -Recurse
foreach($name in 'RemasteredCE_Setup.csproj','app.config','app.ico','app.manifest','lz4','publicKey'){Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination $src}
$project=Join-Path $src 'RemasteredCE_Setup.csproj';$lean=Join-Path $work 'lean';$setup=Join-Path $work 'setup'
& dotnet build $project -c Release -o $lean -p:IncludeRelease=false -p:AssemblyName=RemasteredCE_Launcher --nologo -v:q
if($LASTEXITCODE -ne 0){throw 'Lean launcher build failed'}
$gui=Join-Path $lean 'RemasteredCE_Launcher.exe';AssertHash $gui $meta.launcherSha256
[Reflection.Assembly]::LoadFrom($gui)|Out-Null
$r=[RemasteredCE.Release]::Load($Package)
try{if([RemasteredCE.J]::S($r.Manifest,'version') -ne $meta.version){throw 'Wrong signed release version'}}finally{$r.Dispose()}
Copy-Item -LiteralPath $Package -Destination (Join-Path $src 'release')
& dotnet build $project -c Release -o $setup -p:IncludeRelease=true -p:AssemblyName=RemasteredCE_Setup --nologo -v:q
if($LASTEXITCODE -ne 0){throw 'Setup build failed'}
$exe=Join-Path $setup 'RemasteredCE_Setup.exe';AssertHash $exe $meta.setupSha256
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'Test-New-Release.ps1') -Executable $exe -ExpectedGui $gui -Package $Package -TestRoot $work
if($LASTEXITCODE -ne 0){throw 'Installer integration checks failed'}
$out=Join-Path $work 'output';[IO.Directory]::CreateDirectory($out)|Out-Null
Copy-Item -LiteralPath $exe,(Join-Path $setup 'RemasteredCE_Setup.exe.config'),$gui,$Package -Destination $out
foreach($name in 'README.txt','CHANGELOG.md'){Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination $out}
Write-Output ('PASS: exact signed package, lean launcher and setup reproduced; outputs: '+$out)
