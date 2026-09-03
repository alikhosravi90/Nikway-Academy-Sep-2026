param(
    [Parameter(Mandatory=$true)][string]$BackupPath,
    [string]$Container = "nikway-restore-verification",
    [string]$Database = "nikway_restore",
    [string]$User = "nikway_restore",
    [string]$Password = "restore-only-password"
)

docker rm -f $Container 2>$null | Out-Null
docker run -d --name $Container -e POSTGRES_DB=$Database -e POSTGRES_USER=$User -e POSTGRES_PASSWORD=$Password postgres:16-alpine | Out-Null
if ($LASTEXITCODE -ne 0) { throw "restore container failed to start" }
try {
    $ready = $false
    for ($i = 0; $i -lt 30; $i++) {
        docker exec $Container pg_isready -U $User -d $Database 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { $ready = $true; break }
        Start-Sleep -Seconds 2
    }
    if (-not $ready) { throw "restore database did not become ready" }
    docker cp $BackupPath "${Container}:/tmp/nikway-v1.dump"
    docker exec $Container pg_restore -U $User -d $Database --clean --if-exists --no-owner --no-acl /tmp/nikway-v1.dump
    if ($LASTEXITCODE -ne 0) { throw "pg_restore failed" }
    $tables = docker exec $Container psql -U $User -d $Database -Atc "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'"
    if ([int]$tables -lt 1) { throw "restore verification found no public tables" }
    Write-Output "restore_verified=$tables"
} finally {
    docker rm -f $Container 2>$null | Out-Null
}
