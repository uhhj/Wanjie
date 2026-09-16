param([switch]$Stress)
$taskProject = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$taskGodot = 'D:\Wanjie\tools\Godot\4.7.2\Godot_v4.7.2-stable_win64_console.exe'
if (-not (Test-Path -LiteralPath $taskGodot)) { throw "Godot not found: $taskGodot" }
$taskVersion = & $taskGodot --version
if ($taskVersion -notmatch '^4\.7\.2\.stable') { throw "Required Godot 4.7.2 Stable, got $taskVersion" }
$taskScene = if ($Stress) { 'res://scenes/tests/minotaur_breaker_stress_test.tscn' } else { 'res://scenes/tests/minotaur_breaker_rig_lab.tscn' }
& $taskGodot --path $taskProject $taskScene
