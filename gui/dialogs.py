"""
Dialogs for Delivery Tracker application.
Contains OrderDialog and SettingsDialog.
"""
from datetime import datetime, date
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QDateEdit, QCheckBox, QTextEdit, QMessageBox,
    QGroupBox, QFormLayout, QComboBox
)
from PyQt6.QtCore import QDate

import config
import utils
import database

logger = utils.get_logger(__name__)


class OrderDialog(QDialog):
    """Dialog for adding/editing orders"""
    
    def __init__(self, parent=None, order_data=None):
        super().__init__(parent)
        self.setWindowTitle("Dettagli Ordine")
        self.resize(650, 600)
        self.order_data = order_data
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        # Product Info Group
        product_group = QGroupBox("📦 Informazioni Prodotto")
        product_layout = QFormLayout()
        
        # Platform with autocomplete
        self.platform_input = QComboBox()
        self.platform_input.setEditable(True)
        self.platform_input.setPlaceholderText("Seleziona o digita...")
        self.platform_input.addItems(config.COMMON_PLATFORMS)
        product_layout.addRow("Piattaforma:*", self.platform_input)
        
        self.seller_input = QLineEdit()
        product_layout.addRow("Venditore:", self.seller_input)
        
        self.desc_input = QLineEdit()
        product_layout.addRow("Descrizione:*", self.desc_input)
        
        self.link_input = QLineEdit()
        self.link_input.setPlaceholderText("https://...")
        product_layout.addRow("Link:", self.link_input)
        
        self.qty_input = QLineEdit()
        self.qty_input.setText("1")
        self.qty_input.setMaximumWidth(100)
        product_layout.addRow("Quantità:", self.qty_input)
        
        # Category
        self.category_input = QComboBox()
        self.category_input.setEditable(True)
        self.category_input.setPlaceholderText("Seleziona o digita...")
        self.category_input.addItems(config.DEFAULT_CATEGORIES)
        product_layout.addRow("Categoria:", self.category_input)
        
        product_group.setLayout(product_layout)
        main_layout.addWidget(product_group)

        # Delivery Info Group
        delivery_group = QGroupBox("🚚 Dettagli Spedizione")
        delivery_layout = QFormLayout()
        
        self.destination_input = QLineEdit()
        delivery_layout.addRow("Destinazione:", self.destination_input)
        
        self.position_input = QLineEdit()
        self.position_input.setPlaceholderText("Es: Magazzino, Casa, Ufficio...")
        delivery_layout.addRow("Posizione:", self.position_input)
        
        self.order_date_input = QDateEdit()
        self.order_date_input.setCalendarPopup(True)
        self.order_date_input.setDate(QDate.currentDate())
        self.order_date_input.setDisplayFormat("dd/MM/yyyy")
        delivery_layout.addRow("Data Ordine:", self.order_date_input)
        
        self.est_delivery_input = QDateEdit()
        self.est_delivery_input.setCalendarPopup(True)
        self.est_delivery_input.setDate(QDate.currentDate().addDays(7))
        self.est_delivery_input.setDisplayFormat("dd/MM/yyyy")
        delivery_layout.addRow("Consegna Prevista:", self.est_delivery_input)
        
        self.alarm_cb = QCheckBox("Abilita Allarme")
        self.alarm_cb.setChecked(True)
        self.delivered_cb = QCheckBox("Consegnato")
        
        checkbox_layout = QHBoxLayout()
        checkbox_layout.addWidget(self.alarm_cb)
        checkbox_layout.addWidget(self.delivered_cb)
        delivery_layout.addRow("Stato:", checkbox_layout)
        
        delivery_group.setLayout(delivery_layout)
        main_layout.addWidget(delivery_group)

        # Notes Group
        notes_group = QGroupBox("📝 Note")
        notes_layout = QVBoxLayout()
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(100)
        self.notes_input.setPlaceholderText("Eventuali note, difformità o difetti...")
        notes_layout.addWidget(self.notes_input)
        notes_group.setLayout(notes_layout)
        main_layout.addWidget(notes_group)

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Salva")
        save_btn.clicked.connect(self.validate_and_accept)
        save_btn.setDefault(True)
        
        cancel_btn = QPushButton("❌ Annulla")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

        if self.order_data:
            self.load_data()

    def load_data(self):
        """Load order data into form"""
        self.platform_input.setCurrentText(self.order_data['platform'])
        self.seller_input.setText(self.order_data.get('seller', ''))
        self.destination_input.setText(self.order_data.get('destination', ''))
        self.desc_input.setText(self.order_data['description'])
        self.link_input.setText(self.order_data.get('link', ''))
        self.qty_input.setText(str(self.order_data.get('quantity', 1)))
        self.category_input.setCurrentText(self.order_data.get('category', ''))
        
        if self.order_data.get('order_date'):
            od = datetime.strptime(self.order_data['order_date'], '%Y-%m-%d').date()
            self.order_date_input.setDate(QDate(od.year, od.month, od.day))
            
        if self.order_data.get('estimated_delivery'):
            ed = datetime.strptime(self.order_data['estimated_delivery'], '%Y-%m-%d').date()
            self.est_delivery_input.setDate(QDate(ed.year, ed.month, ed.day))
            
        self.alarm_cb.setChecked(bool(self.order_data.get('alarm_enabled', True)))
        self.delivered_cb.setChecked(bool(self.order_data.get('is_delivered', False)))
        self.position_input.setText(self.order_data.get('position', ''))
        self.notes_input.setText(self.order_data.get('notes', ''))

    def validate_and_accept(self):
        """Validate form data before accepting"""
        # Required fields
        if not self.platform_input.currentText().strip():
            QMessageBox.warning(self, "Validazione", "La piattaforma è obbligatoria!")
            self.platform_input.setFocus()
            return
        
        if not self.desc_input.text().strip():
            QMessageBox.warning(self, "Validazione", "La descrizione è obbligatoria!")
            self.desc_input.setFocus()
            return
        
        # Validate quantity
        valid, qty = utils.Validator.validate_quantity(self.qty_input.text())
        if not valid:
            QMessageBox.warning(self, "Validazione", "La quantità deve essere un numero positivo!")
            self.qty_input.setFocus()
            return
        
        # Validate URL if provided
        link = self.link_input.text().strip()
        if link and not utils.Validator.validate_url(link):
            QMessageBox.warning(self, "Validazione", "Il link deve iniziare con http:// o https://")
            self.link_input.setFocus()
            return
        
        self.accept()

    def get_data(self):
        """Get form data as dictionary"""
        return {
            'platform': self.platform_input.currentText().strip(),
            'seller': self.seller_input.text().strip(),
            'destination': self.destination_input.text().strip(),
            'description': self.desc_input.text().strip(),
            'link': self.link_input.text().strip(),
            'quantity': int(self.qty_input.text() or 1),
            'category': self.category_input.currentText().strip(),
            'order_date': self.order_date_input.date().toString('yyyy-MM-dd'),
            'estimated_delivery': self.est_delivery_input.date().toString('yyyy-MM-dd'),
            'alarm_enabled': self.alarm_cb.isChecked(),
            'is_delivered': self.delivered_cb.isChecked(),
            'position': self.position_input.text().strip(),
            'notes': self.notes_input.toPlainText().strip()
        }


class SettingsDialog(QDialog):
    """Settings dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Impostazioni")
        self.resize(500, 400)
        self.settings = utils.Settings.load()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # General settings
        general_group = QGroupBox("Generali")
        general_layout = QFormLayout()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Chiaro", "Scuro"])
        self.theme_combo.setCurrentText("Chiaro" if self.settings.get('theme') == 'light' else "Scuro")
        general_layout.addRow("Tema:", self.theme_combo)
        
        self.show_delivered_cb = QCheckBox()
        self.show_delivered_cb.setChecked(self.settings.get('show_delivered', True))
        general_layout.addRow("Mostra consegnati:", self.show_delivered_cb)
        
        general_group.setLayout(general_layout)
        layout.addWidget(general_group)
        
        # Notification settings
        notif_group = QGroupBox("Notifiche")
        notif_layout = QFormLayout()
        
        self.notif_enabled_cb = QCheckBox()
        self.notif_enabled_cb.setChecked(self.settings.get('notification_enabled', True))
        notif_layout.addRow("Abilita notifiche:", self.notif_enabled_cb)
        
        self.notif_days_input = QLineEdit()
        self.notif_days_input.setText(str(self.settings.get('notification_days_before', 2)))
        self.notif_days_input.setMaximumWidth(100)
        notif_layout.addRow("Giorni anticipo:", self.notif_days_input)
        
        notif_group.setLayout(notif_layout)
        layout.addWidget(notif_group)
        
        # Backup settings
        backup_group = QGroupBox("Backup")
        backup_layout = QFormLayout()
        
        self.auto_backup_cb = QCheckBox()
        self.auto_backup_cb.setChecked(self.settings.get('auto_backup', True))
        backup_layout.addRow("Backup automatico:", self.auto_backup_cb)
        
        backup_btn = QPushButton("Crea Backup Ora")
        backup_btn.clicked.connect(self.create_backup)
        backup_layout.addRow("", backup_btn)
        
        backup_group.setLayout(backup_layout)
        layout.addWidget(backup_group)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Salva")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn = QPushButton("Annulla")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def create_backup(self):
        """Create a backup now"""
        success, path = utils.BackupManager.create_backup()
        if success:
            QMessageBox.information(self, "Backup", f"Backup creato con successo:\n{path}")
        else:
            QMessageBox.warning(self, "Backup", "Errore durante la creazione del backup")
    
    def save_settings(self):
        """Save settings"""
        self.settings['theme'] = 'light' if self.theme_combo.currentText() == "Chiaro" else 'dark'
        self.settings['show_delivered'] = self.show_delivered_cb.isChecked()
        self.settings['notification_enabled'] = self.notif_enabled_cb.isChecked()
        
        try:
            self.settings['notification_days_before'] = int(self.notif_days_input.text())
        except:
            self.settings['notification_days_before'] = 2
        
        self.settings['auto_backup'] = self.auto_backup_cb.isChecked()
        
        if utils.Settings.save(self.settings):
            QMessageBox.information(self, "Impostazioni", "Impostazioni salvate!\nRiavvia l'applicazione per applicare il tema.")
            self.accept()
        else:
            QMessageBox.warning(self, "Errore", "Errore nel salvataggio delle impostazioni")
