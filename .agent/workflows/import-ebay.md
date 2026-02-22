---
description: Estrai ordini da URL eBay e genera Excel per il Tracker
---

# 🤖 Workflow: Importazione Ordine eBay

Usa questo workflow quando l'utente fornisce un URL o si trova sulla pagina degli ordini eBay (es. `https://www.ebay.it/mye/myebay/purchase`).

## Passaggi del Workflow

1. **Accesso e Navigazione**:
   - Apri l'URL fornito dall'utente.
   - Attendi il caricamento completo della pagina degli acquisti.
   - Assicurati che gli ordini da importare siano visibili a schermo.

2. **Estrazione Dati (IA Scraping)**:
   - Identifica i blocchi dei singoli ordini tramite il selettore `.m-ph-card.m-order-card`.
   - Per ogni ordine/prodotto, estrai:
     - `order_date`: Data dell'ordine (letto dopo la dicitura "Data dell'ordine:").
     - `site_order_id`: Numero ordine (letto dopo "Numero ordine:").
     - `description`: Nome completo del prodotto (dentro `a.nav-link`).
     - `seller`: Nome del venditore (dentro link `a[href*="/usr/"]`, rimuovendo "ID utente").
     - `price`: Prezzo totale dell'ordine (letto dopo "Totale ordine:", convertirlo in numero).
     - `quantity`: Quantità (valore base 1 se non specificato altrimenti).
     - `status`: Stato attuale (prima riga di testo del blocco o dentro `.m-ph-card__header-text`).
     - `image_url`: Estrai l'attributo `src` dell'immagine del prodotto (solitamente dentro `img.m-order-card__img` o simile).
     - `link`: URL del prodotto (dall'attributo `href` di `a.nav-link`).

3. **Generazione Excel**:
   - Crea un file Excel (`.xlsx`) compatibile con l'app Delivery Tracker.
   - Intestazioni richieste: `Data dell'ordine`, `Piattaforma`, `ID Ordine`, `Venditore`, `Descrizione`, `Prezzo Prodotto (EUR)`, `Quantità`, `Immagine`, `Link`, `Stato`, `Numero di Tracking`, `Consegna Stimata`, `Destinazione`, `Vettore`, `Ultimo Miglio`.
   - Normalizza i prezzi come numeri (float) e usa `eBay` come piattaforma.
   - **Nota**: L'app ora gestisce automaticamente le immagini in formato `.webp` o `.avif` convertendole in PNG compatibili durante l'importazione.

4. **Consegna**:
   - Conferma all'utente il numero di articoli estratti.
   - Fornisce il nome del file Excel generato per l'importazione.
