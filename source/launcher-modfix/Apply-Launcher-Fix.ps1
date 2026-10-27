param([string]$GameFolder, [switch]$Restore)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$manifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'hotfix.json') -Raw | ConvertFrom-Json
function Hash($path) { return (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() }
function NoLinks($path) {
    $entry = New-Object IO.DirectoryInfo([IO.Path]::GetFullPath($path))
    while($null -ne $entry) {
        if($entry.Exists -and ($entry.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw "Linked folders are not supported: $($entry.FullName)" }
        $entry = $entry.Parent
    }
}
function CheckFile($path) {
    if((Test-Path -LiteralPath $path) -and ((Get-Item -LiteralPath $path).Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw "Linked files are not supported: $path" }
}
function AtomicCopy($source, $target) {
    CheckFile $target
    $temp = $target + '.modfix-' + [Guid]::NewGuid().ToString('N')
    try {
        [IO.File]::Copy($source,$temp,$false)
        if([IO.File]::Exists($target)) { [IO.File]::Replace($temp,$target,[NullString]::Value) }
        else { [IO.File]::Move($temp,$target) }
    } finally {
        if([IO.File]::Exists($temp)) { [IO.File]::Delete($temp) }
    }
}
if(!$GameFolder) {
    Add-Type -AssemblyName System.Windows.Forms
    $dialog = New-Object Windows.Forms.FolderBrowserDialog
    $dialog.Description = 'Select the Complete Edition game folder containing shogun2_complete_edition.exe (not its RemasteredCE subfolder).'
    if($dialog.ShowDialog() -ne [Windows.Forms.DialogResult]::OK) { exit 0 }
    $GameFolder = $dialog.SelectedPath
    $dialog.Dispose()
}
$GameFolder = [IO.Path]::GetFullPath($GameFolder).TrimEnd('\')
NoLinks $GameFolder
if(!(Test-Path -LiteralPath (Join-Path $GameFolder 'shogun2_complete_edition.exe') -PathType Leaf)) { throw 'Select the Complete Edition game folder.' }
$running = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -in @('shogun2_complete_edition','RemasteredCE_Bootstrap','Launch_Remastered_CE','RemasteredCE_Launcher','RemasteredCE_Setup') })
if($running.Count) { throw 'Close the game and all Remastered CE launcher/setup windows, then try again.' }
$managed = Join-Path $GameFolder 'RemasteredCE'
NoLinks $managed
$target = Join-Path $managed 'RemasteredCE_Launcher.exe'
$config = $target + '.config'
$record = Join-Path $managed 'install-state.json'
foreach($path in @($target,$config,$record)) { CheckFile $path }
if(!(Test-Path -LiteralPath $target -PathType Leaf) -or !(Test-Path -LiteralPath $record -PathType Leaf)) { throw 'A complete 0.1.25 Remastered CE installation is required.' }
$lockPath = Join-Path $GameFolder '.remastered-install.lock'
CheckFile $lockPath
$installationLock = [IO.File]::Open($lockPath,[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
try {
    $state = Get-Content -LiteralPath $record -Raw | ConvertFrom-Json
    if($state.version -ne $manifest.supportedVersion) { throw "This hotfix supports $($manifest.supportedVersion) only. Installed: $($state.version)" }
    $currentHash = Hash $target
    if($state.unifiedLauncherSha256 -ne $currentHash) { throw 'The installed launcher differs from its ownership record. Nothing was replaced.' }
    $backupPrefix = 'RemasteredCE.launcher-modfix-backup-'
    if($Restore) {
        if($currentHash -ne $manifest.hotfixSha256) { throw 'This hotfix is not currently installed. Nothing was replaced.' }
        $backup = @(Get-ChildItem -LiteralPath $GameFolder -Directory | Where-Object Name -Like "$backupPrefix*" | Sort-Object Name -Descending | Where-Object {
            (Test-Path -LiteralPath (Join-Path $_.FullName 'backup.json')) -and
            (Test-Path -LiteralPath (Join-Path $_.FullName 'RemasteredCE_Launcher.exe')) -and
            (Test-Path -LiteralPath (Join-Path $_.FullName 'install-state.json'))
        }) | Select-Object -First 1
        if(!$backup) { throw 'The original launcher backup was not found.' }
        NoLinks $backup.FullName
        $backupMeta = Get-Content -LiteralPath (Join-Path $backup.FullName 'backup.json') -Raw | ConvertFrom-Json
        if($backupMeta.gameFolder -ne $GameFolder -or (Hash (Join-Path $backup.FullName 'RemasteredCE_Launcher.exe')) -ne $manifest.originalSha256 -or (Hash (Join-Path $backup.FullName 'install-state.json')) -ne $backupMeta.stateSha256) { throw 'The backup did not pass verification.' }
        $source = Join-Path $backup.FullName 'RemasteredCE_Launcher.exe'
        $stateSource = Join-Path $backup.FullName 'install-state.json'
        $configSource = Join-Path $backup.FullName 'RemasteredCE_Launcher.exe.config'
        $expectedHash = $manifest.originalSha256
    } else {
        if($currentHash -eq $manifest.hotfixSha256) { Write-Output 'The launcher fix is already installed.'; exit 0 }
        if($currentHash -ne $manifest.originalSha256) { throw 'This is not the verified original 0.1.25 launcher. Nothing was replaced.' }
        $source = Join-Path $PSScriptRoot 'RemasteredCE_Launcher.exe'
        $configSource = $source + '.config'
        if((Hash $source) -ne $manifest.hotfixSha256 -or (Hash $configSource) -ne $manifest.configSha256) { throw 'The hotfix files failed hash verification. Extract the full ZIP again.' }
        $backup = New-Item -ItemType Directory -Path (Join-Path $GameFolder ($backupPrefix + [DateTime]::UtcNow.ToString('yyyyMMddHHmmss') + '-' + [Guid]::NewGuid().ToString('N').Substring(0,8)))
        [IO.File]::Copy($target,(Join-Path $backup.FullName 'RemasteredCE_Launcher.exe'))
        [IO.File]::Copy($record,(Join-Path $backup.FullName 'install-state.json'))
        if([IO.File]::Exists($config)) { [IO.File]::Copy($config,(Join-Path $backup.FullName 'RemasteredCE_Launcher.exe.config')) }
        $backupMeta = [ordered]@{gameFolder=$GameFolder;stateSha256=(Hash $record);hadConfig=[IO.File]::Exists($config)}
        $backupMeta | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $backup.FullName 'backup.json') -Encoding UTF8
        $state.unifiedLauncherSha256 = $manifest.hotfixSha256
        $stateSource = Join-Path $backup.FullName 'hotfix-state.json'
        $state | ConvertTo-Json -Depth 64 | Set-Content -LiteralPath $stateSource -Encoding UTF8
        $expectedHash = $manifest.hotfixSha256
    }
    # Retain the pre-operation pair so any partial replacement can roll back.
    $transaction = Join-Path $backup.FullName ('transaction-' + [Guid]::NewGuid().ToString('N'))
    [IO.Directory]::CreateDirectory($transaction) | Out-Null
    [IO.File]::Copy($target,(Join-Path $transaction 'launcher.exe'))
    [IO.File]::Copy($record,(Join-Path $transaction 'state.json'))
    $hadConfig = [IO.File]::Exists($config)
    if($hadConfig) { [IO.File]::Copy($config,(Join-Path $transaction 'launcher.config')) }
    try {
        AtomicCopy $source $target
        if(Test-Path -LiteralPath $configSource -PathType Leaf) { AtomicCopy $configSource $config }
        elseif($Restore -and !$backupMeta.hadConfig -and [IO.File]::Exists($config)) { [IO.File]::Delete($config) }
        AtomicCopy $stateSource $record
        if((Hash $target) -ne $expectedHash) { throw 'Installed launcher verification failed.' }
    } catch {
        $failure = $_
        try {
            if((Hash $target) -ne (Hash (Join-Path $transaction 'launcher.exe'))) { AtomicCopy (Join-Path $transaction 'launcher.exe') $target }
            if((Hash $record) -ne (Hash (Join-Path $transaction 'state.json'))) { AtomicCopy (Join-Path $transaction 'state.json') $record }
            if($hadConfig) { AtomicCopy (Join-Path $transaction 'launcher.config') $config }
            elseif([IO.File]::Exists($config)) { [IO.File]::Delete($config) }
        } catch { throw "Replacement failed and rollback needs attention. Retained files: $transaction. $($_.Exception.Message)" }
        throw $failure
    }
    if($Restore) { Write-Output 'Original launcher and ownership record restored.' }
    else { Write-Output "Launcher fix installed. Original files backed up in $($backup.FullName). Open Launch_Remastered_CE.exe as usual." }
} finally { $installationLock.Dispose() }
