# Changelog

Tutte le modifiche importanti a questo progetto saranno documentate in questo file.

Il formato è basato su [Keep a Changelog](https://keepachangelog.com/it/1.0.0/),
e questo progetto aderisce al [Semantic Versioning](https://semver.org/lang/it/).

## [2.0.0] - 2025-12-07

### ✨ Aggiunte

#### Interfaccia Utente
- **Dashboard Interattiva** con statistiche in tempo reale
  - Card statistiche (Totale, In Attesa, Consegnati, Scaduti)
  - Grafico a torta per distribuzione piattaforme
  - Grafico a barre per stato consegne
- **Ricerca e Filtri Avanzati**
  - Barra di ricerca testuale
  - Filtro per piattaforma
  - Filtro per categoria
  - Toggle mostra/nascondi consegnati
- **Tema Chiaro/Scuro** configurabile
- **Menu Contestuale** con click destro
- **Sidebar Collassabile** per ottimizzare spazio
- **Validazione Input** completa con messaggi di errore
- **Tooltip** su tutte le celle della tabella

#### Funzionalità
- **Sistema di Categorie** personalizzabili
- **Export Multiplo**:
  - Excel (.xlsx) con formattazione e colori
  - CSV per compatibilità universale
  - JSON per backup completi
- **Import JSON** per ripristino dati
- **Backup Automatico**:
  - Backup all'uscita dell'applicazione
  - Gestione automatica (mantiene ultimi 10)
  - Creazione manuale dalle impostazioni
- **Impostazioni Personalizzabili**:
  - Selezione tema
  - Configurazione notifiche
  - Giorni anticipo allarmi
  - Backup automatico
- **Logging Completo** di tutte le operazioni

#### Database
- **Indici Ottimizzati** per performance migliori
- **Foreign Keys** per integrità referenziale
- **Migrazione Automatica** per nuove colonne
- **Tabelle Aggiuntive**:
  - Categories (categorie personalizzate)
  - Attachments (preparato per allegati futuri)
- **Campi Timestamp** (created_at, updated_at)

#### Codice
- **Architettura Modulare**:
  - `config.py` - Configurazioni e temi
  - `utils.py` - Utility e helper functions
  - `widgets.py` - Widget personalizzati
  - `export_manager.py` - Gestione export/import
- **Type Hints** completi
- **Docstrings** su tutte le funzioni
- **Gestione Errori** robusta con try-except
- **Logger** configurato con file e console

### 🎨 Miglioramenti

#### UI/UX
- **Design Completamente Ridisegnato**:
  - Colori premium e moderni
  - Gradienti sulla sidebar e header tabella
  - Border radius su tutti gli elementi
  - Hover effects e transizioni
  - Scrollbar personalizzate
- **Dialog Migliorati**:
  - Gruppi logici con icone
  - Autocomplete per piattaforme e categorie
  - Placeholder informativi
  - Layout più pulito e organizzato
- **Tabella Migliorata**:
  - Header con gradiente
  - Righe alternate colorate
  - Selezione evidenziata
  - Padding aumentato per leggibilità

#### Performance
- **Query Ottimizzate** con indici database
- **Filtri Lato Database** invece che applicazione
- **Caricamento Lazy** dei dati
- **Caching** delle impostazioni

#### Usabilità
- **Validazione Real-time** nei form
- **Messaggi di Errore** chiari e informativi
- **Conferme** per azioni distruttive
- **Shortcuts** keyboard (Ctrl+N per nuovo ordine)
- **Double-click** per modifica rapida
- **Context Menu** per azioni rapide

### 🔧 Modifiche Tecniche

#### Dipendenze
- Aggiunto `PyQt6-Charts` per grafici
- Aggiunto `openpyxl` per export Excel
- Versioni specificate in `requirements.txt`

#### Struttura File
- Creati 4 nuovi moduli Python
- Aggiunto `run.sh` per avvio facile
- Aggiunto `CHANGELOG.md`
- Migliorato `.gitignore`
- Aggiornato `README.md` con documentazione completa

### 🐛 Correzioni

- Risolto problema con colonna "position" su database esistenti
- Migliorata gestione date con parsing robusto
- Corretta validazione URL
- Risolto crash su tabella vuota
- Migliorata gestione errori database

### 📚 Documentazione

- README completamente riscritto con:
  - Sezioni organizzate con emoji
  - Guida all'uso dettagliata
  - Struttura progetto
  - Note tecniche
  - Troubleshooting
- Aggiunto CHANGELOG
- Docstrings su tutte le funzioni
- Commenti inline dove necessario

---

## [1.1.1] - 2025-12-06

### Aggiunte
- Colonna "Posizione" per tracciare dove si trova il materiale
- Sidebar collassabile

### Miglioramenti
- Design sidebar migliorato
- Icone sui pulsanti

---

## [1.0.0] - 2025-12-05

### Versione Iniziale
- Gestione ordini base
- Allarmi visivi colorati
- Notifiche popup per scaduti
- Database SQLite
- Interfaccia PyQt6
