# Direttive di Estrazione Dati: Temu Order Details

Queste direttive descrivono la logica utilizzata dall'IA per analizzare e strutturare i dati dalle pagine dei dettagli ordine di Temu.

## 1. Identificazione Ordine
- **Selettore ID Ordine**: Cerca elementi contenenti la stringa "ID ordine" o "Order ID". Spesso associato a selettori come `[class*="orderId"]` o `[class*="parent_order_sn"]`.
- **Data Ordine**: Solitamente situata vicino all'ID ordine o sotto l'intestazione principale.

## 2. Struttura Articoli (Container)
Gli articoli sono solitamente raggruppati in una lista. Ogni articolo è contenuto in un blocco ripetitivo (es. `div` con classi come `[class*="goodsItem"]` o `[class*="orderItem"]`).

> [!IMPORTANT]
> **Condizione di Stop**: La lista degli articoli dell'ordine termina tassativamente alla dicitura **"Dettagli del pagamento"**. Tutto ciò che compare sotto (es. "Prodotti consigliati") deve essere ignorato.

## 3. Estrazione Campi per Articolo
Per ogni "container" identificato, vengono estratti i seguenti campi:

| Campo | Logica di Estrazione / Selettori |
|---|---|
| **Descrizione** | Testo contenuto nei tag `span` o `a` che descrivono il prodotto. Selettori comuni: `[class*="goodsName"]`, `[class*="title"]`. |
| **Prezzo** | Elemento contenente il simbolo valuta (€). Viene normalizzato rimuovendo il simbolo e convertendo la virgola in punto per il database. |
| **Quantità** | Testo preceduto da "x" o contenuto in label come "Qtà". Selettori: `[class*="quantity"]`, `[class*="count"]`. |
| **Img. URL** | Attributo `src` del tag `img` principale dell'articolo. Viene cercato l'URL con la risoluzione più alta disponibile. |
| **Link Prodotto** | Attributo `href` del tag `a` che avvolge l'immagine o il titolo dell'articolo. Deve essere un link assoluto alla scheda prodotto. |

## 4. Logica di Parsing Avanzata
- **Lazy Loading**: Scorrere la pagina (scroll) per forzare il caricamento delle immagini e dei prezzi degli articoli in fondo alla lista (specialmente per ordini con molti articoli, es. 55+).
- **Rilevamento Tracking**: Cercare bottoni con testo "Traccia" o "Track". Il numero di tracking viene estratto dalla pagina di tracciamento o dal tooltip associato.
- **Normalizzazione Valuta**: I prezzi vengono puliti da caratteri non numerici per permettere calcoli matematici nell'applicazione.

## 5. Esempio di Schema JSON Prodotto
```json
{
  "description": "Nome Prodotto...",
  "price": 12.50,
  "quantity": 1,
  "image_url": "https://img.kwcdn.com/...",
  "link": "https://www.temu.com/product-link..."
}
```
