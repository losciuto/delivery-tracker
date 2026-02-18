"""
Import HTML Dialog for Delivery Tracker.
Allows the user to paste raw HTML from an order page and import the extracted orders.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QAbstractItemView, QCheckBox, QWidget, QSplitter,
    QGroupBox, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QColor, QBrush, QFont

import database
import utils

logger = utils.get_logger(__name__)


class ParseWorker(QObject):
    """Worker for async HTML parsing (avoids UI freeze on large HTML)"""
    finished = pyqtSignal(dict)  # Now emits a dict with metadata
    error = pyqtSignal(str)

    def __init__(self, html: str):
        super().__init__()
        self.html = html

    def run(self):
        try:
            from html_order_parser import HtmlOrderParser
            parser = HtmlOrderParser()
            results = parser.parse_with_meta(self.html)
            self.finished.emit(results)
        except Exception as e:
            logger.exception("Errore durante il parsing HTML")
            self.error.emit(str(e))


class ImportHtmlDialog(QDialog):
    """Dialog to paste HTML source and import extracted orders."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📋 Importa Ordini da HTML")
        self.resize(900, 680)
        self._parsed_orders = []
        self._duplicate_map = {}   # row_index -> existing DB order dict
        self._thread = None
        self._worker = None
        self.setup_ui()

    # ──────────────────────────────────────────────────────────────────────
    # UI Setup
    # ──────────────────────────────────────────────────────────────────────

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # ── Instructions ──────────────────────────────────────────────────
        info_label = QLabel(
            "ℹ️  <b>Come si usa:</b> Apri la pagina del tuo ordine nel tuo browser abituale (Chrome/Firefox/ecc.), premi "
            "<b>Ctrl+U</b> (o tasto destro → <i>Visualizza sorgente pagina</i>), "
            "seleziona tutto (<b>Ctrl+A</b>), copia (<b>Ctrl+C</b>) e incolla qui sotto.<br><br>"
            "💡 <i>Nota:</b> Per AliExpress e Temu questa procedura manuale è più affidabile dell'importazione da URL."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(
            "background:#E3F2FD; border:1px solid #90CAF9; border-radius:6px; padding:8px;"
        )
        layout.addWidget(info_label)

        # ── Splitter: paste area + preview table ──────────────────────────
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Paste area
        paste_group = QGroupBox("📄 Sorgente HTML")
        paste_layout = QVBoxLayout(paste_group)
        self.html_input = QTextEdit()
        self.html_input.setPlaceholderText(
            "Incolla qui il sorgente HTML della pagina ordine…\n\n"
            "Supportati: Amazon, Temu, eBay, AliExpress, Zalando e altri."
        )
        self.html_input.setFont(QFont("Courier New", 9))
        paste_layout.addWidget(self.html_input)
        splitter.addWidget(paste_group)

        # Preview table
        preview_group = QGroupBox("🔍 Anteprima articoli estratti")
        preview_layout = QVBoxLayout(preview_group)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            "✓", "Piattaforma", "ID Ordine", "Descrizione",
            "Q.tà", "Tracking", "Stato", "Cons. Prevista"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 30)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 160)
        self.table.setColumnWidth(4, 50)
        self.table.setColumnWidth(5, 160)
        self.table.setColumnWidth(6, 120)
        self.table.setColumnWidth(7, 120)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        preview_layout.addWidget(self.table)

        # Select all / none row
        sel_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("Seleziona tutti")
        self.select_all_btn.setFixedHeight(28)
        self.select_all_btn.clicked.connect(self._select_all)
        self.select_none_btn = QPushButton("Deseleziona tutti")
        self.select_none_btn.setFixedHeight(28)
        self.select_none_btn.clicked.connect(self._select_none)
        sel_layout.addWidget(self.select_all_btn)
        sel_layout.addWidget(self.select_none_btn)
        sel_layout.addStretch()
        self.result_label = QLabel("")
        sel_layout.addWidget(self.result_label)
        preview_layout.addLayout(sel_layout)

        splitter.addWidget(preview_group)
        splitter.setSizes([250, 350])
        layout.addWidget(splitter)

        # ── Progress bar (hidden by default) ─────────────────────────────
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # indeterminate
        self.progress.hide()
        layout.addWidget(self.progress)

        # ── Buttons ───────────────────────────────────────────────────────
        btn_layout = QHBoxLayout()

        self.analyze_btn = QPushButton("🔍 Analizza HTML")
        self.analyze_btn.setFixedHeight(40)
        self.analyze_btn.setDefault(True)
        self.analyze_btn.clicked.connect(self._analyze)

        self.import_btn = QPushButton("✅ Importa Selezionati")
        self.import_btn.setFixedHeight(40)
        self.import_btn.setEnabled(False)
        self.import_btn.clicked.connect(self._import_selected)

        cancel_btn = QPushButton("❌ Annulla")
        cancel_btn.setFixedHeight(40)
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(self.analyze_btn)
        btn_layout.addWidget(self.import_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    # ──────────────────────────────────────────────────────────────────────
    # Slots
    # ──────────────────────────────────────────────────────────────────────

    def _analyze(self):
        html = self.html_input.toPlainText().strip()
        if not html:
            QMessageBox.warning(self, "Attenzione", "Incolla prima il sorgente HTML della pagina ordine.")
            return

        self.analyze_btn.setEnabled(False)
        self.import_btn.setEnabled(False)
        self.progress.show()
        self.table.setRowCount(0)
        self.result_label.setText("Analisi in corso…")

        # Run parser in a background thread
        self._thread = QThread()
        self._worker = ParseWorker(html)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_parse_done)
        self._worker.error.connect(self._on_parse_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._thread.start()

    def _on_parse_done(self, result: dict):
        self.progress.hide()
        self.analyze_btn.setEnabled(True)
        
        orders = result.get('orders', [])
        platform = result.get('platform', 'Sconosciuto')
        warning = result.get('warning')
        
        self._parsed_orders = orders

        if warning:
            self.result_label.setText(f"⚠️ {platform}: Pagina non valida")
            QMessageBox.warning(self, "Attenzione", warning)
            return

        if not orders:
            self.result_label.setText(f"⚠️ {platform}: Nessun ordine trovato")
            QMessageBox.information(
                self, "Nessun risultato",
                f"Non è stato possibile estrarre ordini da {platform}.\n\n"
                "Assicurati di aver incollato il sorgente (Ctrl+U) della pagina DETTAGLIO ordine."
            )
            return

        self.result_label.setText(f"✅ {platform}: {len(orders)} articoli trovati")
        self._populate_table(orders)
        self.import_btn.setEnabled(True)

        dup_count = len(self._duplicate_map)
        if dup_count:
            self.result_label.setText(
                f"✅ {len(orders)} articolo/i trovato/i  ·  "
                f"⚠️ {dup_count} già presente/i in DB"
            )
        else:
            self.result_label.setText(f"✅ {len(orders)} articolo/i trovato/i")

    def _on_parse_error(self, error_msg: str):
        self.progress.hide()
        self.analyze_btn.setEnabled(True)
        self.result_label.setText("❌ Errore durante l'analisi")
        QMessageBox.critical(self, "Errore", f"Errore durante l'analisi HTML:\n{error_msg}")
        logger.error(f"HTML-IMPORT: Errore parser: {error_msg}")

    def _find_duplicates(self, orders: list) -> dict:
        """
        Check each parsed order against the DB.
        Returns a dict {row_index: existing_order_dict} for duplicates found.
        Matches on site_order_id (priority) or tracking_number.
        """
        all_orders = database.get_orders(include_delivered=True)
        dup_map = {}
        for row, order in enumerate(orders):
            new_site_id  = (order.get('site_order_id') or '').strip()
            new_tracking = (order.get('tracking_number') or '').strip()
            for existing in all_orders:
                ex_site_id  = (existing.get('site_order_id') or '').strip()
                ex_tracking = (existing.get('tracking_number') or '').strip()
                matched = False
                if new_site_id and ex_site_id and new_site_id == ex_site_id:
                    matched = True
                elif new_tracking and ex_tracking and new_tracking == ex_tracking:
                    matched = True
                if matched:
                    dup_map[row] = existing
                    break
        return dup_map

    def _populate_table(self, orders: list):
        self.table.setRowCount(0)
        status_colors = {
            'Consegnato':         '#C8E6C9',
            'In Consegna':        '#FFE0B2',
            'In Transito':        '#BBDEFB',
            'Spedito':            '#E3F2FD',
            'Problema/Eccezione': '#FFCDD2',
            'In Attesa':          '#F5F5F5',
        }

        self._duplicate_map = self._find_duplicates(orders)

        for row, order in enumerate(orders):
            self.table.insertRow(row)

            is_dup = row in self._duplicate_map

            # Checkbox column — duplicates start unchecked
            chk_widget = QWidget()
            chk_layout = QHBoxLayout(chk_widget)
            chk_layout.setContentsMargins(4, 0, 4, 0)
            chk_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chk = QCheckBox()
            chk.setChecked(not is_dup)   # pre-deselect duplicates
            chk_layout.addWidget(chk)
            self.table.setCellWidget(row, 0, chk_widget)

            self.table.setItem(row, 1, QTableWidgetItem(order.get('platform', '')))
            self.table.setItem(row, 2, QTableWidgetItem(order.get('site_order_id', '')))
            self.table.setItem(row, 3, QTableWidgetItem(order.get('description', '')))
            self.table.setItem(row, 4, QTableWidgetItem(str(order.get('quantity', 1))))
            self.table.setItem(row, 5, QTableWidgetItem(order.get('tracking_number', '')))

            status = order.get('status', 'In Attesa')
            status_item = QTableWidgetItem(status)
            bg = status_colors.get(status, '#F5F5F5')
            status_item.setBackground(QBrush(QColor(bg)))
            self.table.setItem(row, 6, status_item)

            self.table.setItem(row, 7, QTableWidgetItem(order.get('estimated_delivery', '')))

            # Highlight duplicate rows in amber and add tooltip
            if is_dup:
                existing = self._duplicate_map[row]
                dup_color = QColor('#FFF3E0')   # light amber
                dup_border = QColor('#FF9800')
                tooltip = (
                    f"⚠️ Già presente in DB (ID {existing['id']}):\n"
                    f"  Descrizione: {existing.get('description', '')}\n"
                    f"  Stato: {existing.get('status', '')}\n"
                    f"  ID Ordine: {existing.get('site_order_id', '')}\n"
                    f"  Tracking: {existing.get('tracking_number', '')}"
                )
                for col in range(1, 8):
                    item = self.table.item(row, col)
                    if item:
                        item.setBackground(QBrush(dup_color))
                        item.setToolTip(tooltip)
            else:
                # Tooltip on description only
                desc_item = self.table.item(row, 3)
                if desc_item:
                    desc_item.setToolTip(order.get('description', ''))

        self.table.resizeRowsToContents()

    def _select_all(self):
        for row in range(self.table.rowCount()):
            chk = self._get_checkbox(row)
            if chk:
                chk.setChecked(True)

    def _select_none(self):
        for row in range(self.table.rowCount()):
            chk = self._get_checkbox(row)
            if chk:
                chk.setChecked(False)

    def _get_checkbox(self, row: int):
        widget = self.table.cellWidget(row, 0)
        if widget:
            for child in widget.children():
                if isinstance(child, QCheckBox):
                    return child
        return None

    def _import_selected(self):
        selected_rows = []
        for row in range(self.table.rowCount()):
            chk = self._get_checkbox(row)
            if chk and chk.isChecked():
                selected_rows.append(row)

        if not selected_rows:
            QMessageBox.warning(self, "Selezione", "Seleziona almeno un articolo da importare.")
            return

        # Check if any selected rows are duplicates → ask confirmation
        selected_dups = [row for row in selected_rows if row in self._duplicate_map]
        if selected_dups:
            dup_lines = []
            for row in selected_dups:
                existing = self._duplicate_map[row]
                new_order = self._parsed_orders[row]
                dup_lines.append(
                    f"• {new_order.get('description', 'Articolo')}\n"
                    f"  → già in DB come ID {existing['id']} "
                    f"(stato: {existing.get('status', 'N/D')})"
                )
            confirm = QMessageBox.question(
                self,
                "⚠️ Articoli già presenti",
                f"I seguenti {len(selected_dups)} articolo/i risultano già presenti nel database:\n\n"
                + "\n".join(dup_lines)
                + "\n\nVuoi importarli comunque come nuovi ordini?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return

        imported = 0
        skipped = 0
        for row in selected_rows:
            if row < len(self._parsed_orders):
                order = self._parsed_orders[row]
                order_id = database.add_order(order)
                if order_id:
                    imported += 1
                    logger.info(f"HTML-IMPORT: Ordine importato con ID {order_id}: {order.get('description', '')}")
                else:
                    skipped += 1

        msg = f"✅ Importati {imported} ordine/i con successo!"
        if skipped:
            msg += f"\n⚠️ {skipped} ordine/i non importato/i (errore DB)."

        QMessageBox.information(self, "Importazione completata", msg)
        logger.info(f"HTML-IMPORT: Importazione completata. Importati: {imported}, Saltati: {skipped}")
        self.accept()
