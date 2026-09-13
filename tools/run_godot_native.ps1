param(
    [ValidateSet('Lab','Stress','Benchmark','Validate','Capture','Build')]
    [string]$Action = 'Lab',
    [string]$Engine = 'D:/Wanjie/tools/Godot/4.7.2/Godot_v4.7.2-stable_win64_console.exe'
)
$ErrorActionPreference = 'Stop'
$projectPath = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path -LiteralPath $Engine)) { throw "Godot executable missing: $Engine" }
$version = (& $Engine --version | Out-String).Trim()
if ($version -notmatch '^4\.7\.2\.stable\.official\.' -or $version -match 'mono') { throw "Expected Godot 4.7.2 Stable Standard, got $version" }
Push-Location -LiteralPath $projectPath
try {
    switch ($Action) {
        'Lab' { & $Engine --path $projectPath --resolution 1920x1080 }
        'Stress' { & $Engine --path $projectPath --resolution 1920x1080 res://scenes/tests/roman_guard_stress_test.tscn }
        'Benchmark' { & $Engine --path $projectPath --resolution 1920x1080 res://scenes/tests/roman_guard_stress_test.tscn -- --benchmark }
        'Capture' { & $Engine --path $projectPath --script res://scripts/tests/capture_native_animations.gd }
        'Build' { & $Engine --headless --path $projectPath --script res://scripts/build/build_native_scenes.gd }
        'Validate' {
            foreach ($script in @('test_native_rig.gd','test_rig_lab.gd')) {
                $result = & $Engine --headless --path $projectPath --script "res://scripts/tests/$script" 2>&1
                $result | Write-Output
                if ($LASTEXITCODE -ne 0 -or ($result | Out-String) -match 'SCRIPT ERROR|ERROR:') { throw "$script failed" }
            }
        }
    }
} finally { Pop-Location }
