Write-Host ""
Write-Host "========== BusinessOS AI ==========" -ForegroundColor Cyan
Write-Host ""

# 1. Docker Kontrolü
docker info *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker Desktop çalışmıyor!" -ForegroundColor Red
    exit
}

# 2. Windows Yerel PostgreSQL Servisini Durdur
try {
    $service = Get-Service postgresql-x64-18 -ErrorAction Stop
    if ($service.Status -eq "Running") {
        Stop-Service postgresql-x64-18
        Write-Host "Windows PostgreSQL durduruldu." -ForegroundColor Yellow
    }
}
catch {}

# 3. Docker Compose Başlat (PostgreSQL + Redis)
Set-Location infrastructure
docker compose up -d

Write-Host "Veritabanının hazır olması bekleniyor..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# 4. pgvector Eklentisini Etkinleştir
docker exec businessos-postgres psql -U postgres -d businessos_ai -c "CREATE EXTENSION IF NOT EXISTS vector;" *> $null

# 5. Backend Ortamı ve Migration
Set-Location ..
Set-Location backend

& .\.venv\Scripts\Activate.ps1

Write-Host "Veritabanı migration'ları uygulanıyor..." -ForegroundColor Cyan
alembic upgrade head

if ($LASTEXITCODE -ne 0) {
    Write-Host "Migration sırasında hata oluştu!" -ForegroundColor Red
    exit
}

# 6. Celery Worker ve Beat (randevu hatırlatma e-postaları)
#    Her biri ayrı bir PowerShell penceresinde açılır; stop-dev.ps1 kapatır.
$backendPath = (Get-Location).Path
$activate = Join-Path $backendPath ".venv\Scripts\Activate.ps1"
New-Item -ItemType Directory -Force -Path (Join-Path $backendPath ".celery") | Out-Null

Write-Host "Celery worker ve beat başlatılıyor..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$backendPath'; & '$activate'; celery -A app.workers.celery_app worker --pool=solo --loglevel=info"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$backendPath'; & '$activate'; celery -A app.workers.celery_app beat --loglevel=info --schedule .celery\celerybeat-schedule"

# 7. Sunucuyu Başlat
Write-Host "Backend başlatılıyor..." -ForegroundColor Green
uvicorn app.main:app --reload
