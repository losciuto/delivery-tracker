#!/bin/bash
# Script di avvio per Delivery Tracker

# Attiva l'ambiente virtuale se esiste
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Avvia l'applicazione
python main.py
