# Phoenix AI Disaster Recovery Backup/Restore PowerShell Script
# Usage:
#   .\backup_restore.ps1 -Action backup
#   .\backup_restore.ps1 -Action restore [-BackupPath path]

param (
    [Parameter(Mandatory=$true)]
    [ValidateSet("backup", "restore")]
    [string]$Action,

    [Parameter(Mandatory=$false)]
    [string]$BackupPath = ""
)

$dbPath = "ai_project/memory/memory_db.json"
$backupDir = "ai_project/memory/backups"

function Create-Backup {
    Write-Output "Starting memory database backup..."
    if (-not (Test-Path $dbPath)) {
        Write-Error "Database file not found at $dbPath. Nothing to backup."
        exit 1
    }

    if (-not (Test-Path $backupDir)) {
        New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    }

    $timestamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
    $backupFile = Join-Path $backupDir "memory_db_$timestamp.json"
    $tempFile = "$backupFile.tmp"

    try {
        Copy-Item -Path $dbPath -Destination $tempFile -Force
        
        # Verify JSON integrity using PowerShell
        $json = Get-Content -Raw -Path $tempFile | ConvertFrom-Json
        if (-not $json.memories -or -not $json.kg_graph) {
            throw "Missing core database structure fields."
        }

        # Rename temp to final
        $leafName = Split-Path $backupFile -Leaf
        Rename-Item -Path $tempFile -NewName $leafName -Force
        Write-Output "SUCCESS: Backup created at $backupFile"

        # Rotate backups (keep latest 5)
        $files = Get-ChildItem -Path $backupDir -Filter "memory_db_*.json" | Sort-Object LastWriteTime -Descending
        if ($files.Count -gt 5) {
            $files | Select-Object -Skip 5 | Remove-Item -Force
        }
    }
    catch {
        if (Test-Path $tempFile) {
            Remove-Item -Path $tempFile -Force
        }
        Write-Error "Backup creation failed: $_"
        exit 1
    }
}

function Restore-Backup {
    $targetPath = $BackupPath
    if ([string]::IsNullOrEmpty($targetPath)) {
        Write-Output "No backup file specified. Locating the latest backup..."
        if (Test-Path $backupDir) {
            $latest = Get-ChildItem -Path $backupDir -Filter "memory_db_*.json" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
            if ($latest) {
                $targetPath = $latest.FullName
            }
        }
    }

    if ([string]::IsNullOrEmpty($targetPath) -or -not (Test-Path $targetPath)) {
        Write-Error "ERROR: Target backup file not found or empty."
        exit 1
    }

    Write-Output "Restoring database from $targetPath..."

    try {
        # Verify target integrity
        $json = Get-Content -Raw -Path $targetPath | ConvertFrom-Json
        if (-not $json.memories -or -not $json.kg_graph) {
            throw "Corrupted or invalid database structure."
        }

        # Create safety copy
        if (Test-Path $dbPath) {
            Copy-Item -Path $dbPath -Destination "$dbPath.safety" -Force
        }

        Copy-Item -Path $targetPath -Destination $dbPath -Force
        Write-Output "SUCCESS: Database restored successfully from $targetPath"

        if (Test-Path "$dbPath.safety") {
            Remove-Item -Path "$dbPath.safety" -Force
        }
    }
    catch {
        Write-Error "Restore failed: $_"
        if (Test-Path "$dbPath.safety") {
            Move-Item -Path "$dbPath.safety" -Destination $dbPath -Force -Confirm:$false
            Write-Output "Reverted to safety database copy."
        }
        exit 1
    }
}

if ($Action -eq "backup") {
    Create-Backup
}
elseif ($Action -eq "restore") {
    Restore-Backup
}
