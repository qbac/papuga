#!/usr/bin/env bash
# Buduje binarkę Papugi na Linuksie.
# Uruchom z katalogu głównego projektu: ./scripts/build_linux.sh
set -euo pipefail

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install -r requirements.txt

./.venv/bin/python scripts/generate_icon.py
./.venv/bin/pyinstaller papuga.spec --noconfirm

echo ""
echo "Gotowe! Binarka: dist/Papuga/Papuga"
