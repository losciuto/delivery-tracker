# Istruzioni Agent - Delivery Tracker

## Lingua di Comunicazione
- **IMPORTANTE**: Comunica SEMPRE in **italiano** con l'utente.
  > [!NOTE]
  > **IT**: La lingua da utilizzare va modificata in funzione della propria.  
  > **EN**: The language to be used should be modified according to your own.
- Mantieni un tono professionale e collaborativo.

## Gestione Multilingua del Progetto
- Il progetto supporta ufficialmente più lingue.
- Ogni modifica documentale (es. README) deve essere riportata sia in italiano (`README.md`) che in inglese (`README_EN.md`).
- Quando aggiungi nuove funzionalità, assicurati che le stringhe siano predisposte per l'internazionalizzazione (se applicabile).

## Contesto Tecnico
- **Linguaggio**: Python 3.12+
- **GUI**: PyQt6
- **Database**: SQLite
- **Ambiente**: Linux
- **Virtual Env**: Preferenza per `.venv` (o `venv` come fallback).

## Standard di Codifica
- Usa nomi di variabili e funzioni descrittivi (preferibilmente in inglese per consistenza col codice esistente).
- Documenta le funzioni complesse con docstring.
- Mantieni la separazione delle responsabilità tra logica di business (`database.py`, `utils.py`) e interfaccia (`gui/`).
