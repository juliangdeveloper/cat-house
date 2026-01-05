#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Reset database and run fresh migrations
.DESCRIPTION
    This script:
    1. Stops all services and removes volumes (full reset)
    2. Starts services fresh
    3. Generates new migrations for all services
    4. Applies all migrations to the database
.NOTES
    WARNING: This will DELETE all local data!
    Run this script from the cat-house-backend directory
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Red
Write-Host "  DATABASE RESET AND MIGRATION" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Red
Write-Host ""
Write-Host "WARNING: This will DELETE all local data!" -ForegroundColor Yellow
Write-Host ""

$confirmation = Read-Host "Are you sure you want to continue? (yes/no)"
if ($confirmation -ne "yes") {
    Write-Host "Operation cancelled." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "Step 1: Stopping services and removing volumes..." -ForegroundColor Cyan
docker-compose down -v
Write-Host "✓ Services stopped and volumes removed" -ForegroundColor Green
Write-Host ""

Write-Host "Step 2: Rebuilding and starting services..." -ForegroundColor Cyan
docker-compose up -d --build
Start-Sleep -Seconds 10
Write-Host "✓ Services rebuilt and started" -ForegroundColor Green
Write-Host ""

Write-Host "Step 3: Generating migrations..." -ForegroundColor Cyan
& "$PSScriptRoot\generate-migrations.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Migration generation failed" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Migrations generated" -ForegroundColor Green
Write-Host ""

Write-Host "Step 4: Applying migrations..." -ForegroundColor Cyan
& "$PSScriptRoot\init-local-db.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Migration application failed" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Migrations applied" -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "  RESET AND MIGRATION COMPLETE" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Database is ready for development!" -ForegroundColor Green
