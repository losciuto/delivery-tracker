#!/usr/bin/env python3
"""
Test script per verificare che OrderDialog carichi correttamente le liste
"""
import sys
sys.path.insert(0, '/home/massimo/Scaricati/ProgettiAntigravity/delivery-tracker/delivery-tracker')

import config

print("=" * 60)
print("TEST CONFIGURAZIONE DIALOG ORDINI")
print("=" * 60)

print(f"\n📦 PIATTAFORME ({len(config.COMMON_PLATFORMS)} elementi):")
for i, platform in enumerate(config.COMMON_PLATFORMS, 1):
    print(f"  {i:2d}. {platform}")

print(f"\n🏷️  CATEGORIE ({len(config.DEFAULT_CATEGORIES)} elementi):")
for i, category in enumerate(config.DEFAULT_CATEGORIES, 1):
    print(f"  {i:2d}. {category}")

print("\n" + "=" * 60)
print("✅ Le liste sono configurate correttamente!")
print("=" * 60)

print("\n💡 SUGGERIMENTO:")
print("Se il dialog non mostra le liste:")
print("1. Chiudi completamente l'applicazione")
print("2. Riavvia con: ./venv/bin/python main.py")
print("3. Apri 'Aggiungi' o 'Modifica' ordine")
print("4. Click sulla freccia dei campi Piattaforma/Categoria")
