# init-local-db.ps1
# Initialize local PostgreSQL database for Cat House development (Windows PowerShell)

Write-Host "Initializing Cat House Local Database..." -ForegroundColor Cyan

# Wait for PostgreSQL to be ready
Write-Host "Waiting for PostgreSQL to be ready..." -ForegroundColor Yellow
$maxAttempts = 30
$attempt = 0
$isReady = $false

while (-not $isReady -and $attempt -lt $maxAttempts) {
    $attempt++
    try {
        docker-compose exec -T postgres pg_isready -U catuser -d cathouse 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            $isReady = $true
        } else {
            Write-Host "   Waiting for database connection... (Attempt $attempt/$maxAttempts)" -ForegroundColor Gray
            Start-Sleep -Seconds 2
        }
    } catch {
        Write-Host "   Waiting for database connection... (Attempt $attempt/$maxAttempts)" -ForegroundColor Gray
        Start-Sleep -Seconds 2
    }
}

if (-not $isReady) {
    Write-Host "PostgreSQL failed to start after $maxAttempts attempts" -ForegroundColor Red
    exit 1
}

Write-Host "PostgreSQL is ready!" -ForegroundColor Green

# Check if migrations have already been run
$tablesExist = docker-compose exec -T postgres psql -U catuser -d cathouse -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema IN ('auth', 'catalog', 'installation') AND table_name IN ('users', 'cats', 'installations');" 2>$null

if ($tablesExist -match '^\s*[3-9]\d*\s*$') {
    Write-Host "Database already initialized. Skipping migration." -ForegroundColor Yellow
    Write-Host "   To reset the database, run: docker-compose down -v && docker-compose up -d" -ForegroundColor Yellow
    exit 0
}

Write-Host "Running database migrations..." -ForegroundColor Cyan

# Run Alembic migrations from all services
Write-Host "  [1/3] Running auth schema migrations..." -ForegroundColor Yellow
docker-compose exec -T auth-service alembic upgrade head
if ($LASTEXITCODE -ne 0) {
    Write-Host "Auth migration failed. Check logs with: docker-compose logs auth-service" -ForegroundColor Red
    exit 1
}

Write-Host "  [2/3] Running catalog schema migrations..." -ForegroundColor Yellow
docker-compose exec -T catalog-service alembic upgrade head
if ($LASTEXITCODE -ne 0) {
    Write-Host "Catalog migration failed. Check logs with: docker-compose logs catalog-service" -ForegroundColor Red
    exit 1
}

Write-Host "  [3/3] Running installation schema migrations..." -ForegroundColor Yellow
docker-compose exec -T installation-service alembic upgrade head
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installation migration failed. Check logs with: docker-compose logs installation-service" -ForegroundColor Red
    exit 1
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "Database migrations completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Local database is ready for development!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Connection details:" -ForegroundColor Cyan
    Write-Host "  Host: localhost" -ForegroundColor White
    Write-Host "  Port: 5435" -ForegroundColor White
    Write-Host "  Database: cathouse" -ForegroundColor White
    Write-Host "  User: catuser" -ForegroundColor White
    Write-Host "  Password: catpass" -ForegroundColor White
    Write-Host ""
    Write-Host "DATABASE_URL for services:" -ForegroundColor Cyan
    Write-Host "  postgresql+asyncpg://catuser:catpass@postgres:5432/cathouse" -ForegroundColor White
} else {
    Write-Host "Migration failed. Check logs with: docker-compose logs auth-service" -ForegroundColor Red
    exit 1
}
