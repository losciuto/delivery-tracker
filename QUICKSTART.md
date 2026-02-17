# 🚀 Guida Rapida - Delivery Tracker v2.0.1

## ⚡ Avvio Rapido

### Su Linux con GUI

```bash
# 1. Naviga nella directory del progetto
cd /home/massimo/Documenti/Massimo/ProgettiAntigravity/delivery-tracker

# 2. Attiva l'ambiente virtuale
source venv/bin/activate

# 3. Avvia l'applicazione
python main.py
```

### Usando lo Script di Avvio

```bash
./run.sh
```

---

## 📋 Requisiti Sistema

### Librerie Sistema (Linux)
Se l'applicazione non si avvia con errore Qt platform plugin, installa:

```bash
# Ubuntu/Debian
sudo apt-get install libxcb-cursor0 libxcb-xinerama0

# Fedora/RHEL
sudo dnf install xcb-util-cursor

# Arch
sudo pacman -S xcb-util-cursor
```

### Python
- Python 3.8 o superiore
- pip (package manager)

---

## 🎯 Prima Esecuzione

1. **Avvia l'applicazione** - Verrà creato automaticamente:
   - Database `delivery_tracker.db`
   - Directory `logs/`
   - Directory `backups/`

2. **Esplora la Dashboard** - Visualizza statistiche (inizialmente vuote)

3. **Aggiungi il primo ordine**:
   - Click su "Aggiungi" nella sidebar
   - Compila i campi obbligatori (Piattaforma e Descrizione)
   - Salva

4. **Configura le Impostazioni**:
   - Click su "Impostazioni" nella sidebar
   - Scegli il tema preferito
   - Configura notifiche e backup
   - Salva (riavvia per applicare il tema)

---

## 🎨 Funzionalità Principali

### Dashboard
- **Visualizza**: Click su "Dashboard" nella sidebar
- **Statistiche**: Totale, Pendenti, Consegnati, Scaduti
- **Grafici**: Distribuzione piattaforme e stato consegne

### Gestione Ordini
- **Aggiungi**: Sidebar → "Aggiungi" o Menu File → Nuovo
- **Modifica**: Doppio click su un ordine
- **Elimina**: Seleziona ordine → Click "Elimina"
- **Segna Consegnato**: Click destro → "Segna come Consegnato"

### Ricerca e Filtri
- **Ricerca**: Digita nella barra di ricerca in alto
- **Filtra per Piattaforma**: Dropdown "Piattaforma"
- **Filtra per Categoria**: Dropdown "Categoria"
- **Nascondi Consegnati**: Deseleziona checkbox

### Export Dati
- **Menu File → Esporta**:
  - Excel (.xlsx) - Con formattazione colori
  - CSV (.csv) - Compatibilità universale
  - JSON (.json) - Backup completo

### Import Dati
- **Menu File → Importa → Importa JSON**
- Seleziona file JSON precedentemente esportato

### Backup
- **Automatico**: All'uscita dell'applicazione (se abilitato)
- **Manuale**: Impostazioni → "Crea Backup Ora"
- **Ripristino**: Copia file da `backups/` a `delivery_tracker.db`

---

## 🎨 Personalizzazione

### Cambiare Tema
1. Impostazioni → Tema → Seleziona "Chiaro" o "Scuro"
2. Salva
3. Riavvia l'applicazione

### Configurare Notifiche
1. Impostazioni → Notifiche
2. Abilita/Disabilita
3. Imposta giorni anticipo (default: 2)

### Aggiungere Categorie
Le categorie predefinite sono:
- Elettronica
- Abbigliamento
- Casa
- Libri
- Sport
- Giocattoli
- Alimentari
- Altro

Puoi digitare nuove categorie direttamente nel campo "Categoria" quando aggiungi/modifichi un ordine.

---

## 🔍 Shortcuts Tastiera

| Azione | Shortcut |
|--------|----------|
| Nuovo Ordine | Ctrl+N (futuro) |
| Modifica | Doppio Click |
| Elimina | Canc (futuro) |
| Ricerca | Ctrl+F (futuro) |
| Aggiorna | F5 (futuro) |

---

## 🐛 Risoluzione Problemi

### L'applicazione non si avvia

**Problema**: Errore "Qt platform plugin"
```bash
qt.qpa.plugin: Could not load the Qt platform plugin "xcb"
```

**Soluzione**:
```bash
# Ubuntu/Debian
sudo apt-get install libxcb-cursor0 libxcb-xinerama0

# Verifica installazione Qt
./venv/bin/python -c "from PyQt6.QtWidgets import QApplication; print('Qt OK')"
```

### Errore import moduli

**Problema**: `ModuleNotFoundError`

**Soluzione**:
```bash
# Reinstalla dipendenze
./venv/bin/pip install -r requirements.txt
```

### Database corrotto

**Problema**: Errori durante operazioni database

**Soluzione**:
```bash
# Opzione 1: Ripristina da backup
cp backups/backup_YYYYMMDD_HHMMSS.db delivery_tracker.db

# Opzione 2: Ricrea database (PERDI DATI!)
rm delivery_tracker.db
python main.py  # Ricreerà il database vuoto
```

### Grafici non visualizzati

**Problema**: Dashboard senza grafici

**Soluzione**:
```bash
# Verifica PyQt6-Charts
./venv/bin/pip install --upgrade PyQt6-Charts
```

---

## 📊 Interpretazione Colori

### Tabella Ordini
- **Verde Chiaro**: Ordine consegnato ✅
- **Rosso Chiaro**: Consegna scaduta ⚠️
- **Arancione**: Consegna prevista oggi 📅
- **Giallo**: Consegna in arrivo (entro 2 giorni) ⏰
- **Bianco**: Consegna futura (oltre 2 giorni)

### Dashboard
- **Blu**: Totale ordini
- **Arancione**: In attesa
- **Verde**: Consegnati
- **Rosso**: Scaduti

---

## 💡 Suggerimenti

### Best Practices
1. **Backup Regolari**: Abilita backup automatico nelle impostazioni
2. **Categorie Consistenti**: Usa sempre le stesse categorie per filtri efficaci
3. **Note Dettagliate**: Aggiungi note per difformità o problemi
4. **Link Prodotti**: Inserisci sempre il link per riferimento rapido
5. **Posizione Fisica**: Specifica dove si trova il materiale

### Workflow Consigliato
1. **Nuovo Ordine**: Aggiungi subito dopo l'acquisto
2. **Monitoraggio**: Controlla dashboard giornalmente
3. **Aggiornamento**: Segna come consegnato appena arriva
4. **Pulizia**: Nascondi consegnati per focus sui pendenti
5. **Export**: Esporta mensilmente per archivio

---

## 📁 Struttura Directory

```
delivery-tracker/
├── venv/                    # Ambiente virtuale Python
├── logs/                    # File di log giornalieri
│   └── app_2026-02-17.log
├── backups/                 # Backup automatici database
│   └── backup_20260217_171500.db
├── delivery_tracker.db      # Database principale
├── settings.json            # Impostazioni utente
└── [file Python...]
```

---

## 🔄 Aggiornamenti Futuri

### Roadmap v2.1.0
- [ ] Supporto allegati (immagini, PDF)
- [ ] Notifiche desktop native
- [ ] Grafici aggiuntivi (trend temporali)
- [ ] Export PDF con report
- [ ] Multi-lingua (EN, ES, FR)
- [ ] Sincronizzazione cloud
- [ ] App mobile companion

---

## 📞 Supporto

### Problemi o Domande?
1. Controlla questa guida
2. Leggi `README.md` per documentazione completa
3. Consulta `CHANGELOG.md` per novità
4. Apri una issue su GitHub

### Log Files
I log si trovano in `logs/app_YYYY-MM-DD.log` e contengono informazioni dettagliate su tutte le operazioni.

---

## 🎓 Risorse Aggiuntive

- **README.md**: Documentazione completa
- **CHANGELOG.md**: Storia modifiche
- **IMPROVEMENTS.md**: Dettaglio miglioramenti v2.0.1
- **LICENSE**: Licenza GPL-3.0

---

**Buon tracciamento! 📦✨**

*Per qualsiasi problema, controlla i log in `logs/` per dettagli tecnici.*
