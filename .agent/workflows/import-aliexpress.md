---
description: Estrai ordini da URL AliExpress e genera Excel per il Tracker
---

# 🤖 Workflow: Importazione Ordine AliExpress

Usa questo workflow quando l'utente fornisce un URL di un dettaglio ordine o della lista ordini AliExpress (es. `https://www.aliexpress.com/p/order/index.html`).

## Passaggi del Workflow

1. **Accesso e Navigazione**:
   - Apri l'URL fornito dall'utente.
   - Attendi il caricamento completo della pagina degli ordini.
   - Se necessario, gestisci eventuali banner di consenso o login.

2. **Estrazione Dati (IA Scraping)**:
   - Identifica i blocchi dei singoli ordini.
   - Per ogni ordine/prodotto, estrai:
     - `order_date`: Data dell'ordine (es. "Feb 17, 2026").
     - `site_order_id`: ID Ordine (es. `3068779692983676`).
     - `description`: Nome completo del prodotto.
     - `seller`: Nome del venditore. **NOTA**: Si trova all'interno del tag con classe `order-item-store-name`.
     - `price`: Prezzo unitario (es. "5,59€").
     - `quantity`: Quantità (intero).
     - `status`: Stato attuale (es. "Awaiting delivery", "Completed").
     - `image_url`: URL assoluto dell'immagine del prodotto.
     - `link`: URL dello screenshot o della scheda prodotto.

3. **Generazione Excel**:
   - Crea un file Excel (`.xlsx`) compatibile con l'app Delivery Tracker.
   - Intestazioni richieste: `Data dell'ordine`, `Piattaforma`, `ID Ordine`, `Venditore`, `Descrizione`, `Prezzo Prodotto (EUR)`, `Quantità`, `Immagine`, `Link`, `Stato`.
   - Normalizza i prezzi come numeri (float) e usa `AliExpress` come piattaforma.
   - Mappa i termini degli stati (es. "Completed" -> "Consegnato", "Awaiting delivery" -> "In attesa di consegna").

4. **Consegna**:
   - Conferma all'utente il numero di articoli estratti.
   - Indica il nome del file Excel generato (es. `aliexpress_orders_import.xlsx`).
