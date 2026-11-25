@echo off
title BusinessOS AI - Frontend
cd /d "%~dp0frontend"
rem Port 3000 doluysa durur: eski frontend acikken derlemek calisan sunucunun dosyalarini
rem degistirir, yeni sunucu da baslayamaz (eski arayuz ve "page couldn't load" hatalari).
netstat -ano | findstr /R /C:":3000 .*LISTENING" >nul
if not errorlevel 1 (
  echo.
  echo UYARI: 3000 portu kullaniliyor - onceki frontend penceresi hala acik.
  echo Once "BusinessOS AI - Frontend" baslikli eski pencereyi kapatin,
  echo emin degilseniz Gorev Yoneticisi'nden node.exe islemlerini sonlandirin.
  echo Sonra bu dosyayi yeniden calistirin.
  echo.
  pause
  exit /b 1
)
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
