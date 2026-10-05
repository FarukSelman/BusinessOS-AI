@echo off
title BusinessOS AI - Frontend
cd /d "%~dp0frontend"
set NODE_OPTIONS=--max-old-space-size=2048
echo.
echo Frontend hazirlaniyor (1-3 dakika surebilir, bilgisayar bu sirada biraz yavaslayabilir)...
echo.
call npm run build:light
if errorlevel 1 (
  echo.
  echo HATA: frontend derlenemedi. Bu pencerenin ekran goruntusunu Claude'a gonder.
  pause
  exit /b 1
)
set NODE_OPTIONS=
echo.
echo Hazir! Tarayici birazdan http://localhost:3000 adresini acacak.
echo Frontend'i kapatmak icin bu pencereyi kapatman yeterli.
echo Not: backend icin start-dev.ps1 ayrica acik olmali.
echo.
start "" cmd /c "timeout /t 4 >nul & start http://localhost:3000"
call npm run start
