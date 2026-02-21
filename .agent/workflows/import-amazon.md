---
description: Estrai ordini da URL Amazon e genera Excel per il Tracker
---

# 🤖 Workflow: Importazione Ordine Amazon

Usa questo workflow quando l'utente fornisce un URL della pagina degli ordini Amazon (es. `https://www.amazon.it/your-orders/orders?ref_=nav_orders_first`).

## Passaggi del Workflow

1. **Accesso e Navigazione**:
   - Apri l'URL fornito dall'utente tramite `browser_subagent`.
   - Se richiesto un login, avvisa l'utente che non è possibile procedere senza una sessione attiva.
   - **IMPORTANTE**: Scorri (scroll) l'intera pagina fino in fondo per assicurarti che tutti gli ordini visibili siano stati caricati dal sistema di paginazione/lazy-loading di Amazon.

2. **Estrazione Dati (IA Scraping)**:
   - Identifica i blocchi dei singoli ordini nella pagina "I miei ordini".
   - Per ogni ordine/prodotto, estrai:
     - `order_date`: Data dell'ordine (es. "18 febbraio 2026").
     - `site_order_id`: ID Ordine (es. `407-0587852-0014744`).
     - `description`: Nome completo del prodotto.
     - `seller`: Nome del venditore.
     - `price`: Prezzo unitario come numero.
     - `quantity`: Quantità (intero).
     - `status`: Stato attuale (es. "Consegnato 20 febbraio").
     - `image_url`: URL assoluto dell'immagine del prodotto.
     - `link`: URL della scheda prodotto.

3. **Generazione Excel**:
   - Crea un file Excel (`amazon_orders_import.xlsx`) compatibile con l'app Delivery Tracker.
   - Intestazioni richieste: `Data dell'ordine`, `Piattaforma`, `ID Ordine`, `Venditore`, `Descrizione`, `Prezzo Prodotto (EUR)`, `Quantità`, `Immagine`, `Link`, `Stato`.
   - Mappa i valori inserendo `Amazon` come piattaforma.

4. **Consegna**:
   - Conferma all'utente il numero di articoli estratti.
   - Indica il nome del file Excel generato (`amazon_orders_import.xlsx`).
