# Scadenziario Consegne (Delivery Tracker) v2.0.1

Un'applicazione desktop moderna e completa in Python per gestire le scadenze delle consegne da diverse piattaforme online.

## ✨ Funzionalità Principali

### 📦 Gestione Ordini Completa
- **Tracciamento Dettagliato**: Monitora ordini con informazioni complete:
  - Data Ordine e Consegna Prevista
  - Piattaforma (con suggerimenti predefiniti: Amazon, eBay, AliExpress, ecc.)
  - Venditore e Destinazione
  - Descrizione Oggetto
  - Link cliccabile al prodotto
  - Quantità
  - Posizione fisica (Magazzino, Casa, Ufficio, ecc.)
  - Categoria personalizzabile
  - Note per difformità o difetti

### 🎨 Interfaccia Utente Moderna
- **Design Premium**: Interfaccia moderna con gradientie colori curati
- **Tema Chiaro/Scuro**: Supporto per entrambi i temi
- **Dashboard Interattiva**: Visualizzazione statistiche con grafici
  - Grafico a torta per distribuzione piattaforme
  - Grafico a barre per stato consegne
  - Card statistiche in tempo reale
- **Sidebar Collassabile**: Ottimizza lo spazio di lavoro
- **Ricerca e Filtri Avanzati**:
  - Ricerca testuale in descrizione, venditore e note
  - Filtro per piattaforma
  - Filtro per categoria
  - Mostra/nascondi ordini consegnati

### 🔔 Sistema di Allarmi Visivi
- **Verde**: Materiale consegnato (evidenziazione intera riga)
- **Rosso**: Consegna scaduta
- **Arancione**: Consegna prevista per oggi
- **Giallo**: Consegna in arrivo (entro 2 giorni)
- **Notifiche Popup**: Avviso all'avvio per consegne scadute

### 📊 Export/Import Dati
- **Export Multipli Formati**:
  - **Excel (.xlsx)**: Con formattazione colori e stili
  - **CSV**: Per compatibilità universale
  - **JSON**: Per backup completi
- **Import JSON**: Importa ordini da file JSON

### 💾 Backup Automatico
- Backup automatico del database
- Gestione automatica dei backup (mantiene ultimi 10)
- Creazione backup manuale dalle impostazioni
- Ripristino da backup

### ⚙️ Impostazioni Personalizzabili
- Selezione tema (Chiaro/Scuro)
- Configurazione notifiche
- Giorni di anticipo per allarmi
- Backup automatico
- Visualizzazione ordini consegnati

### 🔍 Funzionalità Avanzate
- **Menu Contestuale**: Click destro per azioni rapide
- **Doppio Click**: Modifica rapida ordini
- **Validazione Input**: Controlli su URL, quantità e campi obbligatori
- **Logging Completo**: Tracciamento di tutte le operazioni
- **Performance Ottimizzate**: Indici database per query veloci
- **Ordinamento Colonne**: Click su intestazioni per ordinare
- **Tooltip**: Informazioni al passaggio del mouse

## 🛠️ Requisiti

- Python 3.8+
- PyQt6
- PyQt6-Charts
- openpyxl (per export Excel)

## 📥 Installazione

1. Clona o scarica la repository:
```bash
git clone https://github.com/losciuto/delivery-tracker.git
cd delivery-tracker
```

2. Installa le dipendenze:
```bash
pip install -r requirements.txt
```

## 🚀 Utilizzo

Avvia l'applicazione con:
```bash
python main.py
```

### Prima Configurazione
1. All'avvio, l'applicazione creerà automaticamente il database
2. Accedi alle Impostazioni per configurare tema e notifiche
3. Inizia ad aggiungere i tuoi ordini!

### Navigazione
- **Dashboard**: Visualizza statistiche e panoramica generale
- **Ordini**: Gestisci la lista completa degli ordini
- **Sidebar**: Accesso rapido a tutte le funzioni
- **Menu File**: Export/Import dati
- **Menu Visualizza**: Cambia vista rapidamente

### Gestione Ordini
- **Aggiungi**: Click su "Aggiungi" nella sidebar o Ctrl+N
- **Modifica**: Doppio click su un ordine o seleziona e click "Modifica"
- **Elimina**: Seleziona e click "Elimina" (con conferma)
- **Segna Consegnato**: Click destro → "Segna come Consegnato"

### Ricerca e Filtri
- Usa la barra di ricerca per trovare ordini specifici
- Filtra per piattaforma o categoria
- Nascondi ordini consegnati per focus sui pendenti

## 📁 Struttura Progetto

```
delivery-tracker/
├── main.py              # Entry point con styling
├── gui/                 # Package interfaccia grafica
│   ├── __init__.py      # Espone MainWindow
│   ├── main_window.py   # Logica principale finestra
│   └── dialogs.py       # Dialoghi (Ordine, Impostazioni)
├── database.py          # Gestione database SQLite
├── config.py            # Configurazioni e temi
├── utils.py             # Utility e helper functions
├── widgets.py           # Widget personalizzati (Dashboard, ecc.)
├── export_manager.py    # Gestione export/import
├── requirements.txt     # Dipendenze Python
├── README.md           # Questo file
├── README_EN.md        # English version
├── LICENSE             # Licenza GPL-3.0
├── logs/               # File di log (auto-creato)
├── backups/            # Backup database (auto-creato)
└── delivery_tracker.db # Database SQLite (auto-creato)
```

## 🔧 Tecnologie Utilizzate

- **PyQt6**: Framework GUI moderno
- **PyQt6-Charts**: Grafici e visualizzazioni
- **SQLite**: Database leggero e veloce
- **openpyxl**: Export Excel con formattazione
- **Python logging**: Sistema di logging robusto

## 📝 Note Tecniche

### Database
- Utilizza SQLite con indici ottimizzati
- Foreign keys abilitate per integrità referenziale
- Migrazione automatica per nuove colonne
- Supporto per categorie e allegati (futuro)

### Performance
- Indici su colonne frequentemente interrogate
- Query ottimizzate con filtri
- Caricamento lazy dei dati
- Caching intelligente

### Sicurezza
- Validazione input completa
- Gestione errori robusta
- Backup automatici
- Logging di tutte le operazioni

## 🐛 Risoluzione Problemi

### L'applicazione non si avvia
- Verifica che Python 3.8+ sia installato
- Controlla che tutte le dipendenze siano installate: `pip install -r requirements.txt`
- Controlla i log in `logs/` per errori specifici

### Errori di export Excel
- Assicurati che `openpyxl` sia installato: `pip install openpyxl`

### Database corrotto
- Ripristina da un backup in `backups/`
- O elimina `delivery_tracker.db` per ricrearlo (perderai i dati)

## 🔄 Aggiornamenti v2.0.1

- ✅ **Fix**: Risolto problema dipendenza mancante (PyQt6-Charts)
- ✅ **UI**: Icone sidebar più intuitive e moderne
- ✅ **Miglioramenti**: Stabilità generale e cleanup codice

## 🔄 Aggiornamenti v2.0.0

### Nuove Funzionalità
- ✅ Dashboard con statistiche e grafici
- ✅ Ricerca e filtri avanzati
- ✅ Export Excel con formattazione
- ✅ Sistema di backup automatico
- ✅ Supporto categorie
- ✅ Tema chiaro/scuro
- ✅ Impostazioni personalizzabili
- ✅ Menu contestuale
- ✅ Validazione input migliorata
- ✅ Logging completo

### Miglioramenti
- ✅ UI/UX completamente ridisegnata
- ✅ Performance ottimizzate con indici database
- ✅ Codice modulare e manutenibile
- ✅ Gestione errori robusta
- ✅ Documentazione completa

## 👨‍💻 Autore

**Massimo Lo Sciuto**
- Supporto: Antigravity
- Sviluppo: Gemini 3 Pro

## 📄 Licenza

Questo progetto è rilasciato sotto licenza GPL-3.0. Vedi il file [LICENSE](LICENSE) per i dettagli.

## 🤝 Contributi

I contributi sono benvenuti! Sentiti libero di aprire issue o pull request.

## 📧 Supporto

Per supporto o domande, apri una issue su GitHub.

---

**Buon tracciamento delle tue consegne! 📦✨**
