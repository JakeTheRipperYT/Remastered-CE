param([string]$WorkDirectory = "$PSScriptRoot/_build")
$ErrorActionPreference = 'Stop'
$WorkDirectory = [IO.Path]::GetFullPath($WorkDirectory)
New-Item -ItemType Directory -Force $WorkDirectory | Out-Null
function Run($program, [string[]]$arguments) {
    & $program @arguments
    if($LASTEXITCODE -ne 0) { throw "$program failed with exit code $LASTEXITCODE" }
}
$zipPath = Join-Path $WorkDirectory 'original-installer.zip'
if(!(Test-Path -LiteralPath $zipPath)) {
    Invoke-WebRequest 'https://github.com/JakeTheRipperYT/Remastered-CE/releases/download/v0.1.25-preview/RemasteredCE-0.1.25-original-build-input.zip' -OutFile $zipPath
}
if((Get-FileHash -LiteralPath $zipPath).Hash.ToLowerInvariant() -ne '2920f295cd764837787b2308d7fb2a1803538ec1d87cf8b6f1c8f35f8012d1de') { throw 'Original release hash mismatch.' }
$installer = Join-Path $WorkDirectory 'original-installer'
if(!(Test-Path -LiteralPath $installer)) { Expand-Archive -LiteralPath $zipPath -DestinationPath $installer }
$tools = Join-Path $WorkDirectory 'tools'
$shim = @(Get-ChildItem -Path "$tools/ilspycmd.*" -ErrorAction SilentlyContinue | Where-Object Extension -In @('.exe','.cmd')) | Select-Object -First 1
if(!$shim) {
    Run 'dotnet' @('tool','install','ilspycmd','--version','11.2.0.10050','--tool-path',$tools)
    $shim = Get-ChildItem -Path "$tools/ilspycmd.*" | Where-Object Extension -In @('.exe','.cmd') | Select-Object -First 1
}
$source = Join-Path $WorkDirectory 'recovered-source'
if(Test-Path -LiteralPath $source) { throw 'Recovered source already exists. Use a new WorkDirectory for a fresh build.' }
Run $shim.FullName @('-p','-o',$source,(Join-Path $installer 'RemasteredCE_Setup.exe'))
# Normalize only text sources; signed binary resources stay byte-identical.
$utf8 = New-Object Text.UTF8Encoding($false)
$textFiles = @(Get-ChildItem -LiteralPath $source -Recurse -Filter '*.cs') + @(Get-ChildItem -LiteralPath $source -Filter '*.csproj')
foreach($file in $textFiles) { [IO.File]::WriteAllText($file.FullName,[IO.File]::ReadAllText($file.FullName).Replace("`r`n","`n"),$utf8) }
Run 'git' @('-C',$source,'init','--quiet')
Run 'git' @('-C',$source,'apply','--check',(Join-Path $PSScriptRoot 'launcher-modfix.patch'))
Run 'git' @('-C',$source,'apply',(Join-Path $PSScriptRoot 'launcher-modfix.patch'))
Run 'git' @('-C',$source,'apply','--check',(Join-Path $PSScriptRoot 'installer-integration.patch'))
Run 'git' @('-C',$source,'apply',(Join-Path $PSScriptRoot 'installer-integration.patch'))
$compiled = Join-Path $WorkDirectory 'compiled'
Run 'dotnet' @('build',(Join-Path $source 'RemasteredCE_Setup.csproj'),'-c','Release','-o',$compiled)
$executable = Join-Path $compiled 'RemasteredCE_Launcher.exe'
Run 'powershell.exe' @('-NoProfile','-ExecutionPolicy','Bypass','-File',(Join-Path $PSScriptRoot 'Test-Launcher.ps1'),'-Executable',$executable)
Run 'powershell.exe' @('-NoProfile','-ExecutionPolicy','Bypass','-File',(Join-Path $PSScriptRoot 'Test-Installer-Integration.ps1'),'-Executable',$executable)
$testLog = Join-Path $WorkDirectory 'builtin-selftest.txt'
$process = Start-Process -FilePath $executable -ArgumentList '--self-test',('"' + $testLog + '"') -WindowStyle Hidden -Wait -PassThru
if($process.ExitCode -ne 0) { throw 'Built-in self-tests failed.' }
$hotfix = Join-Path $WorkDirectory 'hotfix'
New-Item -ItemType Directory -Force $hotfix | Out-Null
Copy-Item -LiteralPath $executable -Destination $hotfix
Copy-Item -LiteralPath ($executable + '.config') -Destination $hotfix
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'Apply-Launcher-Fix.ps1') -Destination $hotfix
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'HOTFIX-README.txt') -Destination (Join-Path $hotfix 'README.txt')
[ordered]@{
    supportedVersion='0.1.25-preview'
    originalSha256='ff77839ebb0495bb7e0906364aa078ae882d593eeb03abd60a2bed4ee89f023e'
    hotfixSha256=(Get-FileHash -LiteralPath $executable).Hash.ToLowerInvariant()
    configSha256=(Get-FileHash -LiteralPath ($executable + '.config')).Hash.ToLowerInvariant()
} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $hotfix 'hotfix.json') -Encoding UTF8
$cmdTemplate = '@echo off' + "`r`n" + 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Apply-Launcher-Fix.ps1" {0}' + "`r`n" + 'pause' + "`r`n"
[IO.File]::WriteAllText((Join-Path $hotfix 'Apply Launcher Fix.cmd'),($cmdTemplate -f ''),[Text.Encoding]::ASCII)
[IO.File]::WriteAllText((Join-Path $hotfix 'Restore Original Launcher.cmd'),($cmdTemplate -f '-Restore'),[Text.Encoding]::ASCII)
# Extract the pinned original manager for isolated deployment/rollback fixtures.
Add-Type -AssemblyName System.IO.Compression
$package = [IO.File]::ReadAllBytes((Join-Path $source 'release'))
$signatureLength = [BitConverter]::ToInt32($package,8)
$stream = New-Object IO.MemoryStream(,$package[(12+$signatureLength)..($package.Length-1)])
$archive = New-Object IO.Compression.ZipArchive($stream,[IO.Compression.ZipArchiveMode]::Read)
$entry = $archive.GetEntry('mod-manager.exe').Open()
$original = [IO.File]::Create((Join-Path $WorkDirectory 'original-manager.exe'))
try { $entry.CopyTo($original) } finally { $original.Dispose(); $entry.Dispose(); $archive.Dispose(); $stream.Dispose() }
Run 'powershell.exe' @('-NoProfile','-ExecutionPolicy','Bypass','-File',(Join-Path $PSScriptRoot 'Test-Deployment.ps1'),'-BuildRoot',$WorkDirectory)
$output = Join-Path $WorkDirectory 'RemasteredCE-0.1.25-Launcher-Mod-Fix.zip'
Compress-Archive -Path "$hotfix/*" -DestinationPath $output -Force
Write-Output "Created tested hotfix: $output"
$installerOutput = Join-Path $WorkDirectory 'integrated-installer'
New-Item -ItemType Directory -Force $installerOutput | Out-Null
Copy-Item -LiteralPath $executable -Destination (Join-Path $installerOutput 'RemasteredCE_Setup.exe')
Copy-Item -LiteralPath ($executable + '.config') -Destination (Join-Path $installerOutput 'RemasteredCE_Setup.exe.config')
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'INSTALLER-README.txt') -Destination (Join-Path $installerOutput 'README.txt')
$installerZip = Join-Path $WorkDirectory 'RemasteredCE_Installer_Preview.zip'
Compress-Archive -Path "$installerOutput/*" -DestinationPath $installerZip -Force
Write-Output "Created integrated installer: $installerZip"
