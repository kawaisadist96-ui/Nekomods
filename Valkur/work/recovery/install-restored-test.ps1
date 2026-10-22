$ErrorActionPreference = 'Stop'
$taskRoot = $PSScriptRoot
$targetRoot = 'C:\Users\Administrator\Documents\Paradox Interactive\Crusader Kings III\mod\valkur_units_test'
$relativeMesh = 'gfx\models\units\infantry\valkur\valkur.mesh'
$targetFile = Join-Path $targetRoot $relativeMesh
$stagingFile = Join-Path $taskRoot 'export\valkur.mesh'
$backupFile = Join-Path $taskRoot ('mod-before-restoration\' + $relativeMesh)
$roundtrip = Get-Content -LiteralPath (Join-Path $taskRoot 'roundtrip.json') -Raw | ConvertFrom-Json
if (-not $roundtrip.geometry_matches_export_input -or -not $roundtrip.skin_matches_export_input -or -not $roundtrip.skeleton_matches_previous_game_mesh -or $roundtrip.reimport_weight_mismatches -ne 0) { throw 'Export verification has not passed.' }
$beforeHash = (Get-FileHash -LiteralPath $targetFile -Algorithm SHA256).Hash
if ($beforeHash -ne (Get-FileHash -LiteralPath $backupFile -Algorithm SHA256).Hash) { throw 'Current mod mesh changed after backup. Inspect before replacing.' }
if ($beforeHash -ne 'F051C9B3CE4F63BB961FCB85BA06876CD00E275E44E90D8B809B9E946EC27E57') { throw 'Unexpected original mesh.' }
$otherFiles = @(Get-ChildItem -LiteralPath $targetRoot -Recurse -File | Where-Object { $_.FullName -ne $targetFile } | ForEach-Object { @{ path=$_.FullName; sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash } })
$newHash = (Get-FileHash -LiteralPath $stagingFile -Algorithm SHA256).Hash
$temporaryFile = $targetFile + '.recovery-pending'
if (Test-Path -LiteralPath $temporaryFile) { throw 'Pending file already exists; inspect it first.' }
Copy-Item -LiteralPath $stagingFile -Destination $temporaryFile
if ((Get-FileHash -LiteralPath $temporaryFile -Algorithm SHA256).Hash -ne $newHash) { throw 'Staged copy hash mismatch.' }
Move-Item -LiteralPath $temporaryFile -Destination $targetFile -Force
$afterHash = (Get-FileHash -LiteralPath $targetFile -Algorithm SHA256).Hash
$unchanged = @($otherFiles | Where-Object { (Get-FileHash -LiteralPath $_.path -Algorithm SHA256).Hash -ne $_.sha256 }).Count -eq 0
$manifest = @{ installed_at=(Get-Date).ToString('o'); destination=$targetFile; source=$stagingFile; backup=$backupFile; previous_sha256=$beforeHash; staged_sha256=$newHash; installed_sha256=$afterHash; all_other_mod_files_unchanged=$unchanged; preserved_files=$otherFiles; in_game_test_performed=$false; status='restored test candidate; remaining extreme-pose deformation recorded in RESTORATION-NOTES.md' }
$manifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $taskRoot 'deployment.json') -Encoding utf8
if ($afterHash -ne $newHash -or -not $unchanged) { throw 'Post-install verification failed; inspect deployment.json.' }
Write-Output ('INSTALLED ' + $targetFile)
Write-Output ('SHA256 ' + $afterHash)
Write-Output ('PRESERVED_OTHER_FILES ' + $otherFiles.Count)
