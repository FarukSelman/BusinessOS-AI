# BusinessOS AI - uctan uca test (Mailtrap hatirlatma maili + ajanlar, gercek OpenAI)
# e2e-test.bat'a cift tiklayarak calistirilir. Sonuc: backend\e2e-test-sonuc.log
$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root "backend"
$log = Join-Path $backend "e2e-test-sonuc.log"
$py = Join-Path $backend ".venv\Scripts\python.exe"
$alembic = Join-Path $backend ".venv\Scripts\alembic.exe"

function Say($text, $color = "Cyan") {
    Write-Host $text -ForegroundColor $color
    Add-Content -Path $log -Value $text -Encoding UTF8
}
function Run($exe, [string[]]$arguments) {
    & $exe @arguments 2>&1 | ForEach-Object { "$_" } | ForEach-Object {
        Write-Host $_
        Add-Content -Path $log -Value $_ -Encoding UTF8
    }
    return $LASTEXITCODE
}

Set-Content -Path $log -Value "BusinessOS AI e2e test - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -Encoding UTF8

Say "`n[1/6] Docker kontrol ediliyor..."
docker info *> $null
if ($LASTEXITCODE -ne 0) { Say "HATA: Docker Desktop calismiyor. Docker Desktop'i acip tekrar dene." Red; Say "BITTI: HATA" Red; exit 1 }

try {
    $service = Get-Service postgresql-x64-18 -ErrorAction Stop
    if ($service.Status -eq "Running") { Stop-Service postgresql-x64-18; Say "Windows PostgreSQL servisi durduruldu." Yellow }
} catch {}

Say "[2/6] PostgreSQL ve Redis baslatiliyor..."
Push-Location (Join-Path $root "infrastructure")
$null = Run "docker" @("compose", "up", "-d")
Pop-Location
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    docker exec businessos-postgres pg_isready -U postgres *> $null
    if ($LASTEXITCODE -eq 0) { $ready = $true; break }
    Start-Sleep -Seconds 2
}
if (-not $ready) { Say "HATA: PostgreSQL 60 saniyede hazir olmadi." Red; Say "BITTI: HATA" Red; exit 1 }
docker exec businessos-postgres psql -U postgres -d businessos_ai -c "CREATE EXTENSION IF NOT EXISTS vector;" *> $null

Set-Location $backend
if (-not (Test-Path $py)) { Say "HATA: backend\.venv bulunamadi." Red; Say "BITTI: HATA" Red; exit 1 }

Say "[3/6] Migration uygulaniyor (alembic upgrade head)..."
$code = Run $alembic @("upgrade", "head")
if ($code -ne 0) { Say "HATA: migration basarisiz." Red; Say "BITTI: HATA" Red; exit 1 }

Say "`n[4/6] Hatirlatma maili testi (Mailtrap)..."
$mailCode = Run $py @("scripts\reminder_mail_check.py")

Say "`n[5/6] Ajan testi (gercek OpenAI, 1-3 dakika surebilir)..."
$agentCode = Run $py @("scripts\agent_e2e.py")

Say "`n[6/6] AI icgoru testi (gercek OpenAI)..."
$insightCode = Run $py @("scripts\insights_check.py")

Say "`n=================================="
Say ("Mail testi : " + $(if ($mailCode -eq 0) { "BASARILI" } else { "BASARISIZ" }))
Say ("Ajan testi : " + $(if ($agentCode -eq 0) { "kritik hata yok" } else { "KRITIK HATA / durduruldu" }))
Say ("Icgoru testi: " + $(if ($insightCode -eq 0) { "BASARILI" } else { "BASARISIZ" }))
Say "BITTI" Green
