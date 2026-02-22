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
    QStackedWidget, QMenu, QApplication, QProgressDialog
)
from PyQt6.QtCore import Qt, QSize, QTimer, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QColor, QBrush, QAction, QKeySequence, QShortcut, QPixmap, QIcon

import database
import config
import utils
from widgets import DashboardWidget, SearchFilterBar
from gui.dialogs import OrderDialog, SettingsDialog
from gui.import_file_dialog import ImportFileDialog

logger = utils.get_logger(__name__)

class NumericTableWidgetItem(QTableWidgetItem):
    """Table widget item that sorts numerically rather than alphabetically"""
    def __lt__(self, other):
        if isinstance(other, QTableWidgetItem):
            try:
                # Try to convert both values to float for comparison
                return float(self.text()) < float(other.text())
            except (ValueError, TypeError):
                # Fallback to string comparison if one isn't a number
                return super().__lt__(other)
        return super().__lt__(other)

class SyncWorker(QObject):
    """Worker for asynchronous email synchronization"""
    finished = pyqtSignal(int, int) # count, img_count
    error = pyqtSignal(str)

    def run(self):
        try:
            from email_manager import EmailSyncManager
            import database
            sync_manager = EmailSyncManager()
            count = sync_manager.sync_with_db()
            img_count = database.batch_download_images()
            self.finished.emit(count, img_count)
        except Exception as e:
            # Assicuriamoci che l'errore venga propagato alla UI
            self.error.emit(str(e))


class ImageRepairWorker(QObject):
    """Worker for asynchronous image downloading/repairing"""
    finished = pyqtSignal(int)
    error = pyqtSignal(str)

    def run(self):
        try:
            import database
            img_count = database.batch_download_images()
            self.finished.emit(img_count)
        except Exception as e:
            self.error.emit(str(e))


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
        self.current_delivery_filter = 'all'  # 'all', 'pending', 'delivered', 'overdue'
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
        self.dashboard.card_clicked.connect(self.on_dashboard_card_clicked)
        self.content_stack.addWidget(self.dashboard)

        main_layout.addWidget(self.content_stack)

        # Setup menu bar
        self.setup_menubar()

        # Keyboard shortcuts
        self.dup_shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
        self.dup_shortcut.activated.connect(self.duplicate_order)

    def setup_sidebar(self):
        """Setup sidebar with navigation"""
        self.sidebar_widget = QWidget()
        self.sidebar_widget.setObjectName("sidebar")
        self.sidebar_widget.setFixedWidth(config.SIDEBAR_WIDTH_EXPANDED)
        self.is_collapsed = False

        sidebar_layout = QVBoxLayout(self.sidebar_widget)
        sidebar_layout.setContentsMargins(10, 5, 10, 5)
        sidebar_layout.setSpacing(5)

        # Toggle button
        self.toggle_btn = QPushButton()
        self.toggle_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowLeft))
        self.toggle_btn.clicked.connect(self.toggle_sidebar)
        self.toggle_btn.setFixedHeight(40)
        sidebar_layout.addWidget(self.toggle_btn)

        # Title
        self.title_label = QLabel("MENU")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 2px;")
        sidebar_layout.addWidget(self.title_label)

        # Navigation buttons
        self.sidebar_buttons = []

        # View buttons
        view_label = QLabel("VISUALIZZA")
        view_label.setStyleSheet("font-size: 11px; color: #757575; margin-top: 5px;")
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
        action_label.setStyleSheet("font-size: 11px; color: #757575; margin-top: 5px;")
        sidebar_layout.addWidget(action_label)
        self.sidebar_buttons.append((action_label, ""))

        add_btn = self.create_sidebar_btn("Aggiungi", QStyle.StandardPixmap.SP_FileDialogNewFolder, self.add_order)
        sidebar_layout.addWidget(add_btn)

        refresh_btn = self.create_sidebar_btn("Aggiorna", QStyle.StandardPixmap.SP_BrowserReload, self.refresh_data)
        sidebar_layout.addWidget(refresh_btn)

        dup_btn = self.create_sidebar_btn("Duplica", QStyle.StandardPixmap.SP_FileDialogDetailedView, self.duplicate_order)
        sidebar_layout.addWidget(dup_btn)

        edit_btn = self.create_sidebar_btn("Modifica", QStyle.StandardPixmap.SP_FileIcon, self.edit_order)
        sidebar_layout.addWidget(edit_btn)

        del_btn = self.create_sidebar_btn("Elimina", QStyle.StandardPixmap.SP_TrashIcon, self.delete_order)
        sidebar_layout.addWidget(del_btn)

        file_btn = self.create_sidebar_btn("Importa File", QStyle.StandardPixmap.SP_FileDialogStart, self.import_from_file)
        sidebar_layout.addWidget(file_btn)

        sidebar_layout.addStretch()

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
        self.table.setColumnCount(20)
        self.table.setHorizontalHeaderLabels([
            "ID", "Data", "Piattaforma", "Venditore", "Destinazione", "Descrizione",
            "ID Ordine Sito", "Stato", "Link", "Q.tà", "Cons. Prevista", "Posizione",
            "N. Tracking", "Vettore", "Ultimo Miglio",
            "Categoria", "Consegnato", "Note", "Prezzo", "Immagine"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.setAlternatingRowColors(True)
        self.table.hideColumn(0)  # Hide ID

        # Adjust column widths
        self.table.setColumnWidth(5, 250)  # Descrizione (Initial width)
        self.table.setColumnWidth(10, 160) # Cons. Prevista
        self.table.setColumnWidth(1, 100)  # Data
        self.table.setColumnWidth(9, 60)   # Q.tà
        self.table.setColumnWidth(16, 100) # Consegnato
        self.table.setColumnWidth(18, 80)  # Prezzo
        self.table.setColumnWidth(19, 200) # Immagine

        # Behavior for other columns
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)  # Descrizione (Now resizable)
        header.setSectionResizeMode(17, QHeaderView.ResizeMode.Stretch) # Note

        # Interactive for most, but ensure good initial fit
        for i in [2, 3, 4, 6, 7, 8, 11, 12, 13, 14, 15]:
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
            self.table.setColumnWidth(i, 130)

        self.table.doubleClicked.connect(self.edit_order)
        self.table.cellClicked.connect(self.on_cell_clicked)
        self.table.itemSelectionChanged.connect(self.highlight_related_orders)

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
 
        import_file_action = QAction("📂 Importa File (Excel/CSV/JSON)", self)
        import_file_action.triggered.connect(self.import_from_file)
        import_menu.addAction(import_file_action)

        import_json_action = QAction("Importa JSON (senza anteprima)", self)
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
        self.tools_menu = menubar.addMenu("&Strumenti")

        self.sync_email_action = QAction("📧 Sincronizza Email", self)
        self.sync_email_action.triggered.connect(self.sync_emails)
        self.tools_menu.addAction(self.sync_email_action)

        self.repair_images_action = QAction("🖼️ Ripara Immagini Mancanti", self)
        self.repair_images_action.triggered.connect(self.repair_images)
        self.tools_menu.addAction(self.repair_images_action)

        self.tools_menu.addSeparator()

        self.settings_action_menu = QAction("⚙️ Impostazioni", self)
        self.settings_action_menu.triggered.connect(self.show_settings)
        self.tools_menu.addAction(self.settings_action_menu)

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

        duplicate_action = menu.addAction("Duplica")
        duplicate_action.triggered.connect(self.duplicate_order)

        delete_action = menu.addAction("Elimina")
        delete_action.triggered.connect(self.delete_order)

        menu.addSeparator()

        mark_delivered_action = menu.addAction("Segna come Consegnato")
        mark_delivered_action.triggered.connect(lambda: self.mark_delivered(True))

        mark_not_delivered_action = menu.addAction("Segna come Non Consegnato")
        mark_not_delivered_action.triggered.connect(lambda: self.mark_delivered(False))

        menu.exec(self.table.viewport().mapToGlobal(position))

    def on_cell_clicked(self, row, column):
        """Handle cell click (for links and tracking)"""
        if column == 8:  # Link column
            item = self.table.item(row, column)
            if item and item.text():
                webbrowser.open(item.text())
        elif column == 12:  # Tracking number column
            item = self.table.item(row, column)
            carrier_item = self.table.item(row, 13)
            if item and item.text():
                tracking_number = item.text()
                carrier = carrier_item.text() if carrier_item else None
                url = utils.TrackingHelper.get_tracking_url(tracking_number, carrier)
                if url:
                    webbrowser.open(url)
                else:
                    QMessageBox.information(self, "Tracking", f"Impossibile generare link di tracking per: {tracking_number}")
        elif column == 19:  # Immagine URL column
            item = self.table.item(row, column)
            if item and item.text():
                webbrowser.open(item.text())

    def on_search_changed(self, search_text):
        """Handle search text change"""
        self.current_search = search_text
        self.current_delivery_filter = 'all'  # Reset dashboard-specific filter
        self.refresh_table()

    def on_filter_changed(self, filters):
        """Handle filter change"""
        self.current_platform_filter = filters.get('platform', '')
        self.current_category_filter = filters.get('category', '')
        self.settings['show_delivered'] = filters.get('show_delivered', True)
        self.current_delivery_filter = 'all'  # Reset dashboard-specific filter
        self.refresh_table()

    def on_dashboard_card_clicked(self, filter_type):
        """Handle clicks on dashboard cards to filter orders."""
        logger.info(f"Dashboard card clicked: {filter_type}")
        self.current_delivery_filter = filter_type
        self.content_stack.setCurrentIndex(0)  # Switch to orders view
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

        # Get matching orders
        include_delivered = self.settings.get('show_delivered', True)
        
        orders = database.get_orders(
            include_delivered=include_delivered,
            search=self.current_search,
            platform_filter=self.current_platform_filter,
            category_filter=self.current_category_filter,
            delivery_mode=self.current_delivery_filter
        )

        # Determine current theme colors
        theme_name = self.settings.get('theme', 'light')
        colors = config.LIGHT_THEME if theme_name == 'light' else config.DARK_THEME

        # Count occurrences of site_order_id to identify duplicates
        id_counts = {}
        for order in orders:
            site_id = order.get('site_order_id', '').strip()
            if site_id:
                id_counts[site_id] = id_counts.get(site_id, 0) + 1

        for row, order in enumerate(orders):
            self.table.insertRow(row)

            # Add data to cells
            self.table.setItem(row, 0, NumericTableWidgetItem(str(order['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(order.get('order_date', '')))
            self.table.setItem(row, 2, QTableWidgetItem(order.get('platform', '')))
            self.table.setItem(row, 3, QTableWidgetItem(order.get('seller', '')))
            self.table.setItem(row, 4, QTableWidgetItem(order.get('destination', '')))
            self.table.setItem(row, 5, QTableWidgetItem(order.get('description', '')))
            
            site_id = order.get('site_order_id', '')
            site_id_text = site_id
            if site_id and id_counts.get(site_id, 0) > 1:
                site_id_text = f"🔗 {site_id}"
            
            self.table.setItem(row, 6, QTableWidgetItem(site_id_text))

            status_item = QTableWidgetItem(order.get('status', 'In Attesa'))
            # Format status color based on text
            if order.get('status') == 'Consegnato':
                status_item.setForeground(QBrush(QColor("green")))
            elif order.get('status') == 'Spedito' or order.get('status') == 'In Transito':
                status_item.setForeground(QBrush(QColor("#2196F3")))
            elif order.get('status') == 'In Consegna':
                status_item.setForeground(QBrush(QColor("#FF9800")))
            elif order.get('status') == 'Problema/Eccezione':
                status_item.setForeground(QBrush(QColor("red")))

            self.table.setItem(row, 7, status_item)

            # Link with formatting
            link_item = QTableWidgetItem(order.get('link', ''))
            if order.get('link'):
                link_item.setForeground(QBrush(QColor("blue") if theme_name == 'light' else QColor("#64B5F6")))
                font = link_item.font()
                font.setUnderline(True)
                link_item.setFont(font)
            self.table.setItem(row, 8, link_item)

            self.table.setItem(row, 9, NumericTableWidgetItem(str(order.get('quantity', 1))))
            self.table.setItem(row, 10, QTableWidgetItem(order.get('estimated_delivery', '')))
            self.table.setItem(row, 11, QTableWidgetItem(order.get('position', '')))
            
            # Tracking number with link-like formatting
            tracking = order.get('tracking_number', '')
            tracking_item = QTableWidgetItem(tracking)
            if tracking:
                tracking_item.setForeground(QBrush(QColor("blue") if theme_name == 'light' else QColor("#64B5F6")))
                font = tracking_item.font()
                font.setUnderline(True)
                tracking_item.setFont(font)
                tracking_item.setToolTip(f"📑 Clicca per tracciare la spedizione:\n{tracking}")
            self.table.setItem(row, 12, tracking_item)
            
            self.table.setItem(row, 13, QTableWidgetItem(order.get('carrier', '')))
            self.table.setItem(row, 14, QTableWidgetItem(order.get('last_mile_carrier', '')))
            self.table.setItem(row, 15, QTableWidgetItem(order.get('category', '')))
            self.table.setItem(row, 16, QTableWidgetItem("Sì" if order.get('is_delivered') else "No"))
            self.table.setItem(row, 17, QTableWidgetItem(order.get('notes', '')))

            # Prezzo (col 18)
            price = order.get('price')
            price_text = f"\u20ac {price:.2f}" if price is not None else ''
            self.table.setItem(row, 18, QTableWidgetItem(price_text))

            # Immagine URL (col 19) — cliccabile come link o thumbnail
            image_url = order.get('image_url', '')
            image_blob = order.get('image_blob')
            image_item = QTableWidgetItem()
            
            if image_blob:
                # Show thumbnail as icon if blob is available
                pixmap = QPixmap()
                pixmap.loadFromData(image_blob)
                if not pixmap.isNull():
                    thumbnail = pixmap.scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    image_item.setIcon(QIcon(thumbnail))
                    image_item.setText("") # Don't show URL text if we have the icon
            elif image_url:
                image_item.setText(image_url)
                image_item.setForeground(QBrush(QColor("blue") if theme_name == 'light' else QColor("#64B5F6")))
                font = image_item.font()
                font.setUnderline(True)
                image_item.setFont(font)
            
            if image_url:
                image_item.setToolTip(f"🖼 Clicca per aprire l'immagine:\n{image_url}")
            
            self.table.setItem(row, 19, image_item)
            # Make row taller if we have images
            if image_blob:
                self.table.setRowHeight(row, 65)
            else:
                self.table.setRowHeight(row, 30) # Default height

            # Add tooltips with image preview
            # Use BLOB images for speed/offline access, fallback to URL
            image_url = order.get('image_url', '')
            image_blob = order.get('image_blob')
            
            tooltip_image_src = None
            if image_blob:
                tooltip_image_src = utils.ImageDownloader.to_base64(image_blob)
            elif image_url:
                tooltip_image_src = image_url

            for col in range(20):
                item = self.table.item(row, col)
                if item:
                    text = item.text()
                    if tooltip_image_src:
                        # Rich HTML tooltip with image
                        tooltip_html = (
                            f"<div style='margin: 5px; width: 160px;'>"
                            f"<p style='margin: 0 0 5px 0;'><b>{text}</b></p>"
                            f"<hr style='border: 0; border-top: 1px solid #ddd; margin-bottom: 5px;'>"
                            f"<img src='{tooltip_image_src}' width='150' height='150' style='border: 1px solid #ccc; background: white;'>"
                            f"</div>"
                        )
                        item.setToolTip(tooltip_html)
                    else:
                        item.setToolTip(text)

            # Color rows based on status
            status = order.get('status')
            if status == 'Rimborsato':
                color = QColor(colors.refunded)
            elif status == 'Annullato':
                color = QColor(colors.cancelled)
            elif order.get('is_delivered'):
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
                for col in range(20):
                    item = self.table.item(row, col)
                    if item:
                        item.setBackground(color)
                        # Ensure text is readable on colored background
                        item.setForeground(QBrush(QColor("black") if theme_name == 'light' else QColor("white")))

            # Save original background color as data for easy restoration
            for col in range(20):
                item = self.table.item(row, col)
                if item:
                    item.setData(Qt.ItemDataRole.UserRole, color)
        
        self.table.setSortingEnabled(True)
        logger.info(f"Table refreshed with {len(orders)} orders")

    def refresh_dashboard(self):
        """Refresh dashboard with current data"""
        orders = database.get_orders()
        self.dashboard.update_stats(orders)

    def highlight_related_orders(self):
        """Highlight rows sharing the same Site Order ID as the selected one (optimized)"""
        selected_items = self.table.selectedItems()
        if not selected_items:
            self.clear_highlights()
            return

        row = selected_items[0].row()
        item = self.table.item(row, 6)
        if not item:
            self.clear_highlights()
            return
            
        site_id = item.text().replace("🔗 ", "").strip()
        if not site_id:
            self.clear_highlights()
            return

        logger.debug(f"Highlighting related orders for SiteID: {site_id}")

        # Highlight color (using distinct colors from status colors)
        theme_name = self.settings.get('theme', 'light')
        # Light blue for light theme, blue-grey for dark
        highlight_color = QColor("#E3F2FD") if theme_name == 'light' else QColor("#34495E")
        
        self.table.blockSignals(True)
        
        match_count = 0
        for r in range(self.table.rowCount()):
            current_id_item = self.table.item(r, 6)
            if not current_id_item: continue
            
            current_id = current_id_item.text().replace("🔗 ", "").strip()
            
            if current_id == site_id:
                match_count += 1
                for c in range(self.table.columnCount()):
                    cell = self.table.item(r, c)
                    if cell:
                        cell.setBackground(highlight_color)
            else:
                self.restore_row_visuals(r, theme_name)
        
        self.table.blockSignals(False)
        if match_count > 1:
            logger.info(f"Highlighted {match_count} rows for SiteID {site_id}")

    def clear_highlights(self):
        """Clear all correlation highlights (optimized)"""
        theme_name = self.settings.get('theme', 'light')
        self.table.blockSignals(True)
        for r in range(self.table.rowCount()):
            self.restore_row_visuals(r, theme_name)
        self.table.blockSignals(False)

    def restore_row_visuals(self, row, theme_name):
        """Restore row color from UserRole data previously saved during refresh"""
        colors = config.LIGHT_THEME if theme_name == 'light' else config.DARK_THEME
        
        for c in range(self.table.columnCount()):
            cell = self.table.item(row, c)
            if cell:
                # Retrieve the original status color saved in UserRole
                orig_color = cell.data(Qt.ItemDataRole.UserRole)
                
                if orig_color:
                    cell.setBackground(orig_color)
                else:
                    # Default background if no status color (alternating)
                    default_bg = QColor(colors.bg_table) if row % 2 == 0 else QColor(colors.bg_table_alternate)
                    cell.setBackground(default_bg)
                
                # Restore foreground based on theme and special columns
                cell.setForeground(QBrush(QColor("black") if theme_name == 'light' else QColor("white")))
                
                # Column 7: Status
                if c == 7:
                    status_text = cell.text()
                    if status_text == 'Consegnato':
                        cell.setForeground(QBrush(QColor("green")))
                    elif status_text in ['Spedito', 'In Transito']:
                        cell.setForeground(QBrush(QColor("#2196F3")))
                    elif status_text == 'In Consegna':
                        cell.setForeground(QBrush(QColor("#FF9800")))
                    elif status_text == 'Problema/Eccezione':
                        cell.setForeground(QBrush(QColor("red")))
                
                # Column 8: Link
                elif c == 8 and cell.text():
                    cell.setForeground(QBrush(QColor("blue") if theme_name == 'light' else QColor("#64B5F6")))

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

    def add_order(self, initial_data=None):
        """Add a new order"""
        dialog = OrderDialog(self, order_data=initial_data)
        if dialog.exec():
            data = dialog.get_data()
            order_id = database.add_order(data)
            if order_id:
                QMessageBox.information(self, "Successo", "Ordine aggiunto con successo!")
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Errore", "Errore durante l'aggiunta dell'ordine")

    def import_from_file(self):
        """Open the file import dialog (Excel/CSV/JSON) with preview."""
        dialog = ImportFileDialog(self)
        if dialog.exec():
            self.refresh_data()

    def duplicate_order(self):
        """Duplicate selected order"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Selezione", "Seleziona un ordine dalla tabella per duplicarlo")
            return
            
        order_id = int(self.table.item(row, 0).text())
        order_data = database.get_order_by_id(order_id)
        
        if order_data:
            # We pass the data to add_order, but we might want to clear some unique fields
            # For duplication, usually all fields are kept and user modifies what's needed
            self.add_order(initial_data=dict(order_data))

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
        """Synchronize orders with email updates asynchronously"""
        # Check if email is enabled
        if not self.settings.get('email_sync_enabled', False):
            QMessageBox.warning(self, "Email Sync", "La sincronizzazione email non è abilitata nelle impostazioni.")
            return

        # Disable sync action during process
        self.sync_email_action.setEnabled(False)
        
        # Show non-blocking progress dialog
        self.progress_dialog = QProgressDialog("Sincronizzazione in corso...", None, 0, 0, self)
        self.progress_dialog.setWindowTitle("Sincronizzazione Email")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setCancelButton(None) # Disable cancel for now as it needs worker handling
        self.progress_dialog.show()
        
        # Setup Thread and Worker
        self.sync_thread = QThread()
        self.sync_worker = SyncWorker()
        self.sync_worker.moveToThread(self.sync_thread)
        
        # Connect signals
        self.sync_thread.started.connect(self.sync_worker.run)
        self.sync_worker.finished.connect(self.on_sync_finished)
        self.sync_worker.error.connect(self.on_sync_error)
        
        # Cleanup when finished
        self.sync_worker.finished.connect(self.sync_thread.quit)
        self.sync_worker.error.connect(self.sync_thread.quit)
        self.sync_worker.finished.connect(self.sync_worker.deleteLater)
        self.sync_worker.error.connect(self.sync_worker.deleteLater)
        self.sync_thread.finished.connect(self.sync_thread.deleteLater)
        
        # Start the thread
        self.sync_thread.start()

    def on_sync_finished(self, count, img_count=0):
        """Handle sync completion"""
        logger.info(f"MAIN-WINDOW: Sincronizzazione terminata con successo ({count} aggiornamenti, {img_count} immagini)")
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
            del self.progress_dialog
        
        self.sync_email_action.setEnabled(True)
        
        msg_parts = []
        if count > 0:
            msg_parts.append(f"Aggiornati {count} ordini con nuove informazioni.")
        else:
            msg_parts.append("Nessun nuovo aggiornamento trovato nelle email.")
            
        if img_count > 0:
            msg_parts.append(f"Recuperate {img_count} immagini mancanti.")
            
        QMessageBox.information(self, "Email Sync", "\n".join(msg_parts))
        if count > 0 or img_count > 0:
            self.refresh_data()

    def repair_images(self):
        """Manually trigger image repair"""
        self.repair_images_action.setEnabled(False)
        self.progress_dialog = QProgressDialog("Recupero immagini in corso...", None, 0, 0, self)
        self.progress_dialog.setWindowTitle("Ripara Immagini")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setCancelButton(None)
        self.progress_dialog.show()

        self.repair_thread = QThread()
        self.repair_worker = ImageRepairWorker()
        self.repair_worker.moveToThread(self.repair_thread)
        
        self.repair_thread.started.connect(self.repair_worker.run)
        self.repair_worker.finished.connect(self.on_repair_finished)
        self.repair_worker.error.connect(self.on_repair_error)
        
        self.repair_worker.finished.connect(self.repair_thread.quit)
        self.repair_worker.error.connect(self.repair_thread.quit)
        self.repair_worker.finished.connect(self.repair_worker.deleteLater)
        self.repair_worker.error.connect(self.repair_worker.deleteLater)
        self.repair_thread.finished.connect(self.repair_thread.deleteLater)
        
        self.repair_thread.start()

    def on_repair_finished(self, img_count):
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
            del self.progress_dialog
            
        self.repair_images_action.setEnabled(True)
        if img_count > 0:
            QMessageBox.information(self, "Ripara Immagini", f"Recuperate {img_count} immagini con successo!")
            self.refresh_data()
        else:
            QMessageBox.information(self, "Ripara Immagini", "Nessuna immagine mancante trovata.\nTutte le immagini sono presenti.")

    def on_repair_error(self, error_msg):
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
            del self.progress_dialog
            
        self.repair_images_action.setEnabled(True)
        QMessageBox.critical(self, "Errore", f"Errore durante il recupero:\n{error_msg}")

    def on_sync_error(self, error_msg):
        """Handle sync error"""
        logger.error(f"MAIN-WINDOW: Segnale errore ricevuto: {error_msg}")
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
            del self.progress_dialog
            
        self.sync_email_action.setEnabled(True)
        QMessageBox.critical(self, "Errore Sync", f"Si è verificato un errore durante la sincronizzazione:\n{error_msg}")
