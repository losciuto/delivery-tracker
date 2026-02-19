# Changelog

Tutte le modifiche importanti a questo progetto saranno documentate in questo file.

Il formato è basato su [Keep a Changelog](https://keepachangelog.com/it/1.0.0/),
e questo progetto aderisce al [Semantic Versioning](https://semver.org/lang/it/).
## [2.5.0] - 2026-02-19
### 🚀 Ottimizzazioni di Performance
- **Lookup Duplicati O(1)**: Ridisegnata la logica di ricerca duplicati utilizzando mappe di hash (indici in memoria) per ID Ordine e Tracking. Questo riduce drasticamente i tempi di importazione per file di grandi dimensioni.
- **Atomic Merge**: Ottimizzata la funzione di unione dati per evitare scritture ridondanti sul database se non vengono rilevati cambiamenti reali.
- **Refactoring TextMatcher**: Centralizzata la logica di confronto fuzzy e tokenizzazione in un modulo core (`utils.py`) per una maggiore coerenza e manutenibilità.

### ✨ Miglioramenti UI & UX
- **Analisi Somiglianza nel Tooltip**: Il dialogo di importazione ora mostra la percentuale esatta di somiglianza testuale calcolata per ogni articolo duplicato, offrendo maggiore trasparenza sulle decisioni del "Best-Match".

### 🔧 Robustezza
- **Smart Date Parser**: Implementato un parser di date intelligente capace di interpretare formati internazionali, date in linguaggio naturale (IT/EN) e variazioni di separatori.

## [2.4.0] - 2026-02-19
### ✨ Aggiunte
- **Merge Intelligente Duplicati**: Nuova funzionalità per unire dati da file esterni in ordini già presenti nel database.
    - Riempie automaticamente solo i campi vuoti (prezzo, immagine, link) mantenendo le informazioni esistenti.
- **Logica "Best-Match" Multi-Articolo**: Sistema avanzato per la gestione di ordini contenenti più prodotti.
    - Identifica il prodotto corretto all'interno dello stesso ID ordine tramite confronto testuale delle descrizioni.
    - Utilizza la **tokenizzazione** (intersezione di parole chiave) per gestire titoli troncati o leggermente diversi.
- **Ricerca Duplicati Potenziata**: La ricerca ora include descrizioni simili come criterio di fallback quando Site ID o Tracking non sono disponibili.

### 🔧 Fix & Miglioramenti
- Risolto bug che sovrascriveva erroneamente gli articoli di uno stesso ordine multi-prodotto durante l'importazione.
- Migliorato il parsing delle date per gli ordini Temu importati.

## [2.3.0] - 2026-02-19
### ✨ Aggiunte
- **Piattaforma d'Importazione Universale**: Nuova gestione avanzata dell'importazione che sostituisce i vecchi metodi.
    - Supporto per **Excel (.xlsx, .xls)**, **CSV** e **JSON**.
    - **Analisi Automatica**: Il file viene processato istantaneamente al momento della selezione.
    - **Dialogo di Anteprima**: Visualizzazione completa dei dati estratti prima dell'inserimento nel database.
    - **Detezione Duplicati**: Identificazione automatica degli ordini già presenti (tramite Site ID o Tracking) con evidenziazione visiva e pre-deselezione.
- **Dati Prodotto Avanzati**:
    - Nuovi campi database per **Prezzo** e **Immagine Prodotto**.
    - Visualizzazione miniature e prezzi (formattati in €) nella tabella principale.
    - Link alle immagini cliccabili per apertura rapida nel browser.
- **Scraping IA Temu**:
    - Procedura guidata tramite IA per l'estrazione perfetta degli ordini da Temu (escluso materiale pubblicitario).
    - Generazione automatica di file Excel pronti per l'importazione.
    - Nuovo workflow di automazione: `/import-temu`.

### 🎨 UI & UX
- **Semplificazione Sidebar & Menu**: Rimozione delle opzioni obsolete "Importa HTML" e "Importa da URL" per un'esperienza utente più pulita e focalizzata sui file.
- **Stabilità**: Migrazioni automatiche del database per supportare i nuovi campi senza perdita di dati.

## [2.2.1] - 2026-02-19
### 🎨 UI & UX
- **Ottimizzazione Monitor 19"**: Ridotte le dimensioni minime della finestra e gli spazi verticali nella sidebar per una migliore visualizzazione su schermi piccoli.
- **Riorganizzazione Sidebar**: 
    - Pulsante "Aggiorna" spostato subito dopo "Aggiungi" per un accesso più rapido.
    - Pulsanti "Importa HTML" e "Importa da URL" spostati alla fine della sezione AZIONI.
    - Rimossi i pulsanti "Impostazioni" e "Info" dalla sidebar per pulizia visiva (accessibili dal menu superiore).

## [2.2.0] - 2026-02-18
### ✨ Aggiunte
- **Email Sync 2.0**:
    - Scansione dinamica basata sulle piattaforme attive nel database per una maggiore efficienza.
    - Supporto ottimizzato per nuove piattaforme, inclusa **Too Good To Go**.
    - Estrazione ID Temu migliorata con supporto per lunghezze variabili (15-20 cifre).
    - Logica "Smart State": priorità all'oggetto dell'email e riconoscimento intelligente delle conferme d'ordine per evitare stati errati.
- **UI & UX**:
    - **Raggruppamento Ordini**: Evidenziazione visiva dinamica degli articoli appartenenti allo stesso ordine del sito.
    - **Indicatore Visivo**: Aggiunta icona 🔗 nella colonna ID Ordine per identificare ordini multipli.
    - **Duplicazione Ordini**: Nuova funzione "Duplica" per copiare rapidamente ordini esistenti.
    - Ordinamento LIFO (Last-In-First-Out) come impostazione predefinita per la visualizzazione.
    - Alfabetizzazione automatica delle liste di piattaforme e categorie (mantenendo "Altro" alla fine).

### 🔧 Fix & Miglioramenti
- **Temu Parser**: Implementata logica di "Section Isolation" (scraping) per escludere correttamente suggerimenti e articoli consigliati dall'estrazione dell'ordine.
- **Priorità Estrazione**: Gli ID Ordine specifici delle piattaforme hanno ora la precedenza sul tracking generico per evitare sovrapposizioni.
- **Stabilità Email**: Risolti bug critici come `UnboundLocalError` e `NameError` durante la sincronizzazione.
- **Filtraggio Cartelle**: Restrizione dei criteri di scansione IMAP per escludere sottocartelle personali e focalizzarsi solo su Inbox e piattaforme rilevanti.
- **UI**: Corretta l'evidenziazione delle righe durante il raggruppamento per evitare conflitti visivi con gli allarmi di scadenza.

## [2.1.1] - 2026-02-18
### 🔧 Fix
- **Impostazioni**: Abilitata la modifica manuale del campo "Account Collegato" (email) per una maggiore flessibilità, aggiungendo un tooltip informativo.

## [2.1.0] - 2026-02-17
### ✨ Aggiunte
- **ID Ordine Sito**: Nuovo campo per tracciare l'ID dell'ordine direttamente dal sito del venditore (es. Amazon, eBay).
- **Gestione Stati Dinamica**: Introdotta la colonna "Stato" con colorazione condizionale (In Attesa, Spedito, In Transito, In Consegna, Consegnato, Problema).
- **Sincronizzazione Email Pro**:
    - Estrazione automatica dello stato e del Site Order ID dai testi delle email.
    - Supporto multilingua completo (Italiano/Inglese) per le notifiche di spedizione.
    - Logica di matching potenziata: priorità a Tracking > ID Ordine > Descrizione.

### 🔧 Ottimizzazioni & Fix
- **Stabilità IMAP**: Ottimizzata la scansione delle cartelle (limitata alle 15 più rilevanti) per evitare disconnessioni dai server Outlook/Hotmail.
- **Ricerca Intelligente**: Passaggio alla ricerca IMAP per data (`SINCE`) per una maggiore compatibilità e velocità.
- **Logging**: Aggiunto logging dettagliato `EMAIL-SYNC` per il debug del matching in tempo reale.
- **Bug Fix**: Corretta l'indentazione nella logica di estrazione che impediva il salvataggio degli aggiornamenti in alcuni casi.
- **UI**: Corretto un `AttributeError` nel dialogo dell'ordine relativo al campo link.

### ✨ Aggiunte
- **Tema Dinamico**: Implementazione del cambio tema (Luce/Buio) in tempo reale senza riavvio.
- **UI Intelligente**: Dimensionamento dinamico della finestra basato sulla risoluzione dello schermo.
- **UX**: Centratura automatica della finestra all'avvio.

### 🔧 Ottimizzazioni
- Migliorato il sistema di refresh della tabella per evitare aggiornamenti ridondanti.
- Ottimizzata la gestione delle larghezze delle colonne per monitor standard.

## [2.0.1] - 2026-02-17
 
### ✨ Modifiche
- **Fix**: Risolto problema dipendenza mancante (`PyQt6-Charts`) che impediva l'avvio
- **UI**: Aggiornate icone sidebar con versioni più intuitive (Home, Cartella, File, Computer)
- **Docs**: Aggiornata documentazione e numeri di versione

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
