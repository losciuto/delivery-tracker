import sys
import webbrowser
from datetime import datetime, date
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QDialog, QLabel,
    QLineEdit, QDateEdit, QCheckBox, QTextEdit, QMessageBox, QHeaderView,
    QAbstractItemView, QGroupBox, QFormLayout, QStyle
)
from PyQt6.QtCore import Qt, QDate, QSize
from PyQt6.QtGui import QColor, QBrush, QAction

import database

class OrderDialog(QDialog):
    def __init__(self, parent=None, order_data=None):
        super().__init__(parent)
        self.setWindowTitle("Dettagli Ordine")
        self.resize(600, 500) # Set a reasonable default size
        self.order_data = order_data
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        # --- Product Info Group ---
        product_group = QGroupBox("Informazioni Prodotto")
        product_layout = QFormLayout()
        
        self.platform_input = QLineEdit()
        product_layout.addRow("Piattaforma:", self.platform_input)
        
        self.seller_input = QLineEdit()
        product_layout.addRow("Venditore:", self.seller_input)
        
        self.desc_input = QLineEdit()
        product_layout.addRow("Descrizione:", self.desc_input)
        
        self.link_input = QLineEdit()
        product_layout.addRow("Link:", self.link_input)
        
        self.qty_input = QLineEdit()
        self.qty_input.setText("1")
        product_layout.addRow("Quantità:", self.qty_input)
        
        product_group.setLayout(product_layout)
        main_layout.addWidget(product_group)

        # --- Delivery Info Group ---
        delivery_group = QGroupBox("Dettagli Spedizione")
        delivery_layout = QFormLayout()
        
        self.destination_input = QLineEdit()
        delivery_layout.addRow("Destinazione:", self.destination_input)
        
        self.position_input = QLineEdit()
        delivery_layout.addRow("Posizione:", self.position_input)
        
        self.order_date_input = QDateEdit()
        self.order_date_input.setCalendarPopup(True)
        self.order_date_input.setDate(QDate.currentDate())
        delivery_layout.addRow("Data Ordine:", self.order_date_input)
        
        self.est_delivery_input = QDateEdit()
        self.est_delivery_input.setCalendarPopup(True)
        self.est_delivery_input.setDate(QDate.currentDate().addDays(7))
        delivery_layout.addRow("Consegna Prevista:", self.est_delivery_input)
        
        self.alarm_cb = QCheckBox("Abilita Allarme")
        self.delivered_cb = QCheckBox("Consegnato")
        
        checkbox_layout = QHBoxLayout()
        checkbox_layout.addWidget(self.alarm_cb)
        checkbox_layout.addWidget(self.delivered_cb)
        delivery_layout.addRow("Stato:", checkbox_layout)
        
        delivery_group.setLayout(delivery_layout)
        main_layout.addWidget(delivery_group)

        # --- Notes Group ---
        notes_group = QGroupBox("Note")
        notes_layout = QVBoxLayout()
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        notes_layout.addWidget(self.notes_input)
        notes_group.setLayout(notes_layout)
        main_layout.addWidget(notes_group)

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Salva")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Annulla")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

        if self.order_data:
            self.load_data()

    def load_data(self):
        self.platform_input.setText(self.order_data['platform'])
        self.seller_input.setText(self.order_data.get('seller', ''))
        self.destination_input.setText(self.order_data.get('destination', ''))
        self.desc_input.setText(self.order_data['description'])
        self.link_input.setText(self.order_data['link'])
        self.qty_input.setText(str(self.order_data['quantity']))
        
        od = datetime.strptime(self.order_data['order_date'], '%Y-%m-%d').date()
        self.order_date_input.setDate(QDate(od.year, od.month, od.day))
        
        if self.order_data['estimated_delivery']:
            ed = datetime.strptime(self.order_data['estimated_delivery'], '%Y-%m-%d').date()
            self.est_delivery_input.setDate(QDate(ed.year, ed.month, ed.day))
            
        self.alarm_cb.setChecked(bool(self.order_data['alarm_enabled']))
        self.delivered_cb.setChecked(bool(self.order_data['is_delivered']))
        self.position_input.setText(self.order_data.get('position', ''))
        self.notes_input.setText(self.order_data['notes'])

    def get_data(self):
        return {
            'platform': self.platform_input.text(),
            'seller': self.seller_input.text(),
            'destination': self.destination_input.text(),
            'description': self.desc_input.text(),
            'link': self.link_input.text(),
            'quantity': int(self.qty_input.text() or 1),
            'order_date': self.order_date_input.date().toString('yyyy-MM-dd'),
            'estimated_delivery': self.est_delivery_input.date().toString('yyyy-MM-dd'),
            'alarm_enabled': self.alarm_cb.isChecked(),
            'is_delivered': self.delivered_cb.isChecked(),
            'position': self.position_input.text(),
            'notes': self.notes_input.toPlainText()
        }

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scadenziario Consegne")
        self.resize(1300, 700)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        # Main layout is now Horizontal: Sidebar | Table
        self.layout = QHBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0) # Remove margins for full height sidebar

        self.setup_sidebar()
        self.setup_table()
        self.refresh_table()
        self.check_overdue_items()

    def setup_sidebar(self):
        # Sidebar Container
        self.sidebar_widget = QWidget()
        self.sidebar_widget.setObjectName("sidebar")
        self.sidebar_widget.setFixedWidth(200) # Initial width
        self.is_collapsed = False
        
        sidebar_layout = QVBoxLayout(self.sidebar_widget)
        sidebar_layout.setContentsMargins(5, 10, 5, 10)
        sidebar_layout.setSpacing(10)
        
        # Toggle Button (Hamburger)
        self.toggle_btn = QPushButton()
        # Initial icon: Arrow Left (since it starts expanded, clicking it will collapse)
        self.toggle_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowLeft))
        self.toggle_btn.clicked.connect(self.toggle_sidebar)
        self.toggle_btn.setFixedHeight(40)
        sidebar_layout.addWidget(self.toggle_btn)
        
        # Title (Hidden when collapsed)
        self.title_label = QLabel("MENU")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333; margin-bottom: 10px;")
        sidebar_layout.addWidget(self.title_label)
        
        # Buttons with Icons
        self.sidebar_buttons = []
        
        add_btn = self.create_sidebar_btn("Aggiungi", QStyle.StandardPixmap.SP_FileDialogNewFolder, self.add_order)
        sidebar_layout.addWidget(add_btn)

        edit_btn = self.create_sidebar_btn("Modifica", QStyle.StandardPixmap.SP_FileDialogDetailedView, self.edit_order)
        sidebar_layout.addWidget(edit_btn)

        del_btn = self.create_sidebar_btn("Elimina", QStyle.StandardPixmap.SP_TrashIcon, self.delete_order)
        sidebar_layout.addWidget(del_btn)

        refresh_btn = self.create_sidebar_btn("Aggiorna", QStyle.StandardPixmap.SP_BrowserReload, self.refresh_table)
        sidebar_layout.addWidget(refresh_btn)

        sidebar_layout.addStretch()

        about_btn = self.create_sidebar_btn("Info", QStyle.StandardPixmap.SP_MessageBoxInformation, self.show_about)
        sidebar_layout.addWidget(about_btn)
        
        self.layout.addWidget(self.sidebar_widget)

    def create_sidebar_btn(self, text, icon_pixmap, slot):
        btn = QPushButton(text)
        btn.setIcon(self.style().standardIcon(icon_pixmap))
        btn.clicked.connect(slot)
        btn.setFixedHeight(40)
        btn.setIconSize(QSize(24, 24))
        btn.setToolTip(text)
        self.sidebar_buttons.append((btn, text))
        return btn

    def toggle_sidebar(self):
        if self.is_collapsed:
            # Expand
            self.sidebar_widget.setFixedWidth(200)
            self.title_label.show()
            self.toggle_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowLeft))
            for btn, text in self.sidebar_buttons:
                btn.setText(text)
            self.is_collapsed = False
        else:
            # Collapse
            self.sidebar_widget.setFixedWidth(60)
            self.title_label.hide()
            self.toggle_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowRight))
            for btn, text in self.sidebar_buttons:
                btn.setText("")
            self.is_collapsed = True

    def show_about(self):
        msg = (
            "Scadenziario Consegne\n"
            "Versione 1.1.1\n"
            f"Data: {date.today().strftime('%d/%m/%Y')}\n\n"
            "Autore: Massimo Lo Sciuto\n"
            "Supporto: Antigravity\n"
            "Sviluppo: Gemini 3 Pro"
        )
        QMessageBox.information(self, "Informazioni", msg)

    def setup_table(self):
        self.table = QTableWidget()
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels([
            "ID", "Data", "Piattaforma", "Venditore", "Destinazione", "Descrizione", "Link", "Q.tà", "Cons. Prevista", "Posizione", "Consegnato", "Note"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.hideColumn(0) # Hide ID
        self.layout.addWidget(self.table)
        self.table.doubleClicked.connect(self.edit_order)
        self.table.cellClicked.connect(self.on_cell_clicked)

    def on_cell_clicked(self, row, column):
        # Link column is index 6 now (was 5)
        if column == 6:
            item = self.table.item(row, column)
            if item and item.text():
                webbrowser.open(item.text())

    def refresh_table(self):
        self.table.setSortingEnabled(False) # Disable sorting while populating
        self.table.setRowCount(0)
        orders = database.get_orders()
        
        for row, order in enumerate(orders):
            self.table.insertRow(row)
            
            self.table.setItem(row, 0, QTableWidgetItem(str(order['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(order['order_date']))
            self.table.setItem(row, 2, QTableWidgetItem(order['platform']))
            self.table.setItem(row, 3, QTableWidgetItem(order.get('seller', '')))
            self.table.setItem(row, 4, QTableWidgetItem(order.get('destination', '')))
            self.table.setItem(row, 5, QTableWidgetItem(order['description']))

            # Add tooltips to all items
            for col in range(6): # Columns 0-5
                item = self.table.item(row, col)
                if item:
                    item.setToolTip(item.text())
            
            link_item = QTableWidgetItem(order['link'])
            if order['link']:
                link_item.setForeground(QBrush(QColor("blue")))
                font = link_item.font()
                font.setUnderline(True)
                link_item.setFont(font)
            self.table.setItem(row, 6, link_item)
            
            self.table.setItem(row, 7, QTableWidgetItem(str(order['quantity'])))
            self.table.setItem(row, 8, QTableWidgetItem(order['estimated_delivery']))
            
            # Add "Posizione" column
            position_item = QTableWidgetItem(order.get('position', ''))
            self.table.setItem(row, 9, position_item)
            
            delivered_item = QTableWidgetItem("Sì" if order['is_delivered'] else "No")
            self.table.setItem(row, 10, delivered_item)
            
            self.table.setItem(row, 11, QTableWidgetItem(order['notes']))

            # Add tooltips to remaining items
            for col in range(6, 12):
                item = self.table.item(row, col)
                if item:
                    item.setToolTip(item.text())

            # Color delivered items green
            if order['is_delivered']:
                green_color = QColor(200, 255, 200)  # Light green
                for col in range(12):
                    item = self.table.item(row, col)
                    if item:
                        item.setBackground(green_color)
            # Alarm Logic for non-delivered items
            elif order['alarm_enabled']:
                est_date = datetime.strptime(order['estimated_delivery'], '%Y-%m-%d').date()
                today = date.today()
                
                color = None
                if est_date < today:
                    color = QColor(255, 200, 200) # Overdue - Red
                elif est_date == today:
                    color = QColor(255, 220, 150) # Due Today - Orange
                elif (est_date - today).days <= 2:
                    color = QColor(255, 255, 200) # Upcoming - Yellow
                
                if color:
                    for col in range(12):
                        item = self.table.item(row, col)
                        if item:
                            item.setBackground(color)
        
        self.table.setSortingEnabled(True)

    def check_overdue_items(self):
        orders = database.get_orders()
        overdue_items = []
        today = date.today()
        
        for order in orders:
            if not order['is_delivered'] and order['alarm_enabled']:
                est_date = datetime.strptime(order['estimated_delivery'], '%Y-%m-%d').date()
                if est_date < today:
                    overdue_items.append(f"- {order['description']} (Scadenza: {order['estimated_delivery']})")
        
        if overdue_items:
            msg = "I seguenti articoli sono scaduti:\n\n" + "\n".join(overdue_items)
            QMessageBox.warning(self, "Consegne Scadute", msg)

    def add_order(self):
        dialog = OrderDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            database.add_order(data)
            self.refresh_table()

    def edit_order(self):
        selected = self.table.selectedItems()
        if not selected:
            return
        
        row = selected[0].row()
        # Since sorting is enabled, the row index might not match the visual order if we just use row
        # But we are getting the item from the table, so it should be fine.
        # However, we need to be careful about hidden columns.
        # The ID is in column 0.
        order_id = int(self.table.item(row, 0).text())
        
        all_orders = database.get_orders()
        order_data = next((o for o in all_orders if o['id'] == order_id), None)
        
        if order_data:
            dialog = OrderDialog(self, order_data)
            if dialog.exec():
                new_data = dialog.get_data()
                database.update_order(order_id, new_data)
                self.refresh_table()

    def delete_order(self):
        selected = self.table.selectedItems()
        if not selected:
            return
            
        row = selected[0].row()
        order_id = int(self.table.item(row, 0).text())
        
        confirm = QMessageBox.question(
            self, "Conferma Eliminazione", 
            "Sei sicuro di voler eliminare questo ordine?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            database.delete_order(order_id)
            self.refresh_table()
