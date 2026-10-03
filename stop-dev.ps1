# Celery worker ve beat süreçlerini kapat (start-dev.ps1 ayrı pencerelerde açar)
Get-CimInstance Win32_Process |
    Where-Object { $_.CommandLine -and $_.CommandLine -match "app\.workers\.celery_app" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

Set-Location infrastructure

docker compose down
