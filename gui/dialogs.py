"""
Dialogs for Delivery Tracker application.
Contains OrderDialog and SettingsDialog.
"""
from datetime import datetime, date
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QDateEdit, QCheckBox, QTextEdit, QMessageBox,
    QGroupBox, QFormLayout, QComboBox, QWidget, QFrame, QTabWidget
)
from PyQt6.QtCore import QDate, pyqtSignal

import config
from config import ORDER_STATUSES
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
        # Main dialog layout
        dialog_layout = QVBoxLayout(self)
        dialog_layout.setContentsMargins(10, 10, 10, 10)
        dialog_layout.setSpacing(10)

        # Tab Widget Setup
        self.tabs = QTabWidget()
        
        # --- TAB 1: PRODOTTO ---
        product_tab = QWidget()
        product_main_layout = QVBoxLayout(product_tab)
        
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
        
        self.site_order_id_input = QLineEdit()
        self.site_order_id_input.setPlaceholderText("Es: 403-1234567-1234567...")
        product_layout.addRow("ID Ordine Sito:", self.site_order_id_input)
        self.link_input = QLineEdit()
        self.link_input.setPlaceholderText("https://...")
        product_layout.addRow("Link:", self.link_input)
        
        self.status_input = QComboBox()
        self.status_input.addItems(ORDER_STATUSES)
        product_layout.addRow("Stato:", self.status_input)
        
        self.qty_input = QLineEdit()
        self.qty_input.setText("1")
        self.qty_input.setMaximumWidth(100)
        product_layout.addRow("Quantità:", self.qty_input)

        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("Es: 12.50")
        self.price_input.setMaximumWidth(120)
        product_layout.addRow("Prezzo (€):", self.price_input)

        self.image_url_input = QLineEdit()
        self.image_url_input.setPlaceholderText("https://... (link immagine prodotto)")
        product_layout.addRow("Immagine (URL):", self.image_url_input)

        # Category
        self.category_input = QComboBox()
        self.category_input.setEditable(True)
        self.category_input.setPlaceholderText("Seleziona o digita...")
        self.category_input.addItems(config.DEFAULT_CATEGORIES)
        product_layout.addRow("Categoria:", self.category_input)

        product_group.setLayout(product_layout)
        product_main_layout.addWidget(product_group)
        self.tabs.addTab(product_tab, "📦 Prodotto")

        # --- TAB 2: SPEDIZIONE ---
        delivery_tab = QWidget()
        delivery_main_layout = QVBoxLayout(delivery_tab)
        
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
        
        self.tracking_input = QLineEdit()
        self.tracking_input.setPlaceholderText("Es: 1Z999...")
        delivery_layout.addRow("N. Tracking:", self.tracking_input)
        
        self.carrier_input = QLineEdit()
        self.carrier_input.setPlaceholderText("Es: UPS, DHL, Amazon...")
        delivery_layout.addRow("Vettore:", self.carrier_input)
        
        self.last_mile_input = QLineEdit()
        self.last_mile_input.setPlaceholderText("Es: Poste Italiane, SDA...")
        delivery_layout.addRow("Ultimo Miglio:", self.last_mile_input)
        
        self.alarm_cb = QCheckBox("Abilita Allarme")
        self.alarm_cb.setChecked(True)
        self.delivered_cb = QCheckBox("Consegnato")
        
        checkbox_layout = QHBoxLayout()
        checkbox_layout.addWidget(self.alarm_cb)
        checkbox_layout.addWidget(self.delivered_cb)
        delivery_layout.addRow("Stato:", checkbox_layout)
        
        delivery_group.setLayout(delivery_layout)
        delivery_main_layout.addWidget(delivery_group)
        self.tabs.addTab(delivery_tab, "🚚 Spedizione")

        # --- TAB 3: NOTE ---
        notes_tab = QWidget()
        notes_main_layout = QVBoxLayout(notes_tab)
        
        notes_group = QGroupBox("📝 Note")
        notes_layout = QVBoxLayout()
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Eventuali note, difformità o difetti...")
        notes_layout.addWidget(self.notes_input)
        notes_group.setLayout(notes_layout)
        notes_main_layout.addWidget(notes_group)
        self.tabs.addTab(notes_tab, "📝 Note")
        
        dialog_layout.addWidget(self.tabs)

        # Buttons (Fixed at the bottom, outside tabs)
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(10, 0, 10, 5)
        
        save_btn = QPushButton("💾 Salva")
        save_btn.setFixedHeight(40)
        save_btn.clicked.connect(self.validate_and_accept)
        save_btn.setDefault(True)
        
        cancel_btn = QPushButton("❌ Annulla")
        cancel_btn.setFixedHeight(40)
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        dialog_layout.addLayout(btn_layout)

        if self.order_data:
            self.load_data()

        # Connect auto-alignment for text fields
        self.setup_auto_align()

    def setup_auto_align(self):
        """Connect editingFinished to return cursor to position 0 for all text inputs"""
        text_widgets = [
            self.seller_input, self.desc_input, self.site_order_id_input,
            self.link_input, self.qty_input, self.price_input, self.image_url_input,
            self.destination_input, self.position_input, self.tracking_input,
            self.carrier_input, self.last_mile_input, self.platform_input,
            self.category_input
        ]
        
        for widget in text_widgets:
            if isinstance(widget, QLineEdit):
                widget.editingFinished.connect(lambda w=widget: w.setCursorPosition(0))
            elif isinstance(widget, QComboBox) and widget.isEditable():
                line_edit = widget.lineEdit()
                if line_edit:
                    line_edit.editingFinished.connect(lambda le=line_edit: le.setCursorPosition(0))


    def load_data(self):
        """Load order data into form"""
        self.platform_input.setCurrentText(self.order_data['platform'])
        self.seller_input.setText(self.order_data.get('seller', ''))
        self.destination_input.setText(self.order_data.get('destination', ''))
        self.desc_input.setText(self.order_data['description'])
        self.site_order_id_input.setText(self.order_data.get('site_order_id', ''))
        self.link_input.setText(self.order_data.get('link', ''))
        self.status_input.setCurrentText(self.order_data.get('status', 'In Attesa'))
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
        self.tracking_input.setText(self.order_data.get('tracking_number', ''))
        self.carrier_input.setText(self.order_data.get('carrier', ''))
        self.last_mile_input.setText(self.order_data.get('last_mile_carrier', ''))
        self.notes_input.setText(self.order_data.get('notes', ''))

        # New fields
        price = self.order_data.get('price')
        self.price_input.setText(f"{price:.2f}" if price is not None else '')
        self.image_url_input.setText(self.order_data.get('image_url', ''))

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

        # Validate price if provided
        price_text = self.price_input.text().strip()
        if price_text:
            try:
                float(price_text.replace(',', '.'))
            except ValueError:
                QMessageBox.warning(self, "Validazione", "Il prezzo deve essere un numero (es: 12.50)")
                self.price_input.setFocus()
                return

        # Validate image URL if provided
        image_url = self.image_url_input.text().strip()
        if image_url and not utils.Validator.validate_url(image_url):
            QMessageBox.warning(self, "Validazione", "L'URL immagine deve iniziare con http:// o https://")
            self.image_url_input.setFocus()
            return
        
        self.accept()

    def get_data(self):
        """Get form data as dictionary"""
        price_text = self.price_input.text().strip().replace(',', '.')
        try:
            price = float(price_text) if price_text else None
        except ValueError:
            price = None

        return {
            'platform': self.platform_input.currentText().strip(),
            'seller': self.seller_input.text().strip(),
            'destination': self.destination_input.text().strip(),
            'description': self.desc_input.text().strip(),
            'site_order_id': self.site_order_id_input.text().strip(),
            'link': self.link_input.text().strip(),
            'status': self.status_input.currentText(),
            'quantity': int(self.qty_input.text() or 1),
            'price': price,
            'image_url': self.image_url_input.text().strip(),
            'category': self.category_input.currentText().strip(),
            'order_date': self.order_date_input.date().toString('yyyy-MM-dd'),
            'estimated_delivery': self.est_delivery_input.date().toString('yyyy-MM-dd'),
            'alarm_enabled': self.alarm_cb.isChecked(),
            'is_delivered': self.delivered_cb.isChecked(),
            'position': self.position_input.text().strip(),
            'tracking_number': self.tracking_input.text().strip(),
            'carrier': self.carrier_input.text().strip(),
            'last_mile_carrier': self.last_mile_input.text().strip(),
            'notes': self.notes_input.toPlainText().strip()
        }


class SettingsDialog(QDialog):
    """Settings dialog"""
    
    theme_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Impostazioni")
        self.resize(500, 400)
        self.settings = utils.Settings.load()
        self.setup_ui()
    
    def connect_microsoft_account(self):
        """Invoke auth_helper to connect account"""
        from auth_helper import authorize
        QMessageBox.information(self, "OAuth2 Authentication", 
                               "Si aprirà il browser. Segui le istruzioni nel terminale/finestra per autorizzare l'app.")
        if authorize():
            QMessageBox.information(self, "Successo", "Account collegato con successo!")
            self.settings = utils.Settings.load() # Reload to get new cache and email
            self.email_addr_input.setText(self.settings.get('email_address', ''))
        else:
            QMessageBox.critical(self, "Errore", "L'autorizzazione è fallita o è stata annullata.")
    
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
        
        # Email settings
        email_group = QGroupBox("Integrazione Email (Hotmail/Outlook)")
        email_layout = QFormLayout()
        
        self.email_sync_cb = QCheckBox()
        self.email_sync_cb.setChecked(self.settings.get('email_sync_enabled', False))
        email_layout.addRow("Abilita sincronizzazione:", self.email_sync_cb)
        
        self.email_addr_input = QLineEdit()
        self.email_addr_input.setText(self.settings.get('email_address', ''))
        self.email_addr_input.setPlaceholderText("esempio@hotmail.com")
        self.email_addr_input.setToolTip("Inserisci l'email manualmente o usa il pulsante 'Connetti' per l'autorizzazione automatica")
        email_layout.addRow("Account Collegato:", self.email_addr_input)
        
        self.connect_btn = QPushButton("Connetti Account Microsoft")
        self.connect_btn.clicked.connect(self.connect_microsoft_account)
        email_layout.addRow("", self.connect_btn)
        
        email_group.setLayout(email_layout)
        layout.addWidget(email_group)
        
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
        
        # Email settings
        self.settings['email_sync_enabled'] = self.email_sync_cb.isChecked()
        self.settings['email_address'] = self.email_addr_input.text().strip()
        
        try:
            self.settings['notification_days_before'] = int(self.notif_days_input.text())
        except:
            self.settings['notification_days_before'] = 2
        
        self.settings['auto_backup'] = self.auto_backup_cb.isChecked()
        
        if utils.Settings.save(self.settings):
            self.theme_changed.emit(self.settings['theme'])
            QMessageBox.information(self, "Impostazioni", "Impostazioni salvate con successo!")
            self.accept()
        else:
            QMessageBox.warning(self, "Errore", "Errore nel salvataggio delle impostazioni")
