param([string]$Executable = "$PSScriptRoot/build-fixed/RemasteredCE_Setup.exe")
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Web.Extensions
Add-Type -AssemblyName System.Windows.Forms
[Reflection.Assembly]::LoadFrom([IO.Path]::GetFullPath($Executable)) | Out-Null
$testRoot = Join-Path ([IO.Path]::GetTempPath()) ('RCE-modfix-' + [Guid]::NewGuid().ToString('N').Substring(0,8))
[IO.Directory]::CreateDirectory($testRoot) | Out-Null
$script:passed = 0
function Assert($condition, $message) {
    if (!$condition) { throw $message }
    $script:passed++
    'PASS: ' + $message
}
function Pack($path, $format, $compressed, $timestamp, $type = 3, $badOffset = $false) {
    $aligned = $format -eq 'PFHs'
    $legacy = $format -eq 'PFH0'
    $names = @('db\units_tables\custom', 'script\campaign\mod.lua')
    $plain = [byte[]]([Text.Encoding]::UTF8.GetBytes(('example ' * 150)))
    $stored = if ($compressed) { [RemasteredCE.Lz4]::Encode($plain, 'fast', 0) } else { $plain }
    $index = New-Object IO.MemoryStream
    $iw = New-Object IO.BinaryWriter($index)
    $indexSize = 0
    foreach($name in $names) {
        $indexSize += 4 + [Text.Encoding]::UTF8.GetByteCount($name) + 1
        if($aligned) { $indexSize += 8 }
        if($compressed) { $indexSize += 4 }
        if($timestamp) { $indexSize += 8 }
    }
    $dataStart = 24 + $indexSize
    if(!$legacy) { $dataStart += 8 }
    if($aligned) { $dataStart = [int]([Math]::Ceiling($dataStart / 16.0) * 16) }
    $offset = $dataStart
    foreach($name in $names) {
        if($aligned) { $iw.Write([uint64]$(if($badOffset) { 1 } else { $offset })) }
        if($compressed) { $iw.Write([uint32]$plain.Length) }
        $iw.Write([uint32]$stored.Length)
        if($timestamp) { $iw.Write([uint64]133000000000000000) }
        $iw.Write([Text.Encoding]::UTF8.GetBytes($name + [char]0))
        $offset += $stored.Length
        if($aligned) { $offset = [int]([Math]::Ceiling($offset / 16.0) * 16) }
    }
    $iw.Flush()
    $writer = New-Object IO.BinaryWriter([IO.File]::Create($path))
    try {
        $writer.Write([Text.Encoding]::ASCII.GetBytes($format))
        $flags = $type
        if($compressed) { $flags = $flags -bor 0x20 }
        if($timestamp) { $flags = $flags -bor 0x40 }
        $writer.Write([uint32]$flags)
        $writer.Write([uint32]0); $writer.Write([uint32]0)
        $writer.Write([uint32]2); $writer.Write([uint32]$indexSize)
        if(!$legacy) { $writer.Write([uint64]133000000000000000) }
        $writer.Write($index.ToArray())
        foreach($name in $names) {
            if($aligned) { while($writer.BaseStream.Position % 16) { $writer.Write([byte]0) } }
            $writer.Write([byte[]]$stored)
        }
    } finally { $writer.Dispose(); $iw.Dispose(); $index.Dispose() }
}
foreach($format in @('PFH0','PFH2','PFH3','PFHs')) {
    foreach($compressed in @($false,$true)) {
        if($compressed -and $format -notin @('PFH3','PFHs')) { continue }
        foreach($timestamp in @($false,$true)) {
            if($timestamp -and $format -eq 'PFH0') { continue }
            $path = Join-Path $testRoot "$format-$compressed-$timestamp.pack"
            Pack $path $format $compressed $timestamp
            $result = [RemasteredCE.Mods]::ReadPack($path,'test',$false)
            Assert ($null -eq $result.Error -and $result.Files.Count -eq 2) "Read $format compressed=$compressed timestamps=$timestamp ($($result.Error))"
            $before = [RemasteredCE.Mods]::Hash($path)
            $result.Enabled = $true
            $packs = New-Object 'System.Collections.Generic.List[RemasteredCE.ModPack]'
            $packs.Add($result)
            $staged = [RemasteredCE.Mods]::Stage($packs, (Join-Path $testRoot "cache-$format-$compressed-$timestamp"), [Action[string]]{param($s)})
            Assert ([RemasteredCE.Mods]::Hash((Join-Path $staged $result.Name)) -eq $before) 'Staging preserves every pack byte'
        }
    }
}
$bad = Join-Path $testRoot 'bad-offset.pack'
Pack $bad 'PFHs' $true $false 3 $true
Assert ($null -ne [RemasteredCE.Mods]::ReadPack($bad,'test',$false).Error) 'Reject aligned data overlapping the header'
$truncated = Join-Path $testRoot 'truncated.pack'
[IO.File]::WriteAllBytes($truncated, [Text.Encoding]::ASCII.GetBytes('PFH3'))
Assert ($null -ne [RemasteredCE.Mods]::ReadPack($truncated,'test',$false).Error) 'Reject truncated header'
$badFlags = Join-Path $testRoot 'encrypted.pack'
Pack $badFlags 'PFH3' $false $false
$bytes = [IO.File]::ReadAllBytes($badFlags); $bytes[4] = $bytes[4] -bor 0x10; [IO.File]::WriteAllBytes($badFlags,$bytes)
Assert ($null -ne [RemasteredCE.Mods]::ReadPack($badFlags,'test',$false).Error) 'Continue rejecting unsupported encrypted payloads'
$bounds = Join-Path $testRoot 'bad-size.pack'
Pack $bounds 'PFH3' $true $false
$bytes = [IO.File]::ReadAllBytes($bounds); [Array]::Copy([BitConverter]::GetBytes([uint32]9999999),0,$bytes,36,4); [IO.File]::WriteAllBytes($bounds,$bytes)
Assert ($null -ne [RemasteredCE.Mods]::ReadPack($bounds,'test',$false).Error) 'Reject compressed stored size beyond EOF'
$game = Join-Path $testRoot 'game'
$privateData = Join-Path $game 'RemasteredCE/data'
$baseData = Join-Path $game 'data'
[IO.Directory]::CreateDirectory($privateData) | Out-Null
[IO.Directory]::CreateDirectory($baseData) | Out-Null
Pack (Join-Path $privateData 'private.pack') 'PFH3' $true $false
Pack (Join-Path $privateData 'data.pack') 'PFH3' $true $false
Pack (Join-Path $baseData 'data.pack') 'PFH3' $true $false
Pack (Join-Path $privateData 'movie.pack') 'PFHs' $true $false 4
$found = [RemasteredCE.Mods]::Discover($game,[string[]]@(),[string[]]@())
Assert ($found.Count -eq 2) 'Discover private mods and exclude reconstructed/vanilla base packs'
Assert (($found | Where-Object Name -eq 'movie.pack').AutoLoaded) 'Private-data movie pack is marked automatically loaded'
$mods = New-Object 'System.Collections.Generic.List[RemasteredCE.ModPack]'
$mod = $found | Where-Object Name -eq 'private.pack'; $mod.Enabled = $true; $mods.Add($mod)
$scriptPath = Join-Path $testRoot 'user.script.txt'
$sessionRoot = Join-Path $testRoot 'sessions'
$original = [Text.Encoding]::Unicode.GetPreamble() + [Text.Encoding]::Unicode.GetBytes('mod "manual.pack"; add_working_directory "C:/manual"; keep_this true;')
[IO.File]::WriteAllBytes($scriptPath,$original)
$hash = [RemasteredCE.Mods]::Hash($scriptPath)
$manualSession = [RemasteredCE.ModScriptSession]::Prepare($sessionRoot,$scriptPath,$null,$mods,$true,[Func[bool]]{return $false})
Assert ($null -eq $manualSession -and [RemasteredCE.Mods]::Hash($scriptPath) -eq $hash) 'Manual launch leaves existing script byte-for-byte unchanged'
Assert (!(Test-Path (Join-Path $sessionRoot 'script-session.json'))) 'Manual launch creates no script replacement journal'
$missingScript = Join-Path $testRoot 'missing/user.script.txt'
[RemasteredCE.ModScriptSession]::Prepare($sessionRoot,$missingScript,$null,$mods,$true,[Func[bool]]{return $false}) | Out-Null
Assert (!(Test-Path $missingScript)) 'Manual launch does not create a missing user script'
$session = [RemasteredCE.ModScriptSession]::Prepare($sessionRoot,$scriptPath,'C:/active',$mods,$false,[Func[bool]]{return $false})
Assert ([IO.File]::ReadAllText($scriptPath).Contains('mod "private.pack";')) 'Selected-mod mode writes selected pack command'
$session.Dispose()
Assert ([RemasteredCE.Mods]::Hash($scriptPath) -eq $hash) 'Selected-mod mode restores original bytes after play'
$session = [RemasteredCE.ModScriptSession]::Prepare($sessionRoot,$scriptPath,'C:/active',$mods,$false,[Func[bool]]{return $false})
[RemasteredCE.ModScriptSession]::Prepare($sessionRoot,$scriptPath,$null,$mods,$true,[Func[bool]]{return $false}) | Out-Null
Assert ([RemasteredCE.Mods]::Hash($scriptPath) -eq $hash) 'Manual mode recovers an interrupted selected-mod session first'
$profile = New-Object RemasteredCE.ModProfile; $profile.Name = 'Manual'; $profile.UseExistingScript = $true
[RemasteredCE.Mods]::SaveProfile((Join-Path $testRoot 'profile'),$profile,$mods)
$loaded = [RemasteredCE.Mods]::Profiles((Join-Path $testRoot 'profile'))
Assert ($loaded[0].UseExistingScript) 'Manual script preference persists in profiles'
$form = New-Object RemasteredCE.ModForm($game, [string[]]@(), $true)
$flags = [Reflection.BindingFlags]'Instance,NonPublic'
$check = $form.GetType().GetField('existingScript',$flags).GetValue($form)
$grid = $form.GetType().GetField('grid',$flags).GetValue($form)
$check.Checked = $true
Assert (!$grid.Enabled) 'Manual mode visibly disables selection grid'
$check.Checked = $false
Assert ($grid.Enabled) 'Returning to selection mode enables selection grid'
$form.Dispose()
"TOTAL PASS: $script:passed"
