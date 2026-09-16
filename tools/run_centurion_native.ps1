param([ValidateSet('Lab','Stress','Build','Validate','Capture','Benchmark')][string]$Action='Lab')
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
$enginePath='D:/Wanjie/tools/Godot/4.7.2/Godot_v4.7.2-stable_win64_console.exe'
$engineVersion=(& $enginePath --version | Out-String).Trim()
if($engineVersion -notmatch '^4\.7\.2\.stable\.official\.') { throw "Wrong Godot: $engineVersion" }
switch($Action) {
 'Lab' { & $enginePath --path $projectRoot res://scenes/tests/roman_centurion_rig_lab.tscn }
 'Stress' { & $enginePath --path $projectRoot --resolution 1920x1080 res://scenes/tests/roman_centurion_stress_test.tscn }
 'Benchmark' { & $enginePath --path $projectRoot --resolution 1920x1080 res://scenes/tests/roman_centurion_stress_test.tscn -- --benchmark }
 'Build' { & $enginePath --headless --path $projectRoot --script res://scripts/build/build_centurion_scenes.gd }
 'Capture' { & $enginePath --path $projectRoot --script res://scripts/tests/capture_centurion_native.gd }
 'Validate' {
  foreach($testName in @('test_centurion_native','test_centurion_lab')) {
   $testOutput=& $enginePath --headless --path $projectRoot --script "res://scripts/tests/$testName.gd" 2>&1
   $testOutput | Write-Output
   if($LASTEXITCODE -ne 0 -or ($testOutput | Out-String) -match 'SCRIPT ERROR|ERROR:') { throw "$testName failed" }
  }
 }
}
