import os
import sys
from bs4 import BeautifulSoup
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment

def parse_ebay_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    orders = []

    # Seleziona tutte le card degli ordini
    cards = soup.select('.m-ph-card.m-order-card')

    for card in cards:
        info_text = card.get_text(separator='\n', strip=True)
        lines = [line.strip() for line in info_text.split('\n') if line.strip()]

        def extract_label(label_text):
            for i, line in enumerate(lines):
                if label_text in line and i + 1 < len(lines):
                    return lines[i + 1]
            return ""

        # Estrazione Dati
        data_ordine = extract_label("Data dell'ordine:")
        totale = extract_label("Totale ordine:")
        numero_ordine = extract_label("Numero ordine:")
        stato = lines[0] if lines else "N/D"

        # Estrazione Titoli
        title_els = card.select('a.nav-link')
        for title_el in title_els:
            descrizione = title_el.get_text(strip=True)
            
            # Estrazione Venditore
            seller_el = card.select_one('a[href*="/usr/"]')
            venditore = seller_el.get_text(strip=True).replace("ID utente", "").replace("\u00a0", "").strip() if seller_el else "N/D"

            # Conversione formato totale per Excel
            prezzo = 0.0
            if totale:
                try:
                    totale_str = totale.replace('EUR', '').replace('€', '').replace(',', '.').strip()
                    prezzo = float(totale_str)
                except ValueError:
                    pass

            order_data = [
                data_ordine,
                "eBay",
                numero_ordine,
                venditore,
                descrizione,
                prezzo,
                1, # Quantità fissa 1, eventuale parsing avanzato per qt
                "", # Immagine non ancora estratta
                "", # Link non ancora estratto
                stato,
                "", # Numero di Tracking da estrarre (spesso non in questa pagina)
                data_ordine, # Consegna Stimata (Fallback alla data ordine)
                "", # Destinazione
                "Poste Italiane", # Vettore default
                "Poste Italiane" # Ultimo Miglio default
            ]
            orders.append(order_data)

    return orders

def generate_excel(html_filepath, output_filename):
    if not os.path.exists(html_filepath):
        print(f"Errore: Il file {html_filepath} non esiste.")
        return

    with open(html_filepath, 'r', encoding='utf-8') as f:
        html_content = f.read()

    parsed_orders = parse_ebay_html(html_content)

    if not parsed_orders:
        print("Nessun ordine trovato o errore nel parsing del file HTML.")
        return

    wb = Workbook()
    ws = wb.active
    ws.title = "eBay Orders"

    headers = ["Data dell'ordine", "Piattaforma", "ID Ordine", "Venditore", "Descrizione", 
               "Prezzo Prodotto (EUR)", "Quantità", "Immagine", "Link", "Stato", 
               "Numero di Tracking", "Consegna Stimata", "Destinazione", "Vettore", "Ultimo Miglio"]
    
    ws.append(headers)

    for row_data in parsed_orders:
        ws.append(row_data)

    # Styling headers
    header_font = Font(bold=True)
    for cell in ws[1]:
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    # Adjust column widths
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if cell.value and len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        ws.column_dimensions[column].width = min(max_length + 2, 50)

    wb.save(output_filename)
    print(f"File '{output_filename}' generato con i dati degli ordini eBay!")
    print(f"Totale articoli estratti: {len(parsed_orders)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python generate_ebay_excel.py <percorso_file_html> [file_output_xlsx]")
        sys.exit(1)
        
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "ebay_orders_import.xlsx"
    
    generate_excel(input_file, output_file)
