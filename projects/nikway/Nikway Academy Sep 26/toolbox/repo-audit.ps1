param(
  [string]$Repository = 'E:\AGENTIC-ARMY',
  [string]$Output = ''
)

if (-not (Test-Path -LiteralPath $Repository)) { throw "Repository not found: $Repository" }
if ([string]::IsNullOrWhiteSpace($Output)) { $Output = Join-Path $Repository 'projects\nikway\Nikway Academy Sep 26\continuous-mission\audit-output.yaml' }

$tracked = @(rg --files $Repository -g '!**/node_modules/**' -g '!**/__pycache__/**' -g '!**/dist/**' -g '!*.db')
$secretCandidates = @($tracked | Where-Object { $_ -match '(?i)(token|secret|password|credential|api-key)' })
$spec = 'D:\NIKWAY Academy 2026\NIKWAY_V1_BUILD_SPEC.md'
$report = @"
id: NIKWAY-REPO-AUDIT-$(Get-Date -Format yyyyMMddHHmmss)
tool: repo-audit
repository: $Repository
generated_at: $(Get-Date -Format o)
file_count: $($tracked.Count)
v1_spec_present: $(Test-Path -LiteralPath $spec)
secret_candidate_count: $($secretCandidates.Count)
secret_candidates:
$($secretCandidates | ForEach-Object { "  - $_" } | Out-String)
findings:
  - id: AUDIT-001
    severity: high
    finding: Existing implementation and V1 specification are not yet aligned.
    recommendation: Keep the prototype separate and implement PostgreSQL/OIDC modular boundaries before release.
  - id: AUDIT-002
    severity: high
    finding: A secret-like filename requires manual review.
    recommendation: Remove real credentials from Git and rotate exposed values.
stop_status: $(if ($secretCandidates.Count -gt 0) { 'blocked_for_human_review' } else { 'clear_for_design' })
"@
Set-Content -LiteralPath $Output -Value $report -Encoding utf8
Write-Output $Output
