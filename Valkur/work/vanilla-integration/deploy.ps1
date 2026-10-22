$ErrorActionPreference = 'Stop'
$taskRoot = $PSScriptRoot
$relative = 'gfx\models\units\infantry\valkur'
$modRoot = 'C:\Users\Administrator\Documents\Paradox Interactive\Crusader Kings III\mod\valkur_units_test'
$target = Join-Path $modRoot $relative
$stage = Join-Path (Join-Path $taskRoot 'staged') $relative
$backup = Join-Path (Join-Path $taskRoot 'mod-before') $relative
$check = Get-Content -LiteralPath (Join-Path $taskRoot 'integration-validation.json') -Raw | ConvertFrom-Json
$roundtrip = @(Get-Content -LiteralPath (Join-Path $taskRoot 'roundtrip.json') -Raw | ConvertFrom-Json)
if ($check.animation_count -ne 26 -or $roundtrip.Count -ne 5) { throw 'Validation incomplete' }
$files = @(Get-ChildItem -LiteralPath $stage -File | Where-Object { $_.Extension -in '.mesh','.anim','.asset' })
if ($files.Count -ne 32) { throw "Unexpected file count: $($files.Count)" }
$records = @()
foreach ($file in $files) {
 $dest = Join-Path $target $file.Name
 $old = Join-Path $backup $file.Name
 $before = $null
 if (Test-Path -LiteralPath $dest) {
  $before = (Get-FileHash -LiteralPath $dest -Algorithm SHA256).Hash
  if (!(Test-Path -LiteralPath $old)) { throw "Backup missing: $old" }
  if ((Get-FileHash -LiteralPath $old -Algorithm SHA256).Hash -ne $before) { throw "Live file changed since snapshot: $dest" }
 }
 $records += [pscustomobject]@{file=$file.Name;before=$before;after=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash}
}
$written = @()
try {
 foreach ($record in $records) {
  $dest = Join-Path $target $record.file
  $pending = $dest + '.valkur-pending'
  Copy-Item -LiteralPath (Join-Path $stage $record.file) -Destination $pending
  Move-Item -LiteralPath $pending -Destination $dest -Force
  $written += $record
  if ((Get-FileHash -LiteralPath $dest -Algorithm SHA256).Hash -ne $record.after) { throw "Hash mismatch: $dest" }
 }
} catch {
 foreach ($record in $written) {
  $dest = Join-Path $target $record.file
  if ($null -ne $record.before) { Copy-Item -LiteralPath (Join-Path $backup $record.file) -Destination $dest -Force }
  else { Remove-Item -LiteralPath $dest }
 }
 throw
}
[pscustomobject]@{time=(Get-Date -Format o);target=$target;backup=$backup;files=$records;in_game_test=$false} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $taskRoot 'deployment.json') -Encoding UTF8
Write-Output "DEPLOYED $($records.Count) files; hashes verified."
