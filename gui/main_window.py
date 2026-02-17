"""
Main Window for Delivery Tracker application.
Contains the primary GUI logic and layout.
"""
import webbrowser
from datetime import date
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel,
    QMessageBox, QHeaderView, QAbstractItemView, QStyle, 
    QStackedWidget, QMenu
)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QColor, QBrush, QAction

import database
import config
import utils
from widgets import DashboardWidget, SearchFilterBar
from gui.dialogs import OrderDialog, SettingsDialog

logger = utils.get_logger(__name__)


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{config.APP_NAME} v{config.APP_VERSION}")
        
        # Dynamic window sizing based on screen resolution
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        if screen:
            screen_geom = screen.availableGeometry()
            width = int(screen_geom.width() * 0.9)
            height = int(screen_geom.height() * 0.85)
            
            # Ensure we don't go below config minimums
            width = max(width, config.WINDOW_MIN_WIDTH)
            height = max(height, config.WINDOW_MIN_HEIGHT)
            
            logger.info(f"Setting dynamic window size: {width}x{height} (Screen: {screen_geom.width()}x{screen_geom.height()})")
            self.resize(width, height)
            
            # Center the window
            x = (screen_geom.width() - width) // 2
            y = (screen_geom.height() - height) // 2
            self.move(x, y)
        else:
            self.setMinimumSize(config.WINDOW_MIN_WIDTH, config.WINDOW_MIN_HEIGHT)
            self.resize(config.WINDOW_MIN_WIDTH, config.WINDOW_MIN_HEIGHT)
        
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
        
        dashboard_btn = self.create_sidebar_btn("Dashboard", QStyle.StandardPixmap.SP_DirHomeIcon, 
                                                  lambda: self.content_stack.setCurrentIndex(1))
        sidebar_layout.addWidget(dashboard_btn)
        
        orders_btn = self.create_sidebar_btn("Ordini", QStyle.StandardPixmap.SP_DirIcon,
                                              lambda: self.content_stack.setCurrentIndex(0))
        sidebar_layout.addWidget(orders_btn)
        
        # Action buttons
        action_label = QLabel("AZIONI")
        action_label.setStyleSheet("font-size: 11px; color: #757575; margin-top: 15px;")
        sidebar_layout.addWidget(action_label)
        self.sidebar_buttons.append((action_label, ""))
        
        add_btn = self.create_sidebar_btn("Aggiungi", QStyle.StandardPixmap.SP_FileDialogNewFolder, self.add_order)
        sidebar_layout.addWidget(add_btn)

        edit_btn = self.create_sidebar_btn("Modifica", QStyle.StandardPixmap.SP_FileIcon, self.edit_order)
        sidebar_layout.addWidget(edit_btn)

        del_btn = self.create_sidebar_btn("Elimina", QStyle.StandardPixmap.SP_TrashIcon, self.delete_order)
        sidebar_layout.addWidget(del_btn)

        refresh_btn = self.create_sidebar_btn("Aggiorna", QStyle.StandardPixmap.SP_BrowserReload, self.refresh_data)
        sidebar_layout.addWidget(refresh_btn)

        sidebar_layout.addStretch()

        # Bottom buttons
        settings_btn = self.create_sidebar_btn("Impostazioni", QStyle.StandardPixmap.SP_ComputerIcon, self.show_settings)
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
        
        # Adjust column widths
        self.table.setColumnWidth(8, 160)  # Cons. Prevista (leggermente più larga)
        self.table.setColumnWidth(1, 100)  # Data
        self.table.setColumnWidth(7, 60)   # Q.tà
        self.table.setColumnWidth(11, 100) # Consegnato
        
        # Behavior for other columns
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)  # Descrizione
        header.setSectionResizeMode(12, QHeaderView.ResizeMode.Stretch) # Note
        
        # Interactive for most, but ensure good initial fit
        for i in [2, 3, 4, 6, 9, 10]:
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
            self.table.setColumnWidth(i, 130)
        
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
        
        # Tools menu
        tools_menu = menubar.addMenu("&Strumenti")
        
        sync_email_action = QAction("📧 Sincronizza Email", self)
        sync_email_action.triggered.connect(self.sync_emails)
        tools_menu.addAction(sync_email_action)
        
        tools_menu.addSeparator()
        
        settings_action = QAction("⚙️ Impostazioni", self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
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
        
        # Determine current theme colors
        theme_name = self.settings.get('theme', 'light')
        colors = config.LIGHT_THEME if theme_name == 'light' else config.DARK_THEME
        
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
                link_item.setForeground(QBrush(QColor("blue") if theme_name == 'light' else QColor("#64B5F6")))
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
                color = QColor(colors.delivered)
            elif order.get('estimated_delivery') and order.get('alarm_enabled'):
                est_date = utils.DateHelper.parse_date(order['estimated_delivery'])
                if est_date:
                    status = utils.DateHelper.get_date_status(est_date)
                    if status == 'overdue':
                        color = QColor(colors.overdue)
                    elif status == 'due_today':
                        color = QColor(colors.due_today)
                    elif status == 'upcoming':
                        color = QColor(colors.upcoming)
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
                        # Ensure text is readable on colored background
                        item.setForeground(QBrush(QColor("black") if theme_name == 'light' else QColor("white")))
        
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
        from PyQt6.QtWidgets import QFileDialog
        import export_manager
        
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
        
        default_ext = config.EXPORT_FORMATS.get(format_type.capitalize(), '.csv')
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Esporta Dati", 
            f"delivery_tracker_export_{date.today()}{default_ext}",
            filters.get(format_type, "All Files (*.*)")
        )
        
        if filename:
            success = False
            if format_type == 'excel':
                success = export_manager.export_to_excel(filename, orders)
            elif format_type == 'csv':
                success = database.export_to_csv(filename, orders)
            elif format_type == 'json':
                success = database.export_to_json(filename, orders)
                
            if success:
                QMessageBox.information(self, "Export", f"Export completato con successo:\n{filename}")
            else:
                QMessageBox.warning(self, "Export", "Errore durante l'export")

    def import_data(self):
        """Import data from JSON"""
        from PyQt6.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getOpenFileName(
            self, "Importa Dati", "", "JSON Files (*.json)"
        )
        
        if filename:
            success, count = database.import_from_json(filename)
            if success:
                QMessageBox.information(self, "Import", f"Importati {count} ordini con successo!")
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Import", "Errore durante l'importazione")

    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self)
        # Store initial theme to check if it changed
        initial_theme = self.settings.get('theme', 'light')
        dialog.theme_changed.connect(self.apply_theme)
        
        if dialog.exec():
            # Reload settings
            self.settings = utils.Settings.load()
            
            # If theme didn't change (so apply_theme wasn't called via signal), 
            # we still need to refresh for other settings (like show_delivered)
            if self.settings.get('theme') == initial_theme:
                self.refresh_data()

    def apply_theme(self, theme_name):
        """Apply theme in real-time"""
        logger.info(f"Switching to {theme_name} theme...")
        from PyQt6.QtWidgets import QApplication
        QApplication.instance().setStyleSheet(utils.get_stylesheet(theme_name))
        
        # Update dashboard widget theme specifically
        if hasattr(self, 'dashboard'):
            self.dashboard.update_theme()
            
        # Update current settings object
        self.settings['theme'] = theme_name
        self.refresh_data()

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self, 
            "Informazioni",
            f"""<h3>{config.APP_NAME} v{config.APP_VERSION}</h3>
            <p>Gestisci le tue consegne in modo semplice e veloce.</p>
            <p><b>Autore:</b> {config.APP_AUTHOR}</p>
            <p><b>Sviluppo:</b> {config.APP_DEVELOPER}</p>
            <p><b>Supporto:</b> {config.APP_SUPPORT}</p>
            """
        )

    def sync_emails(self):
        """Synchronize orders with email updates"""
        from email_manager import EmailSyncManager
        
        # Check if email is enabled
        if not self.settings.get('email_sync_enabled', False):
            QMessageBox.warning(self, "Email Sync", "La sincronizzazione email non è abilitata nelle impostazioni.")
            return

        # Show progress
        progress = QMessageBox(self)
        progress.setWindowTitle("Sincronizzazione Email")
        progress.setText("Connessione a Hotmail in corso...")
        progress.setStandardButtons(QMessageBox.StandardButton.NoButton)
        progress.show()
        QApplication.processEvents()
        
        try:
            sync_manager = EmailSyncManager()
            count = sync_manager.sync_with_db()
            
            progress.close()
            
            if count > 0:
                QMessageBox.information(self, "Email Sync", f"Sincronizzazione completata!\nAggiornati {count} ordini con nuove informazioni.")
                self.refresh_data()
            else:
                # Specific check if no updates found
                QMessageBox.information(self, "Email Sync", "Nessun nuovo aggiornamento trovato nelle email.")
                
        except Exception as e:
            progress.close()
            logger.error(f"Sync error: {e}")
            QMessageBox.critical(self, "Errore Sync", f"Si è verificato un errore durante la sincronizzazione:\n{e}")
