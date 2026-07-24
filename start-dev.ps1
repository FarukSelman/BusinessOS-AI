Write-Host ""
Write-Host "========== BusinessOS AI ==========" -ForegroundColor Cyan
Write-Host ""

# Docker kontrolü
docker info *> $null

if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker Desktop çalışmıyor!" -ForegroundColor Red
    exit
}

# Windows PostgreSQL servisini durdur
try {
    $service = Get-Service postgresql-x64-18 -ErrorAction Stop

    if ($service.Status -eq "Running") {
        Stop-Service postgresql-x64-18
        Write-Host "Windows PostgreSQL durduruldu." -ForegroundColor Yellow
    }
}
catch {}

# Docker Compose
Set-Location infrastructure

docker compose up -d

# Backend
Set-Location ..

Set-Location backend

& .\.venv\Scripts\Activate.ps1

uvicorn app.main:app --reload