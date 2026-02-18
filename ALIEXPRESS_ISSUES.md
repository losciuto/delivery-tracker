# Analisi Criticità Parsing AliExpress

Il tentativo di implementare un parser AliExpress basato su sorgente HTML e Regular Expressions ha evidenziato limiti strutturali che rendono l'approccio attuale non affidabile per un ambiente di produzione. Di seguito sono elencate le parti non funzionanti e le ragioni tecniche del fallimento.

## Parti Non Funzionanti / Da Completare

### 1. Estrazione Articoli (Noise Filtering)
L'estrazione degli articoli cattura spesso "rumore" (prodotti consigliati, sponsorizzati o visti di recente) invece degli articoli effettivamente ordinati. 
- **Problema**: AliExpress utilizza classi CSS dinamiche e offuscate. Non esiste un "container" univoco e stabile che separi gli articoli acquistati da quelli suggeriti.
- **Conseguenza**: Il sistema può importare 10-15 articoli errati per ogni ordine reale.

### 2. Estrazione Tracking Number
Il numero di tracking è spesso assente dal sorgente HTML statico della pagina di riepilogo o dettaglio, oppure è caricato tramite chiamate API asincrone dopo il caricamento della pagina.
- **Problema**: I tentativi di estrarre codici come `RTZ...` o simili funzionano solo se il dato è presente nel testo o in blocchi JSON iniettati, cosa che non avviene in tutte le varianti della pagina AliExpress.

### 3. Struttura HTML Variabile
AliExpress serve versioni diverse della stessa pagina a seconda dell'utente, del browser e della sessione (A/B testing).
- **Problema**: I pattern regex sviluppati per una sessione non corrispondono alla struttura HTML di un'altra.

## Ragioni del Fallimento dell'Approccio

L'approccio basato su **HTML Scraping + Regex** è considerato **NON VALIDO** per AliExpress per i seguenti motivi:
1. **Dinamismo Eccessivo**: La pagina è quasi interamente renderizzata via JavaScript. Il sorgente HTML (Ctrl+U) spesso contiene solo scheletri e script minificati, rendendo impossibile una ricerca testuale affidabile.
2. **Offuscamento**: Molti dati sensibili (ID, nomi) sono inseriti in strutture JSON annidate o codificate che cambiano chiave frequentemente.

## Proposta per il Completamento (Approccio Alternativo)

Per rendere AliExpress funzionante al 100%, l'architettura dovrebbe evolvere verso:
1. **Browser Extension**: Una piccola estensione per Chrome/Firefox che estragga i dati direttamente dal DOM "vivo" mentre l'utente è loggato, inviandoli all'app.
2. **Integrazione API**: Se possibile, utilizzare API ufficiali o semi-ufficiali (sebbene AliExpress sia molto restrittivo).
3. **Headless Browser**: Utilizzare strumenti come Playwright per simulare una navigazione reale, ma questo comporterebbe problemi di autenticazione e anti-bot.

---
*Documento generato per evidenziare le lacune nel supporto AliExpress attuale.*
