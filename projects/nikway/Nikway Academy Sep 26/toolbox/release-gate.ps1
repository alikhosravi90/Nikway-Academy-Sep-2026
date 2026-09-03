param(
  [string]$Package = 'E:\AGENTIC-ARMY\projects\nikway\Nikway Academy Sep 26\continuous-mission\publish-ready-sample'
)

if (-not (Test-Path -LiteralPath $Package)) { throw "Package not found: $Package" }
$manifest = Join-Path $Package 'release-manifest.yaml'
$summary = Join-Path $Package 'stage-summary.yaml'
$readiness = Join-Path $Package '..\final-readiness-report.yaml'
$required = @($manifest, $summary, $readiness)
$missing = @($required | Where-Object { -not (Test-Path -LiteralPath $_) })
$status = if ($missing.Count -eq 0) { 'ready_for_review' } else { 'not_ready' }
Write-Output "status=$status"
Write-Output "missing=$($missing.Count)"
if ($missing.Count -gt 0) { $missing | ForEach-Object { Write-Output $_ } }
if ($status -eq 'ready_for_review') {
  Write-Output 'external_publish=requires_human_confirmation'
}
