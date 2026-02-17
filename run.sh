#!/bin/bash
# Script di avvio per Delivery Tracker

# Attiva l'ambiente virtuale se esiste
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "⚠️  Ambiente virtuale non trovato!"
    echo "    Esegui './setup.sh' per configurare il progetto prima di avviarlo."
    exit 1
fi

# Avvia l'applicazione
python3 main.py
