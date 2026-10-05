@echo off
title BusinessOS AI - e2e test
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0e2e-test.ps1"
echo.
echo Pencereyi kapatabilirsin.
pause >nul
