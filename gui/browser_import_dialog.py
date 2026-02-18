"""
Browser Import Dialog for Delivery Tracker.
Uses QWebEngineView to navigate to a URL and capture order data.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView

import utils
import database

logger = utils.get_logger(__name__)

class BrowserImportDialog(QDialog):
    """Dialog with an integrated browser for capturing order data."""

    def __init__(self, parent=None, initial_url="https://www.temu.com"):
        super().__init__(parent)
        self.setWindowTitle("🌐 Importa da URL (Browser)")
        self.resize(1100, 800)
        
        # Configure the browser profile BEFORE setup_ui
        self._configure_profile()
        
        self.setup_ui()
        
        if initial_url:
            self.url_input.setText(initial_url)
            self.browser.setUrl(QUrl(initial_url))

    def _configure_profile(self):
        """Set a realistic User-Agent and enable persistence for cookies."""
        from PyQt6.QtWebEngineCore import QWebEngineProfile
        
        profile = QWebEngineProfile.defaultProfile()
        
        # Use a standard Chrome User-Agent to avoid 'overloaded' blocks
        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        )
        profile.setHttpUserAgent(user_agent)
        
        # Note: In a real app we might want a dedicated storage name
        # profile.setStorageName("DeliveryTrackerBrowser")
        # profile.setPersistentStoragePath("./browser_data")
        
        logger.info(f"Browser profile configured with User-Agent: {user_agent[:40]}...")

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # ── Toolbar ──────────────────────────────────────────────────────
        toolbar = QHBoxLayout()
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Inserisci l'URL della pagina ordine...")
        self.url_input.returnPressed.connect(self._load_url)
        toolbar.addWidget(self.url_input)

        go_btn = QPushButton("Vai")
        go_btn.setFixedWidth(60)
        go_btn.clicked.connect(self._load_url)
        toolbar.addWidget(go_btn)

        toolbar.addSpacing(10)

        self.capture_btn = QPushButton("🔍 Cattura Dati")
        self.capture_btn.setFixedHeight(32)
        self.capture_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.capture_btn.clicked.connect(self._capture_html)
        toolbar.addWidget(self.capture_btn)

        layout.addLayout(toolbar)

        # ── Browser ──────────────────────────────────────────────────────
        self.browser = QWebEngineView()
        self.browser.urlChanged.connect(lambda url: self.url_input.setText(url.toString()))
        self.browser.loadStarted.connect(lambda: self.progress.show())
        self.browser.loadFinished.connect(lambda: self.progress.hide())
        layout.addWidget(self.browser, 1) # Added stretch factor 1

        # ── Progress bar ─────────────────────────────────────────────────
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setFixedHeight(4)
        self.progress.setTextVisible(False)
        self.progress.hide()
        layout.addWidget(self.progress)

        # ── Instructions ─────────────────────────────────────────────────
        help_label = QLabel(
            "ℹ️ Naviga sulla pagina ordine e clicca <b>Cattura Dati</b>"
        )
        help_label.setStyleSheet("color: #888; font-size: 10px; margin-top: -5px;")
        layout.addWidget(help_label)

    def _load_url(self):
        url_text = self.url_input.text().strip()
        if not url_text.startswith(('http://', 'https://')):
            url_text = 'https://' + url_text
        self.browser.setUrl(QUrl(url_text))

    def _capture_html(self):
        """Extract HTML from the current page and pass it to the parser."""
        self.capture_btn.setEnabled(False)
        self.capture_btn.setText("Analisi...")
        
        # QWebEngineView.toHtml is asynchronous
        self.browser.page().toHtml(self._on_html_captured)

    def _on_html_captured(self, html):
        self.capture_btn.setEnabled(True)
        self.capture_btn.setText("🔍 Cattura Dati")
        
        if not html:
            QMessageBox.warning(self, "Errore", "Impossibile recuperare il sorgente della pagina.")
            return

        # Use the same logic as ImportHtmlDialog but with the captured HTML
        from gui.import_html_dialog import ImportHtmlDialog
        
        # We temporarily hide ourselves and show the preview dialog
        preview_dialog = ImportHtmlDialog(self)
        preview_dialog.html_input.setPlainText(html)
        preview_dialog._analyze() # Trigger analysis immediately
        
        if preview_dialog.exec():
            # If the user imported something, we are done
            self.accept()
        else:
            # If they cancelled, we stay here area
            pass

