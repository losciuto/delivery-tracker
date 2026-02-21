from openpyxl import Workbook
from openpyxl.styles import Font, Alignment

# Data extracted from Amazon browser analysis WITH tracking details
orders_data = [
    ["Data dell'ordine", "Piattaforma", "ID Ordine", "Venditore", "Descrizione", "Prezzo Prodotto (EUR)", "Quantità", "Immagine", "Link", "Stato", "Numero di Tracking", "Consegna Stimata", "Destinazione", "Vettore", "Ultimo Miglio"],
    ["18 Feb 2026", "Amazon", "407-0587852-0014744", "Amazon.it", "LG 27U411A Monitor 27\" Full HD IPS, HDR 10, 120Hz, 1ms MBR, HDMI, D-Sub (VGA), Uscita cuffie, 1920x1080, sRGB 99%, Schermo Antiriflesso, Flicker Safe, Reader Mode, Nero", 99.99, 1, "https://m.media-amazon.com/images/I/71WOHAmf7ML._SS142_.jpg", "https://www.amazon.it/dp/B0FKNKDNXN", "Consegnato 20 febbraio", "950C40825844F", "20 febbraio", "Max Lo Sciuto Studio Cigna, Palermo, PA 90121", "Poste Italiane", "Poste Italiane"],
    ["14 Feb 2026", "Amazon", "404-5175867-9935545", "Mzhou", "MZHOU Scheda Adattatore PCI-E x1 a 4 USB, Scheda Splitter Segnale PCI-E, ASM1184e", 11.99, 1, "https://m.media-amazon.com/images/I/71qS7X2IUzL._SS142_.jpg", "https://www.amazon.it/dp/B097CYKM3L", "Ritirato 16 febbraio", "IT3220286422", "16 febbraio", "Amazon Counter - Putia e Cafè, Ficarazzi 90010", "Amazon", "Amazon"],
    ["09 Feb 2026", "Amazon", "407-7164831-9095558", "KOORUI", "KOORUI Monitor 27 Pollici Curvo (1500R), Full HD (1920x1080), VA, 144 Hz, 5 ms, HDMI, VGA, Gaming Monitor, Eye Saver Mode, Flicker Safe, Nero, 27N5CA", 120.31, 1, "https://m.media-amazon.com/images/I/71v1RkYl-wL._AC_AA200_.jpg", "https://www.amazon.it/dp/B0DK12LHLK", "Consegnato 12 febbraio", "IT3215575148", "12 febbraio", "Max Lo Sciuto Studio Cigna, Palermo, PA 90121", "Amazon", "Amazon"],
    ["09 Feb 2026", "Amazon", "407-7164831-9095558", "Kalea Informatique", "KALEA-INFORMATIQUE Scheda di espansione per convertire una porta PCI Express x1 in 4 porte PCIe x1 con chipset ASM1184e", 120.31, 1, "https://m.media-amazon.com/images/I/71H2O8S9hLL._AC_AA200_.jpg", "https://www.amazon.it/dp/B08XWN4T6B", "Consegnato 11 febbraio", "IT3214270376", "11 febbraio", "Max Lo Sciuto Studio Cigna, Palermo, PA 90121", "Amazon", "Amazon"],
    ["09 Feb 2026", "Amazon", "407-2290755-7841142", "Phoenix srl", "Lenovo, Pc Desktop Pronto All'Uso, Computer Pc Fisso Intel I5, Ram 8Gb, SSD 256Gb, Pacchetto Office 2021, W 11 Pro e Chiavetta WI-FI (Ricondizionato)", 165.00, 1, "https://m.media-amazon.com/images/I/71BBHC88DP._AC_AA200_.jpg", "https://www.amazon.it/dp/B0BBHC88DP", "Consegnato 13 febbraio", "3UW1S0T000298", "13 febbraio", "Max Lo Sciuto Studio Cigna, Palermo, PA 90121", "Poste Italiane", "Poste Italiane"],
    ["02 Feb 2026", "Amazon", "407-3655632-8711535", "SPES", "SPES - Tutore Spalla e Braccio Shoulder Block, Immobilizzatore Post Operatorio per Lussazione e Frattura Omero, Sostegno Ambidestro Regolabile - Taglia Unica, Nero", 39.00, 1, "https://m.media-amazon.com/images/I/71H-N3vGfHL._AC_AA200_.jpg", "https://www.amazon.it/dp/B0FPCZLY42", "Consegnato 3 febbraio", "IT3205976441", "3 febbraio", "Max Lo Sciuto Studio Cigna, Palermo, PA 90121", "Amazon", "Amazon"],
    ["11 Dic 2025", "Amazon", "404-0652287-6970750", "CARTUCCE E STAMPANTI", "DR2400 DR-2400 Unità Tamburo Compatibile per Brother MFC-L2710DN MFC-L2710DW MFC-L2730DW L2750DW DCP-L2510D DCP-L2530DW DCP-L2550DN L2537DW HL-L2310D HL-L2350DW HL-L2357DW HL-L2370DN L2375DW Stampante", 11.90, 6, "https://m.media-amazon.com/images/I/71r9w1wz9pL._AC_AA200_.jpg", "https://www.amazon.it/dp/B07L89R2HK", "Consegnato 19 dicembre", "", "19 dicembre", "Max Lo Sciuto Studio Cigna, Palermo, PA 90121", "", ""]
]

def generate_excel(filename):
    wb = Workbook()
    ws = wb.active
    ws.title = "Amazon Orders"

    # Add data
    for row in orders_data:
        ws.append(row)

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
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column].width = adjusted_width

    wb.save(filename)
    print(f"File '{filename}' generato con i dati degli ordini Amazon e dettaglio logistica!")
    print(f"Totale articoli: {len(orders_data) - 1}")

if __name__ == "__main__":
    generate_excel("amazon_orders_import.xlsx")
