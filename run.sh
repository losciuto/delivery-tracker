#!/bin/bash
# Script di avvio per Delivery Tracker

# Attiva l'ambiente virtuale se esiste
# Attiva l'ambiente virtuale se esiste
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# Avvia l'applicazione
python3 main.py
