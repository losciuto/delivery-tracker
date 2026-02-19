# 🕵️ Soluzioni di Scraping e Importazione Dati

Questo documento analizza le diverse strategie implementate e potenziali per l'estrazione dati dai siti di e-commerce (Temu, AliExpress, Amazon, ecc.) e la loro integrazione nel Delivery Tracker.

## 1. Approccio Assistito (IA Subagent)
*Attualmente implementato tramite workflow `/import-temu`*

**Come funziona:**
L'utente fornisce un URL dell'ordine. Un agente IA (Antigravity/Subagent) apre un browser sicuro, analizza il DOM, estrae i dati e genera un file Excel compatibile.

**Vantaggi:**
- **Alta Precisione**: L'IA può interpretare layout complessi e cambiamenti dinamici del DOM.
- **Gestione Auth**: Supera i sistemi anti-bot e i captcha che bloccano gli scraper automatizzati "puri".
- **Zero Installazione**: L'utente non deve installare nulla sul proprio computer locale.

**Svantaggi:**
- **Manuale**: Richiede l'interazione con l'agente per ogni nuovo ordine.

---

## 2. Estensione Browser (Potenziale)
**Come funziona:**
Una piccola estensione per Chrome/Firefox aggiunge un pulsante "Esporta per Tracker" direttamente nelle pagine dell'ordine.

**Vantaggi:**
- **Integrazione Nativa**: Molto più veloce per l'utente finale.
- **Accesso Sessione**: Utilizza i cookie del browser dell'utente (nessun problema di login).

**Svantaggi:**
- **Manutenzione**: Ogni modifica al sito del venditore richiede l'aggiornamento dell'estensione.
- **Privacy**: Richiede permessi di lettura sulle pagine visitate.

---

## 3. Script Locale (Selenium / Playwright)
**Come funziona:**
Uno script Python integrato nell'app che automatizza il browser locale.

**Vantaggi:**
- **Automazione Totale**: Possibilità di sincronizzare tutti gli ordini con un clic.

**Svantaggi:**
- **Fragilità**: Facilmente bloccato dai sistemi anti-scraping (Shadow DOM, Canvas fingerprinting).
- **Setup**: Richiede driver browser installati correttamente sul sistema dell'utente.

---

## 4. Tampermonkey / Userscript
**Come funziona:**
Uno script JavaScript eseguito tramite estensioni come Tampermonkey direttamente nel browser.

**Vantaggi:**
- **Leggero**: Semplice da scrivere e modificare.
- **Esportazione Diretta**: Può generare file JSON o Excel scaricabili dal browser.

**Svantaggi:**
- **UX**: Richiede all'utente di installare un gestore di script e lo script stesso.

---

## Conclusioni
L'approccio attuale basato su **Workflow Assistito** è il più robusto contro i cambiamenti dei siti e i blocchi bot. Lo sviluppo futuro potrebbe prevedere un **Userscript (Tampermonkey)** come soluzione intermedia per utenti avanzati che desiderano esportazioni rapide senza passare dall'IA.
