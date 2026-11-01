$ErrorActionPreference='Stop'
$env:TEMP='F:\Codex\Temp';$env:TMP=$env:TEMP
$env:DOTNET_CLI_HOME='F:\Codex\Temp\dotnet-home'
$env:NUGET_PACKAGES='F:\Codex\Temp\nuget-packages'
$env:NUGET_HTTP_CACHE_PATH='F:\Codex\Temp\nuget-http'
$env:DOTNET_NOLOGO='1';$env:DOTNET_SKIP_FIRST_TIME_EXPERIENCE='1'
$env:DOTNET_GENERATE_ASPNET_CERTIFICATE='false';$env:DOTNET_CLI_TELEMETRY_OPTOUT='1'
& 'F:\Codex\RuntimeCache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B 'F:/Codex/Remastered-CE-Port/source/build_current_installer.py' 'F:/Codex/Remastered-CE-Port/work/particle-dynres-controller/candidate-installer.json'
if($LASTEXITCODE -ne 0){throw 'Current installer build failed'}
