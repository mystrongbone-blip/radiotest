@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 骨骼3D 檢視器

set "PY="
where py >nul 2>nul
if not errorlevel 1 set "PY=py -3"
if not defined PY (
    where python >nul 2>nul
    if not errorlevel 1 set "PY=python"
)
if not defined PY (
    echo.
    echo   找不到 Python 3。
    echo   到 https://www.python.org/downloads/ 下載，安裝時勾选 "Add python.exe to PATH"。
    echo.
    pause
    exit /b 1
)

%PY% serve.py %*

echo.
echo   伺服器已停止，視窗可關閉。
pause