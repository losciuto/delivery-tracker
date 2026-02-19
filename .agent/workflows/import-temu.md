---
description: Estrai ordini da URL Temu e genera Excel per il Tracker
---

# 🤖 Workflow: Importazione Ordine Temu

Usa questo workflow quando l'utente fornisce un URL di un dettaglio ordine Temu (es. `https://www.temu.com/bgt_order_detail.html?...`).

## Passaggi del Workflow

1. **Accesso e Navigazione**:
   - Apri l'URL fornito dall'utente.
   - Se compare un modal di login, prova a leggere i dati in sottofondo o interagisci se necessario.

2. **Estrazione Dati (IA Scraping)**:
   - Identifica la lista prodotti.
   - **CRITICO**: Fermati non appena trovi la dicitura **"Dettagli del pagamento"**. Tutto ciò che segue è pubblicità o raccomandazioni e deve essere ignorato.
   - Per ogni prodotto (max 9-10 solitamente, a meno di ordini multipli), estrai:
     - `description`: Nome completo del prodotto.
     - `price`: Prezzo unitario (es. "5,44€").
     - `quantity`: Quantità (intero).
     - `image_url`: URL assoluto dell'immagine.
     - `link`: URL della scheda prodotto (prendi l'href dal titolo o dall'immagine).

3. **Generazione Excel**:
   - Crea un file Excel (`.xlsx`) compatibile con l'app Delivery Tracker.
   - Intestazioni richieste: `Data dell'ordine`, `Piattaforma`, `ID Ordine`, `Descrizione`, `Prezzo Prodotto (EUR)`, `Quantità`, `Immagine`, `Link`, `Stato`.
   - Normalizza i prezzi come numeri (float) e usa `Temu` come piattaforma.

4. **Consegna**:
   - Conferma all'utente il numero di articoli estratti.
   - Fornisce il nome del file Excel generato.
