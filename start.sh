#!/bin/bash
# Projeyi başlatma scripti

cd "$(dirname "$0")"

# Virtual environment'ı aktif et
if [ ! -d ".venv" ]; then
    echo "Virtual environment oluşturuluyor..."
    python3 -m venv .venv
fi

echo "Bağımlılıklar yükleniyor..."
.venv/bin/pip install -q 'fastapi>=0.104.0' 'uvicorn[standard]>=0.24.0' feedparser beautifulsoup4 requests python-dotenv

echo "API başlatılıyor..."
echo "Web arayüzü: http://localhost:8000"
echo ""
.venv/bin/python api.py

