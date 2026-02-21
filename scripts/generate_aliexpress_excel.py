from openpyxl import Workbook
from openpyxl.styles import Font, Alignment

# Data extracted from AliExpress browser analysis
# Columns: 'Data dell'ordine', 'Piattaforma', 'ID Ordine', 'Venditore', 'Descrizione', 'Prezzo Prodotto (EUR)', 'Quantità', 'Immagine', 'Link', 'Stato', 'Numero di Tracking', 'Consegna Stimata', 'Destinazione', 'Vettore', 'Ultimo Miglio'
orders_data = [
    ["Data dell'ordine", "Piattaforma", "ID Ordine", "Venditore", "Descrizione", "Prezzo Prodotto (EUR)", "Quantità", "Immagine", "Link", "Stato", "Numero di Tracking", "Consegna Stimata", "Destinazione", "Vettore", "Ultimo Miglio"],
    ["17 Feb 2026", "AliExpress", "3068779692983676", "ENSH Tech World Store", "Scheda Riser PCI Express adattatore Extender PCI-e da 1X a 16X per GPU Mining", 5.59, 3, "https://ae01.alicdn.com/kf/S5c33d643c04e4a0a8af279e409cca037f.jpg_220x220.jpg", "https://www.aliexpress.com/item/1005007368382420.html", "In attesa di consegna", "AP00797880759958", "2026-03-01", "VIA POMARA 24-B,Palermo,Palermo,Sicilia,Italy 90121", "AliExpress Selection Standard", "AliExpress Selection Standard"],
    ["17 Feb 2026", "AliExpress", "3068779693003676", "JuYiCheng Store", "Scheda prototipo PCB Circuito verde bifacciale (varie misure) per DIY/Arduino", 2.04, 1, "https://ae01.alicdn.com/kf/S704ba6514e7a44ceb40a20055a0b756bG.jpg_220x220.jpg", "https://www.aliexpress.com/item/1005008880680070.html", "In attesa di consegna", "AP00797880759958", "2026-03-01", "VIA POMARA 24-B,Palermo,Palermo,Sicilia,Italy 90121", "AliExpress Selection Standard", "AliExpress Selection Standard"],
    ["09 Feb 2026", "AliExpress", "3068715734913676", "Zirong 5477 Trade Store", "MIniGPS Finder Sicurezza SmartTrack Link Smart Tag (Apple Find My)", 4.42, 1, "https://ae01.alicdn.com/kf/Sfb72d4ec8903483aa298ca80b8ea68b7b.jpg_220x220.jpg", "https://www.aliexpress.com/item/1005010332697604.html", "Consegnato", "9C1579J611751", "2026-02-19", "Via Galletti 128/G,Palermo,Palermo,Sicilia,Italy 90121", "Poste Italiane", "Poste Italiane"],
    ["09 Feb 2026", "AliExpress", "3068715734933676", "Find My Store", "Localizzatore anti-smarrimento per Android/iOS Apple Find My", 3.44, 1, "https://ae01.alicdn.com/kf/S189ddaf552464f02a589abd8cf380d59o.jpg_220x220.jpg", "https://www.aliexpress.com/item/1005009750564756.html", "Consegnato", "9C1579J611751", "2026-02-19", "Via Galletti 128/G,Palermo,Palermo,Sicilia,Italy 90121", "Poste Italiane", "Poste Italiane"],
    ["05 Feb 2026", "AliExpress", "3068667663043676", "3D Printer Premium Store Store", "Kit strumenti stampante 3D (53 pezzi) con aghi pulizia ugelli", 4.46, 1, "https://ae01.alicdn.com/kf/Sa7737977f8c14613b2fca69119427c0ej.png_220x220.png", "https://www.aliexpress.com/item/1005010142795504.html", "In attesa di consegna", "505713438072", "2026-02-11", "VIA POMARA 24-B,Palermo,Palermo,Sicilia,Italy 90121", "Poste Italiane", "Poste Italiane"],
    ["05 Feb 2026", "AliExpress", "3068667663063676", "All-Electronics-Five-Stars Store", "Programmatore USB CH341A/CH341B + Clip SOIC8 + Adattatori", 3.65, 1, "https://ae01.alicdn.com/kf/S08a2b688efdc436f91375fb6de5a65efi.jpg_220x220.jpg", "https://www.aliexpress.com/item/1005006398250607.html", "In attesa di consegna", "505713438072", "2026-02-11", "VIA POMARA 24-B,Palermo,Palermo,Sicilia,Italy 90121", "Poste Italiane", "Poste Italiane"],
    ["20 Gen 2026", "AliExpress", "3067894146723676", "Jamily Trend Store", "Cavi Splitter SATA (Jamily Trend Store)", 5.47, 1, "https://ae01.alicdn.com/kf/S0b47c570a90e4b62b1874b527062e091D.jpg_220x220.jpg", "https://www.aliexpress.com/item/1005008319243125.html", "Consegnato", "", "", "VIA POMARA 24-B,Palermo,Palermo,Sicilia,Italy 90121", "Poste Italiane", "Poste Italiane"],
    ["20 Gen 2026", "AliExpress", "3067894146753676", "Wisdom Interest Store", "Cavo Splitter Alimentazione SATA 1 Maschio a 2 Femmina 15PIN", 1.59, 1, "https://ae01.alicdn.com/kf/S8080209e740e4dc2a68be1753c739d9cP.jpg_220x220.jpg", "https://www.aliexpress.com/item/1005007690933814.html", "Consegnato", "", "", "VIA POMARA 24-B,Palermo,Palermo,Sicilia,Italy 90121", "Poste Italiane", "Poste Italiane"],
    ["18 Gen 2026", "AliExpress", "3067636936383676", "Shop1102751449 Store", "Mini PCIe to PCI express 16X Riser per laptop EXP GDC", 5.99, 2, "https://ae01.alicdn.com/kf/Se25f5ff32f344ad78e803d2b3be26eacB.jpg_220x220.jpg", "https://www.aliexpress.com/item/1005005443376594.html", "Consegnato", "", "", "VIA POMARA 24-B,Palermo,Palermo,Sicilia,Italy 90121", "Poste Italiane", "Poste Italiane"],
    ["18 Gen 2026", "AliExpress", "3067636936403676", "TISHRIC Franchise Store", "Scheda espansione PCI-e USB 3.2 (2/4/5 porte Type-C/19Pin)", 13.83, 1, "https://ae01.alicdn.com/kf/S00808fc1a27b4ab4ad80f025f7a09e87g.jpg_220x220.jpg", "https://www.aliexpress.com/item/1005006037410264.html", "Consegnato", "", "", "VIA POMARA 24-B,Palermo,Palermo,Sicilia,Italy 90121", "Poste Italiane", "Poste Italiane"]
]

def generate_excel(filename):
    wb = Workbook()
    ws = wb.active
    ws.title = "AliExpress Orders"

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
    print(f"File '{filename}' generato con Vettore e Ultimo Miglio!")
    print(f"Totale articoli: {len(orders_data) - 1}")

if __name__ == "__main__":
    generate_excel("aliexpress_orders_import.xlsx")
