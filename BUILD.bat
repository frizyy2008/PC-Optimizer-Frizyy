@echo off
chcp 65001 >nul
title PC Optimizer — Сборка EXE
color 0A

echo.
echo  ╔══════════════════════════════════════╗
echo  ║   PC OPTIMIZER PRO — СБОРКА .EXE    ║
echo  ╚══════════════════════════════════════╝
echo.

python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo  [!] Python не найден! Скачай: https://python.org
    echo  [!] При установке отметь "Add Python to PATH"
    pause & exit
)
echo  [+] Python найден

echo  [*] Устанавливаю зависимости (customtkinter, pyinstaller)...
pip install -r requirements.txt --quiet --disable-pip-version-check
echo  [+] Зависимости установлены
echo.
echo  [*] Собираю EXE, подождите 1-2 минуты...
echo.

if exist icon.ico (
    pyinstaller --onefile --windowed --name "PC_Optimizer_Pro" --icon=icon.ico optimizer.py
) else (
    pyinstaller --onefile --windowed --name "PC_Optimizer_Pro" optimizer.py
)

echo.
if exist "dist\PC_Optimizer_Pro.exe" (
    echo  ╔══════════════════════════════════════╗
    echo  ║   ГОТОВО!  dist\PC_Optimizer_Pro.exe ║
    echo  ╚══════════════════════════════════════╝
    explorer dist
) else (
    echo  [!] Ошибка сборки. Проверь вывод выше.
)

echo.
pause
