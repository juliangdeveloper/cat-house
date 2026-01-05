#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Generate Alembic migrations for all services
.DESCRIPTION
    This script generates migration files for all services that need them.
    It should be run when models are modified and new migrations are needed.
.NOTES
    Run this script from the cat-house-backend directory
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "Generating database migrations for all services..." -ForegroundColor Cyan
Write-Host ""

# Function to generate migration for a service
function Generate-ServiceMigration {
    param(
        [string]$ServiceName,
        [string]$MigrationMessage,
        [int]$StepNumber,
        [int]$TotalSteps
    )
    
    Write-Host "  [$StepNumber/$TotalSteps] Generating $ServiceName migration..." -ForegroundColor Yellow
    
    docker-compose exec -T $ServiceName alembic revision --autogenerate -m "$MigrationMessage"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to generate $ServiceName migration" -ForegroundColor Red
        return $false
    }
    
    # Copy migration files from container to host
    Write-Host "  Copying migration files from container to host..." -ForegroundColor Gray
    $containerName = "cathouse-$($ServiceName.Replace('-service', ''))"
    docker cp "${containerName}:/app/alembic/versions/." "./$ServiceName/alembic/versions/"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "WARNING: Failed to copy migration files" -ForegroundColor Yellow
    }
    
    Write-Host "SUCCESS: $ServiceName migration generated successfully" -ForegroundColor Green
    Write-Host ""
    return $true
}

# Ensure services are running
Write-Host "Ensuring services are running..." -ForegroundColor Cyan
docker-compose up -d
Start-Sleep -Seconds 5
Write-Host ""

# Generate migrations for each service
$success = $true

# Auth service
if (-not (Generate-ServiceMigration -ServiceName "auth-service" -MigrationMessage "Schema update" -StepNumber 1 -TotalSteps 3)) {
    $success = $false
}

# Catalog service
if (-not (Generate-ServiceMigration -ServiceName "catalog-service" -MigrationMessage "Schema update" -StepNumber 2 -TotalSteps 3)) {
    $success = $false
}

# Installation service
if (-not (Generate-ServiceMigration -ServiceName "installation-service" -MigrationMessage "Schema update" -StepNumber 3 -TotalSteps 3)) {
    $success = $false
}

if ($success) {
    Write-Host "All migrations generated successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Review the generated migration files in each service alembic/versions/ folder"
    Write-Host "  2. Run init-local-db.ps1 to apply migrations to local database"
    Write-Host "  3. Commit the migration files to git"
    Write-Host ""
    exit 0
} else {
    Write-Host "Some migrations failed to generate. Check the errors above." -ForegroundColor Red
    exit 1
}
