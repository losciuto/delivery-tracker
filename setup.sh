#!/bin/bash

# =================================================================
# Script di Setup per Delivery Tracker v2.1.0
# =================================================================

echo "📦 Inizio configurazione di Delivery Tracker..."

# 1. Verifica Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Errore: Python 3 non è installato. Per favore installalo prima di procedere."
    exit 1
fi

# 2. Creazione ambiente virtuale
if [ ! -d "venv" ]; then
    echo "🔧 Creazione dell'ambiente virtuale (venv)..."
    python3 -m venv venv
else
    echo "✅ Ambiente virtuale già esistente."
fi

# 3. Attivazione e installazione dipendenze
echo "📥 Installazione delle dipendenze Python..."
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

# 4. Verifica librerie di sistema Qt (Linux)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "🔍 Verifica librerie di sistema per Qt..."
    MISSING_LIBS=()
    
    # Lista librerie comuni per PyQt6 su Linux
    LIBS=("libxcb-cursor.so.0" "libxcb-xinerama.so.0")
    
    for lib in "${LIBS[@]}"; do
        if ! ldconfig -p | grep -q "$lib"; then
            MISSING_LIBS+=("$lib")
        fi
    done
    
    if [ ${#MISSING_LIBS[@]} -gt 0 ]; then
        echo "⚠️  Attenzione: Alcune librerie Qt sembrano mancare: ${MISSING_LIBS[*]}"
        echo "   Puoi installarle con:"
        echo "   Ubuntu/Debian: sudo apt-get install libxcb-cursor0 libxcb-xinerama0"
        echo "   Fedora: sudo dnf install xcb-util-cursor xcb-util-renderutil"
    else
        echo "✅ Librerie Qt di sistema verificate."
    fi
fi

# 5. Permessi per lo script di avvio
chmod +x run.sh
echo "🚀 Setup completato con successo!"
echo "   Puoi avviare l'applicazione con: ./run.sh"
echo "================================================================="
