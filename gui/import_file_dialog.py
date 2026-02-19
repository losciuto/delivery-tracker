"""
Import File Dialog for Delivery Tracker.
Supports importing orders from Excel (.xlsx/.xls), CSV and JSON files.
Shows a preview table with duplicate detection and per-row checkbox selection.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QMessageBox, QAbstractItemView, QCheckBox, QWidget, QSplitter,
    QGroupBox, QProgressBar, QLineEdit, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QColor, QBrush, QFont

import database
import utils
from export_manager import ExportManager

logger = utils.get_logger(__name__)

# Supported file filter string
FILE_FILTER = "File supportati (*.xlsx *.xls *.csv *.json);;Excel (*.xlsx *.xls);;CSV (*.csv);;JSON (*.json);;Tutti i file (*)"


class ImportWorker(QObject):
    """Worker for async file parsing to avoid UI freeze on large files."""
    finished = pyqtSignal(list)   # emits list of order dicts
    error = pyqtSignal(str)

    def __init__(self, filepath: str):
        super().__init__()
        self.filepath = filepath

    def run(self):
        try:
            ok, orders, err = ExportManager.import_auto(self.filepath)
            if not ok:
                self.error.emit(err or "Errore durante la lettura del file")
            else:
                self.finished.emit(orders)
        except Exception as e:
            logger.exception("Errore durante l'import del file")
            self.error.emit(str(e))


class ImportFileDialog(QDialog):
    """
    Dialog to select and preview orders from Excel/CSV/JSON before importing.
    Mirrors the UX of ImportHtmlDialog.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📂 Importa Ordini da File")
        self.resize(920, 680)
        self._parsed_orders = []
        self._duplicate_map = {}   # row_index -> existing DB order dict
        self._thread = None
        self._worker = None
        self._filepath = ""
        self.setup_ui()

    # ──────────────────────────────────────────────────────────────────────
    # UI Setup
    # ──────────────────────────────────────────────────────────────────────

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # ── Info bar ──────────────────────────────────────────────────────
        info_label = QLabel(
            "ℹ️  <b>Come si usa:</b> Seleziona un file <b>Excel (.xlsx/.xls)</b>, "
            "<b>CSV</b> o <b>JSON</b> contenente i tuoi ordini. "
            "Le colonne vengono rilevate automaticamente indipendentemente dall'ordine.<br>"
            "💡 <i>Colonne duplicate già presenti nel DB vengono evidenziate in arancione e pre-deselezionate.</i>"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(
            "background:#E3F2FD; border:1px solid #90CAF9; border-radius:6px; padding:8px;"
        )
        layout.addWidget(info_label)

        # ── File selector ─────────────────────────────────────────────────
        file_group = QGroupBox("📁 File da importare")
        file_layout = QHBoxLayout(file_group)
        file_layout.setContentsMargins(8, 8, 8, 8)

        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Nessun file selezionato...")
        self.file_path_edit.setReadOnly(True)
        self.file_path_edit.setStyleSheet("background: transparent;")
        file_layout.addWidget(self.file_path_edit)

        browse_btn = QPushButton("📂 Sfoglia…")
        browse_btn.setFixedWidth(110)
        browse_btn.setFixedHeight(34)
        browse_btn.clicked.connect(self._browse_file)
        file_layout.addWidget(browse_btn)

        layout.addWidget(file_group)

        # ── Preview table ─────────────────────────────────────────────────
        preview_group = QGroupBox("🔍 Anteprima articoli")
        preview_layout = QVBoxLayout(preview_group)

        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels([
            "✓", "Piattaforma", "ID Ordine", "Descrizione",
            "Q.tà", "Prezzo", "Stato", "Cons. Prevista", "Immagine"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 30)
        self.table.setColumnWidth(1, 110)
        self.table.setColumnWidth(2, 160)
        self.table.setColumnWidth(4, 55)
        self.table.setColumnWidth(5, 80)
        self.table.setColumnWidth(6, 120)
        self.table.setColumnWidth(7, 120)
        self.table.setColumnWidth(8, 160)
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

        layout.addWidget(preview_group)

        # ── Progress bar (hidden by default) ─────────────────────────────
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        layout.addWidget(self.progress)

        # ── Buttons ───────────────────────────────────────────────────────
        btn_layout = QHBoxLayout()

        self.import_btn = QPushButton("✅ Importa Selezionati")
        self.import_btn.setFixedHeight(40)
        self.import_btn.setEnabled(False)
        self.import_btn.clicked.connect(self._import_selected)

        cancel_btn = QPushButton("❌ Annulla")
        cancel_btn.setFixedHeight(40)
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(self.import_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    # ──────────────────────────────────────────────────────────────────────
    # Slots
    # ──────────────────────────────────────────────────────────────────────

    def _browse_file(self):
        """Open file browser dialog."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Seleziona file ordini", "", FILE_FILTER
        )
        if filepath:
            self._filepath = filepath
            self.file_path_edit.setText(filepath)
            self.import_btn.setEnabled(False)
            self.table.setRowCount(0)
            self.result_label.setText("")
            self._parsed_orders = []
            self._analyze()  # Auto-analyze once file is selected

    def _analyze(self):
        """Start async file parsing."""
        if not self._filepath:
            return

        self.import_btn.setEnabled(False)
        self.progress.show()
        self.table.setRowCount(0)
        self.result_label.setText("Analisi in corso…")

        self._thread = QThread()
        self._worker = ImportWorker(self._filepath)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_parse_done)
        self._worker.error.connect(self._on_parse_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._thread.start()

    def _on_parse_done(self, orders: list):
        self.progress.hide()
        self._parsed_orders = orders

        if not orders:
            self.result_label.setText("⚠️ Nessun ordine trovato nel file")
            QMessageBox.information(
                self, "Nessun risultato",
                "Non è stato possibile estrarre ordini dal file.\n\n"
                "Verifica che il file contenga intestazioni riconoscibili e dati validi."
            )
            return

        self._populate_table(orders)
        self.import_btn.setEnabled(True)

        dup_count = len(self._duplicate_map)
        base_msg = f"✅ {len(orders)} articolo/i trovato/i"
        if dup_count:
            self.result_label.setText(f"{base_msg}  ·  ⚠️ {dup_count} già presente/i in DB")
        else:
            self.result_label.setText(base_msg)

    def _on_parse_error(self, error_msg: str):
        self.progress.hide()
        self.result_label.setText("❌ Errore durante l'analisi")
        QMessageBox.critical(self, "Errore", f"Errore durante la lettura del file:\n{error_msg}")
        logger.error(f"FILE-IMPORT: Errore: {error_msg}")

    def _find_duplicates(self, orders: list) -> dict:
        """
        Check each parsed order against the DB.
        Matches on site_order_id/tracking AND description (Best Match).
        Returns {row_index: existing_order_dict}.
        """
        import re
        all_orders = database.get_orders(include_delivered=True)
        dup_map = {}

        def get_tokens(text):
            if not text: return set()
            # Lowercase, keep alphanumeric tokens only, ignore very short words
            words = re.findall(r'\w+', text.lower())
            return {w for w in words if len(w) > 1}

        def calculate_similarity(tokens1, tokens2):
            if not tokens1 or not tokens2: return 0.0
            intersection = tokens1.intersection(tokens2)
            # Use Jaccard-like or simple intersection ratio
            return len(intersection) / max(len(tokens1), len(tokens2))

        for row, order in enumerate(orders):
            new_site_id  = (order.get('site_order_id') or '').strip()
            new_tracking = (order.get('tracking_number') or '').strip()
            new_desc     = (order.get('description') or '').strip()
            new_tokens   = get_tokens(new_desc)
            
            # Phase 1: Filter possible candidates by ID or Tracking
            candidates = []
            for existing in all_orders:
                ex_site_id  = (existing.get('site_order_id') or '').strip()
                ex_tracking = (existing.get('tracking_number') or '').strip()
                
                match_id = new_site_id and ex_site_id and new_site_id == ex_site_id
                match_track = new_tracking and ex_tracking and new_tracking == ex_tracking
                
                if match_id or match_track:
                    candidates.append(existing)

            # Phase 2: If candidates exist, find the best match by description
            best_existing = None
            if candidates:
                max_sim = -1.0
                for cand in candidates:
                    cand_tokens = get_tokens(cand.get('description', ''))
                    sim = calculate_similarity(new_tokens, cand_tokens)
                    if sim > max_sim:
                        max_sim = sim
                        best_existing = cand
                
                # Minimum threshold for multi-item orders: 0.2 (at least some shared keywords)
                if max_sim < 0.2:
                    # If very low similarity, maybe it's a different item in same order but we don't have it yet
                    # However, if it matched ID/Tracking, it's safer to consider it a duplicate for merge
                    # unless we are sure it's NEW.
                    pass

            # Phase 3: Fallback - Search ALL orders by description if no ID match
            if not best_existing and new_tokens:
                max_sim = 0.0
                for ex in all_orders:
                    ex_tokens = get_tokens(ex.get('description', ''))
                    sim = calculate_similarity(new_tokens, ex_tokens)
                    if sim > max_sim:
                        max_sim = sim
                        best_existing = ex
                
                # Threshold for description-only match: 0.6 (fairly strict)
                if max_sim < 0.6:
                    best_existing = None

            if best_existing:
                dup_map[row] = best_existing

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

            # Checkbox
            chk_widget = QWidget()
            chk_layout = QHBoxLayout(chk_widget)
            chk_layout.setContentsMargins(4, 0, 4, 0)
            chk_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chk = QCheckBox()
            chk.setChecked(not is_dup)
            chk_layout.addWidget(chk)
            self.table.setCellWidget(row, 0, chk_widget)

            self.table.setItem(row, 1, QTableWidgetItem(str(order.get('platform', ''))))
            self.table.setItem(row, 2, QTableWidgetItem(str(order.get('site_order_id', ''))))
            self.table.setItem(row, 3, QTableWidgetItem(str(order.get('description', ''))))
            self.table.setItem(row, 4, QTableWidgetItem(str(order.get('quantity', 1))))

            # Price
            price = order.get('price')
            price_text = f"€ {price:.2f}" if price is not None else ''
            self.table.setItem(row, 5, QTableWidgetItem(price_text))

            # Status with color
            status = str(order.get('status', 'In Attesa'))
            status_item = QTableWidgetItem(status)
            bg = status_colors.get(status, '#F5F5F5')
            status_item.setBackground(QBrush(QColor(bg)))
            self.table.setItem(row, 6, status_item)

            self.table.setItem(row, 7, QTableWidgetItem(str(order.get('estimated_delivery', ''))))
            self.table.setItem(row, 8, QTableWidgetItem(str(order.get('image_url', ''))))

            # Highlight duplicates
            if is_dup:
                existing = self._duplicate_map[row]
                dup_color = QColor('#FFF3E0')
                tooltip = (
                    f"⚠️ Già presente in DB (ID {existing['id']}):\n"
                    f"  Descrizione: {existing.get('description', '')}\n"
                    f"  Stato: {existing.get('status', '')}\n"
                    f"  ID Ordine: {existing.get('site_order_id', '')}\n"
                    f"  Tracking: {existing.get('tracking_number', '')}"
                )
                for col in range(1, 9):
                    item = self.table.item(row, col)
                    if item:
                        item.setBackground(QBrush(dup_color))
                        item.setToolTip(tooltip)
            else:
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
        selected_rows = [
            row for row in range(self.table.rowCount())
            if (chk := self._get_checkbox(row)) and chk.isChecked()
        ]

        if not selected_rows:
            QMessageBox.warning(self, "Selezione", "Seleziona almeno un articolo da importare.")
            return

        # Identify selected duplicates
        selected_dups = [row for row in selected_rows if row in self._duplicate_map]
        
        # Choice for duplicates
        dup_action = "new" # default: import as new
        if selected_dups:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("⚠️ Articoli già presenti")
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setText(f"Sono stati selezionati {len(selected_dups)} articoli che risultano già presenti nel database.")
            msg_box.setInformativeText("Cosa vuoi fare con questi articoli?")
            
            # Custom buttons
            btn_merge = msg_box.addButton("Aggiorna Esistenti", QMessageBox.ButtonRole.AcceptRole)
            btn_merge.setToolTip("Riempie i campi vuoti dei record già presenti nel DB")
            
            btn_new = msg_box.addButton("Importa come Nuovi", QMessageBox.ButtonRole.AcceptRole)
            btn_new.setToolTip("Crea nuovi record separati (comportamento standard)")
            
            btn_skip = msg_box.addButton("Salta Duplicati", QMessageBox.ButtonRole.RejectRole)
            btn_skip.setToolTip("Importa solo gli articoli nuovi, saltando questi")
            
            msg_box.addButton(QMessageBox.StandardButton.Cancel)

            msg_box.exec()
            clicked_btn = msg_box.clickedButton()

            if clicked_btn == btn_merge:
                dup_action = "merge"
            elif clicked_btn == btn_new:
                dup_action = "new"
            elif clicked_btn == btn_skip:
                dup_action = "skip"
            else:
                return # Cancel

        imported = 0
        updated = 0
        skipped = 0
        
        for row in selected_rows:
            if row >= len(self._parsed_orders):
                continue

            order = self._parsed_orders[row].copy() # Work on a copy
            
            # Ensure mandatory fields have defaults
            if not order.get('order_date'):
                from datetime import date
                order['order_date'] = date.today().strftime('%Y-%m-%d')
            if not order.get('platform'):
                order['platform'] = 'Sconosciuto'
            if not order.get('description'):
                order['description'] = f"Articolo importato (riga {row + 1})"

            is_dup = row in self._duplicate_map
            
            if is_dup:
                if dup_action == "skip":
                    skipped += 1
                    continue
                elif dup_action == "merge":
                    existing_id = self._duplicate_map[row]['id']
                    if database.merge_order_data(existing_id, order):
                        updated += 1
                    else:
                        skipped += 1
                    continue
                # else: "new" -> falls through to add_order

            order_id = database.add_order(order)
            if order_id:
                imported += 1
                logger.info(f"FILE-IMPORT: Ordine importato ID {order_id}: {order.get('description', '')}")
            else:
                skipped += 1

        # Summary message
        msg_parts = []
        if imported:
            msg_parts.append(f"✅ Importati {imported} nuovi ordini.")
        if updated:
            msg_parts.append(f"🔄 Aggiornati {updated} ordini esistenti.")
        if skipped:
            msg_parts.append(f"⚠️ {skipped} articoli saltati o con errore.")
            
        if not msg_parts:
            msg_parts.append("Nessuna operazione effettuata.")

        QMessageBox.information(self, "Importazione completata", "\n".join(msg_parts))
        logger.info(f"FILE-IMPORT: Completato. New: {imported}, Merged: {updated}, Skipped: {skipped}")
        self.accept()
