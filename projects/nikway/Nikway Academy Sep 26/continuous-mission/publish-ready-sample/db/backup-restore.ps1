param(
    [string]$Container = "publish-ready-sample-postgres-1",
    [string]$Database = "nikway_v1",
    [string]$User = "nikway_app",
    [string]$BackupPath = "backup/nikway-v1.dump"
)

$resolvedBackup = if ([System.IO.Path]::IsPathRooted($BackupPath)) {
    [System.IO.Path]::GetFullPath($BackupPath)
} else {
    Join-Path (Get-Location) $BackupPath
}
$backupDirectory = Split-Path -Parent $resolvedBackup
New-Item -ItemType Directory -Force -Path $backupDirectory | Out-Null
docker exec $Container pg_dump -Fc -U $User -d $Database -f /tmp/nikway-v1.dump
if ($LASTEXITCODE -ne 0) { throw "pg_dump failed" }
docker cp "${Container}:/tmp/nikway-v1.dump" $resolvedBackup
if (-not (Test-Path -LiteralPath $resolvedBackup)) { throw "backup was not copied" }
Write-Output "backup_created=$resolvedBackup"
