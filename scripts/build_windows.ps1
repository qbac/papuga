# Buduje Papuga.exe na Windows.
# Uruchom w PowerShell z katalogu głównego projektu:
#   .\scripts\build_windows.ps1

$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

.\.venv\Scripts\pip install --upgrade pip
.\.venv\Scripts\pip install -r requirements.txt

.\.venv\Scripts\python scripts\generate_icon.py
.\.venv\Scripts\pyinstaller papuga.spec --noconfirm

Write-Host ""
Write-Host "Gotowe! Plik wykonywalny: dist\Papuga.exe (jeden plik, nie wymaga Pythona)." -ForegroundColor Green
