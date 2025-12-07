"""
Enhanced GUI module for Delivery Tracker.
Includes improved UI, dashboard, search/filter, export, and theme support.
"""
import sys
import webbrowser
from datetime import datetime, date
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QDialog, QLabel,
    QLineEdit, QDateEdit, QCheckBox, QTextEdit, QMessageBox, QHeaderView,
    QAbstractItemView, QGroupBox, QFormLayout, QStyle, QComboBox,
    QFileDialog, QTabWidget, QStackedWidget, QToolBar, QMenu
)
from PyQt6.QtCore import Qt, QDate, QSize, QTimer
from PyQt6.QtGui import QColor, QBrush, QAction, QIcon

import database
import config
import utils
import export_manager
from widgets import DashboardWidget, SearchFilterBar

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


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{config.APP_NAME} v{config.APP_VERSION}")
        self.setMinimumSize(config.WINDOW_MIN_WIDTH, config.WINDOW_MIN_HEIGHT)
        
        # Load settings
        self.settings = utils.Settings.load()
        
        # Current filters
        self.current_search = ''
        self.current_platform_filter = ''
        self.current_category_filter = ''
        
        self.setup_ui()
        self.refresh_data()
        self.check_overdue_items()
        
        # Auto-refresh timer (optional)
        if self.settings.get('auto_refresh_minutes', 0) > 0:
            self.refresh_timer = QTimer()
            self.refresh_timer.timeout.connect(self.refresh_data)
            self.refresh_timer.start(self.settings['auto_refresh_minutes'] * 60 * 1000)
        
        logger.info("Application started")

    def setup_ui(self):
        """Setup the main UI"""
        # Central widget with tab/stack
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        main_layout = QHBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Sidebar
        self.setup_sidebar()
        main_layout.addWidget(self.sidebar_widget)
        
        # Content area (stacked widget for different views)
        self.content_stack = QStackedWidget()
        
        # Orders view
        self.orders_widget = QWidget()
        self.setup_orders_view()
        self.content_stack.addWidget(self.orders_widget)
        
        # Dashboard view
        self.dashboard = DashboardWidget()
        self.content_stack.addWidget(self.dashboard)
        
        main_layout.addWidget(self.content_stack)
        
        # Setup menu bar
        self.setup_menubar()

    def setup_sidebar(self):
        """Setup sidebar with navigation"""
        self.sidebar_widget = QWidget()
        self.sidebar_widget.setObjectName("sidebar")
        self.sidebar_widget.setFixedWidth(config.SIDEBAR_WIDTH_EXPANDED)
        self.is_collapsed = False
        
        sidebar_layout = QVBoxLayout(self.sidebar_widget)
        sidebar_layout.setContentsMargins(10, 15, 10, 15)
        sidebar_layout.setSpacing(10)
        
        # Toggle button
        self.toggle_btn = QPushButton()
        self.toggle_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowLeft))
        self.toggle_btn.clicked.connect(self.toggle_sidebar)
        self.toggle_btn.setFixedHeight(40)
        sidebar_layout.addWidget(self.toggle_btn)
        
        # Title
        self.title_label = QLabel("MENU")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        sidebar_layout.addWidget(self.title_label)
        
        # Navigation buttons
        self.sidebar_buttons = []
        
        # View buttons
        view_label = QLabel("VISUALIZZA")
        view_label.setStyleSheet("font-size: 11px; color: #757575; margin-top: 10px;")
        sidebar_layout.addWidget(view_label)
        self.sidebar_buttons.append((view_label, ""))
        
        dashboard_btn = self.create_sidebar_btn("Dashboard", QStyle.StandardPixmap.SP_FileDialogInfoView, 
                                                  lambda: self.content_stack.setCurrentIndex(1))
        sidebar_layout.addWidget(dashboard_btn)
        
        orders_btn = self.create_sidebar_btn("Ordini", QStyle.StandardPixmap.SP_FileDialogListView,
                                              lambda: self.content_stack.setCurrentIndex(0))
        sidebar_layout.addWidget(orders_btn)
        
        # Action buttons
        action_label = QLabel("AZIONI")
        action_label.setStyleSheet("font-size: 11px; color: #757575; margin-top: 15px;")
        sidebar_layout.addWidget(action_label)
        self.sidebar_buttons.append((action_label, ""))
        
        add_btn = self.create_sidebar_btn("Aggiungi", QStyle.StandardPixmap.SP_FileDialogNewFolder, self.add_order)
        sidebar_layout.addWidget(add_btn)

        edit_btn = self.create_sidebar_btn("Modifica", QStyle.StandardPixmap.SP_FileDialogDetailedView, self.edit_order)
        sidebar_layout.addWidget(edit_btn)

        del_btn = self.create_sidebar_btn("Elimina", QStyle.StandardPixmap.SP_TrashIcon, self.delete_order)
        sidebar_layout.addWidget(del_btn)

        refresh_btn = self.create_sidebar_btn("Aggiorna", QStyle.StandardPixmap.SP_BrowserReload, self.refresh_data)
        sidebar_layout.addWidget(refresh_btn)

        sidebar_layout.addStretch()

        # Bottom buttons
        settings_btn = self.create_sidebar_btn("Impostazioni", QStyle.StandardPixmap.SP_FileDialogDetailedView, self.show_settings)
        sidebar_layout.addWidget(settings_btn)
        
        about_btn = self.create_sidebar_btn("Info", QStyle.StandardPixmap.SP_MessageBoxInformation, self.show_about)
        sidebar_layout.addWidget(about_btn)

    def create_sidebar_btn(self, text, icon_pixmap, slot):
        """Create a sidebar button"""
        btn = QPushButton(text)
        btn.setIcon(self.style().standardIcon(icon_pixmap))
        btn.clicked.connect(slot)
        btn.setFixedHeight(40)
        btn.setIconSize(QSize(config.ICON_SIZE, config.ICON_SIZE))
        btn.setToolTip(text)
        self.sidebar_buttons.append((btn, text))
        return btn

    def toggle_sidebar(self):
        """Toggle sidebar collapsed/expanded"""
        if self.is_collapsed:
            # Expand
            self.sidebar_widget.setFixedWidth(config.SIDEBAR_WIDTH_EXPANDED)
            self.title_label.show()
            self.toggle_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowLeft))
            for widget, text in self.sidebar_buttons:
                if isinstance(widget, QPushButton):
                    widget.setText(text)
                elif isinstance(widget, QLabel):
                    widget.show()
            self.is_collapsed = False
        else:
            # Collapse
            self.sidebar_widget.setFixedWidth(config.SIDEBAR_WIDTH_COLLAPSED)
            self.title_label.hide()
            self.toggle_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowRight))
            for widget, text in self.sidebar_buttons:
                if isinstance(widget, QPushButton):
                    widget.setText("")
                elif isinstance(widget, QLabel):
                    widget.hide()
            self.is_collapsed = True

    def setup_orders_view(self):
        """Setup the orders table view"""
        layout = QVBoxLayout(self.orders_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Search and filter bar
        self.search_filter_bar = SearchFilterBar()
        self.search_filter_bar.search_changed.connect(self.on_search_changed)
        self.search_filter_bar.filter_changed.connect(self.on_filter_changed)
        layout.addWidget(self.search_filter_bar)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(13)
        self.table.setHorizontalHeaderLabels([
            "ID", "Data", "Piattaforma", "Venditore", "Destinazione", "Descrizione", 
            "Link", "Q.tà", "Cons. Prevista", "Posizione", "Categoria", "Consegnato", "Note"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.setAlternatingRowColors(True)
        self.table.hideColumn(0)  # Hide ID
        self.table.doubleClicked.connect(self.edit_order)
        self.table.cellClicked.connect(self.on_cell_clicked)
        
        # Context menu
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.table)

    def setup_menubar(self):
        """Setup menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        export_menu = file_menu.addMenu("Esporta")
        
        export_excel_action = QAction("Esporta Excel", self)
        export_excel_action.triggered.connect(lambda: self.export_data('excel'))
        export_menu.addAction(export_excel_action)
        
        export_csv_action = QAction("Esporta CSV", self)
        export_csv_action.triggered.connect(lambda: self.export_data('csv'))
        export_menu.addAction(export_csv_action)
        
        export_json_action = QAction("Esporta JSON", self)
        export_json_action.triggered.connect(lambda: self.export_data('json'))
        export_menu.addAction(export_json_action)
        
        import_menu = file_menu.addMenu("Importa")
        
        import_json_action = QAction("Importa JSON", self)
        import_json_action.triggered.connect(self.import_data)
        import_menu.addAction(import_json_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Esci", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("&Visualizza")
        
        dashboard_action = QAction("Dashboard", self)
        dashboard_action.triggered.connect(lambda: self.content_stack.setCurrentIndex(1))
        view_menu.addAction(dashboard_action)
        
        orders_action = QAction("Ordini", self)
        orders_action.triggered.connect(lambda: self.content_stack.setCurrentIndex(0))
        view_menu.addAction(orders_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Aiuto")
        
        about_action = QAction("Info", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def show_context_menu(self, position):
        """Show context menu for table"""
        menu = QMenu()
        
        edit_action = menu.addAction("Modifica")
        edit_action.triggered.connect(self.edit_order)
        
        delete_action = menu.addAction("Elimina")
        delete_action.triggered.connect(self.delete_order)
        
        menu.addSeparator()
        
        mark_delivered_action = menu.addAction("Segna come Consegnato")
        mark_delivered_action.triggered.connect(lambda: self.mark_delivered(True))
        
        mark_not_delivered_action = menu.addAction("Segna come Non Consegnato")
        mark_not_delivered_action.triggered.connect(lambda: self.mark_delivered(False))
        
        menu.exec(self.table.viewport().mapToGlobal(position))

    def on_cell_clicked(self, row, column):
        """Handle cell click (for links)"""
        if column == 6:  # Link column
            item = self.table.item(row, column)
            if item and item.text():
                webbrowser.open(item.text())

    def on_search_changed(self, search_text):
        """Handle search text change"""
        self.current_search = search_text
        self.refresh_table()

    def on_filter_changed(self, filters):
        """Handle filter change"""
        self.current_platform_filter = filters.get('platform', '')
        self.current_category_filter = filters.get('category', '')
        self.settings['show_delivered'] = filters.get('show_delivered', True)
        self.refresh_table()

    def refresh_data(self):
        """Refresh all data"""
        self.refresh_table()
        self.refresh_dashboard()
        self.update_filter_options()

    def refresh_table(self):
        """Refresh the orders table"""
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        
        # Get orders with filters
        orders = database.get_orders(
            include_delivered=self.settings.get('show_delivered', True),
            search=self.current_search,
            platform_filter=self.current_platform_filter,
            category_filter=self.current_category_filter
        )
        
        for row, order in enumerate(orders):
            self.table.insertRow(row)
            
            # Add data to cells
            self.table.setItem(row, 0, QTableWidgetItem(str(order['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(order.get('order_date', '')))
            self.table.setItem(row, 2, QTableWidgetItem(order.get('platform', '')))
            self.table.setItem(row, 3, QTableWidgetItem(order.get('seller', '')))
            self.table.setItem(row, 4, QTableWidgetItem(order.get('destination', '')))
            self.table.setItem(row, 5, QTableWidgetItem(order.get('description', '')))

            # Link with formatting
            link_item = QTableWidgetItem(order.get('link', ''))
            if order.get('link'):
                link_item.setForeground(QBrush(QColor("blue")))
                font = link_item.font()
                font.setUnderline(True)
                link_item.setFont(font)
            self.table.setItem(row, 6, link_item)
            
            self.table.setItem(row, 7, QTableWidgetItem(str(order.get('quantity', 1))))
            self.table.setItem(row, 8, QTableWidgetItem(order.get('estimated_delivery', '')))
            self.table.setItem(row, 9, QTableWidgetItem(order.get('position', '')))
            self.table.setItem(row, 10, QTableWidgetItem(order.get('category', '')))
            self.table.setItem(row, 11, QTableWidgetItem("Sì" if order.get('is_delivered') else "No"))
            self.table.setItem(row, 12, QTableWidgetItem(order.get('notes', '')))

            # Add tooltips
            for col in range(13):
                item = self.table.item(row, col)
                if item:
                    item.setToolTip(item.text())

            # Color rows based on status
            if order.get('is_delivered'):
                color = QColor(config.LIGHT_THEME.delivered)
            elif order.get('estimated_delivery') and order.get('alarm_enabled'):
                est_date = utils.DateHelper.parse_date(order['estimated_delivery'])
                if est_date:
                    status = utils.DateHelper.get_date_status(est_date)
                    if status == 'overdue':
                        color = QColor(config.LIGHT_THEME.overdue)
                    elif status == 'due_today':
                        color = QColor(config.LIGHT_THEME.due_today)
                    elif status == 'upcoming':
                        color = QColor(config.LIGHT_THEME.upcoming)
                    else:
                        color = None
                else:
                    color = None
            else:
                color = None
            
            if color:
                for col in range(13):
                    item = self.table.item(row, col)
                    if item:
                        item.setBackground(color)
        
        self.table.setSortingEnabled(True)
        logger.info(f"Table refreshed with {len(orders)} orders")

    def refresh_dashboard(self):
        """Refresh dashboard with current data"""
        orders = database.get_orders()
        self.dashboard.update_stats(orders)

    def update_filter_options(self):
        """Update filter dropdown options"""
        # Get platforms from database, fallback to defaults if empty
        platforms = database.get_platforms()
        if not platforms:
            platforms = config.COMMON_PLATFORMS
        self.search_filter_bar.update_platforms(platforms)
        
        # Get categories from database, fallback to defaults if empty
        categories = [cat['name'] for cat in database.get_categories()]
        if not categories:
            categories = config.DEFAULT_CATEGORIES
        self.search_filter_bar.update_categories(categories)

    def check_overdue_items(self):
        """Check and notify about overdue items"""
        if not self.settings.get('notification_enabled', True):
            return
        
        orders = database.get_orders(include_delivered=False)
        overdue_items = []
        today = date.today()
        
        for order in orders:
            if order.get('alarm_enabled') and order.get('estimated_delivery'):
                est_date = utils.DateHelper.parse_date(order['estimated_delivery'])
                if est_date and est_date < today:
                    overdue_items.append(f"- {order['description']} (Scadenza: {order['estimated_delivery']})")
        
        if overdue_items:
            msg = "⚠️ I seguenti articoli sono scaduti:\n\n" + "\n".join(overdue_items)
            QMessageBox.warning(self, "Consegne Scadute", msg)

    def add_order(self):
        """Add a new order"""
        dialog = OrderDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            order_id = database.add_order(data)
            if order_id:
                QMessageBox.information(self, "Successo", "Ordine aggiunto con successo!")
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Errore", "Errore durante l'aggiunta dell'ordine")

    def edit_order(self):
        """Edit selected order"""
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.information(self, "Selezione", "Seleziona un ordine da modificare")
            return
        
        row = selected[0].row()
        order_id = int(self.table.item(row, 0).text())
        
        order_data = database.get_order_by_id(order_id)
        
        if order_data:
            dialog = OrderDialog(self, order_data)
            if dialog.exec():
                new_data = dialog.get_data()
                if database.update_order(order_id, new_data):
                    QMessageBox.information(self, "Successo", "Ordine aggiornato con successo!")
                    self.refresh_data()
                else:
                    QMessageBox.warning(self, "Errore", "Errore durante l'aggiornamento")

    def delete_order(self):
        """Delete selected order"""
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.information(self, "Selezione", "Seleziona un ordine da eliminare")
            return
            
        row = selected[0].row()
        order_id = int(self.table.item(row, 0).text())
        
        confirm = QMessageBox.question(
            self, "Conferma Eliminazione", 
            "Sei sicuro di voler eliminare questo ordine?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            if database.delete_order(order_id):
                QMessageBox.information(self, "Successo", "Ordine eliminato con successo!")
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Errore", "Errore durante l'eliminazione")

    def mark_delivered(self, delivered=True):
        """Mark selected order as delivered/not delivered"""
        selected = self.table.selectedItems()
        if not selected:
            return
            
        row = selected[0].row()
        order_id = int(self.table.item(row, 0).text())
        
        if database.mark_as_delivered(order_id, delivered):
            self.refresh_data()

    def export_data(self, format_type):
        """Export data to file"""
        orders = database.get_orders()
        
        if not orders:
            QMessageBox.information(self, "Export", "Nessun ordine da esportare")
            return
        
        # File dialog
        filters = {
            'excel': "Excel Files (*.xlsx)",
            'csv': "CSV Files (*.csv)",
            'json': "JSON Files (*.json)"
        }
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Esporta Ordini", "", filters.get(format_type, "All Files (*)")
        )
        
        if not filepath:
            return
        
        # Export
        success = False
        if format_type == 'excel':
            success = export_manager.ExportManager.export_to_excel(filepath, orders)
        elif format_type == 'csv':
            success = export_manager.ExportManager.export_to_csv(filepath, orders)
        elif format_type == 'json':
            success = export_manager.ExportManager.export_to_json(filepath, orders)
        
        if success:
            QMessageBox.information(self, "Export", f"Dati esportati con successo in:\n{filepath}")
        else:
            QMessageBox.warning(self, "Errore", "Errore durante l'esportazione")

    def import_data(self):
        """Import data from JSON file"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Importa Ordini", "", "JSON Files (*.json)"
        )
        
        if not filepath:
            return
        
        success, count = database.import_from_json(filepath)
        
        if success:
            QMessageBox.information(self, "Import", f"Importati {count} ordini con successo!")
            self.refresh_data()
        else:
            QMessageBox.warning(self, "Errore", "Errore durante l'importazione")

    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self)
        if dialog.exec():
            self.settings = utils.Settings.load()
            self.refresh_data()

    def show_about(self):
        """Show about dialog"""
        msg = (
            f"<h2>{config.APP_NAME}</h2>"
            f"<p><b>Versione:</b> {config.APP_VERSION}</p>"
            f"<p><b>Data:</b> {date.today().strftime('%d/%m/%Y')}</p>"
            f"<p><b>Autore:</b> {config.APP_AUTHOR}</p>"
            f"<p><b>Supporto:</b> {config.APP_SUPPORT}</p>"
            f"<p><b>Sviluppo:</b> {config.APP_DEVELOPER}</p>"
            "<hr>"
            "<p>Applicazione per la gestione e il tracciamento delle consegne da piattaforme online.</p>"
        )
        QMessageBox.about(self, "Informazioni", msg)

    def closeEvent(self, event):
        """Handle window close event"""
        # Auto backup on close if enabled
        if self.settings.get('auto_backup', True):
            utils.BackupManager.create_backup()
        
        logger.info("Application closed")
        event.accept()
