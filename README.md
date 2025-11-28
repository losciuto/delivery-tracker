# Scadenziario Consegne (Delivery Tracker)

Un'applicazione desktop in Python per gestire le scadenze delle consegne da diverse piattaforme online.

## Funzionalità
- **Gestione Ordini**: Traccia ordini con dettagli completi:
    - Data Ordine
    - Piattaforma
    - Venditore
    - Destinazione
    - Descrizione Oggetto
    - Link (cliccabile)
    - Quantità
    - Consegna Prevista
    - Posizione (dove si trova il materiale)
    - Note (per difformità o difetti)
- **Allarmi Visivi**:
    - **Verde**: Materiale consegnato (evidenziazione intera riga).
    - **Rosso**: Consegna scaduta.
    - **Arancione**: Consegna prevista per oggi.
    - **Giallo**: Consegna in arrivo (entro 2 giorni).
- **Notifiche**: Avviso popup all'avvio per le consegne scadute.
- **Interfaccia Utente**:
    - Lingua Italiana.
    - Colonne ordinabili e ridimensionabili.
    - Design moderno.
- **Stato**: Contrassegna gli ordini come "Consegnato".

## Requisiti
- Python 3
- PyQt6

## Installazione
1. Clona o scarica la repository.
2. Installa le dipendenze:
```bash
pip install -r requirements.txt
```

## Utilizzo
Avvia l'applicazione con:
```bash
python main.py
```

## Autore
Massimo Lo Sciuto
Supporto: Antigravity
Sviluppo: Gemini 3 Pro
