"""
Main entry point for Delivery Tracker application.
Initializes database, applies styling, and launches the GUI.
"""
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
import database
import config
import utils
from gui import MainWindow

logger = utils.get_logger(__name__)


def get_stylesheet(theme='light'):
    """Get application stylesheet based on theme"""
    
    # Load theme colors
    colors = config.LIGHT_THEME if theme == 'light' else config.DARK_THEME
    
    return f"""
        /* Global Styles */
        * {{
            font-family: 'Segoe UI', 'San Francisco', 'Helvetica Neue', Arial, sans-serif;
        }}
        
        QMainWindow {{
            background-color: {colors.bg_main};
        }}
        
        /* Sidebar Styles */
        QWidget#sidebar {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {colors.bg_sidebar}, stop:1 #1565C0);
            border-right: 2px solid {colors.border};
        }}
        
        QWidget#sidebar QPushButton {{
            background-color: rgba(255, 255, 255, 0.1);
            color: white;
            border: none;
            padding: 10px 15px;
            text-align: left;
            font-size: 14px;
            font-weight: 500;
            border-radius: 6px;
            margin: 2px 0;
        }}
        
        QWidget#sidebar QPushButton:hover {{
            background-color: rgba(255, 255, 255, 0.2);
        }}
        
        QWidget#sidebar QPushButton:pressed {{
            background-color: rgba(255, 255, 255, 0.3);
        }}
        
        QWidget#sidebar QLabel {{
            color: rgba(255, 255, 255, 0.7);
            font-weight: normal;
        }}
        
        /* Table Styles */
        QTableWidget {{
            background-color: {colors.bg_table};
            alternate-background-color: {colors.bg_table_alternate};
            selection-background-color: {colors.primary};
            selection-color: white;
            border: 1px solid {colors.border};
            border-radius: 8px;
            gridline-color: {colors.border_light};
        }}
        
        QHeaderView::section {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {colors.primary}, stop:1 {colors.primary_hover});
            color: white;
            padding: 8px;
            border: none;
            border-right: 1px solid rgba(255, 255, 255, 0.2);
            font-weight: bold;
            font-size: 13px;
        }}
        
        QHeaderView::section:hover {{
            background: {colors.primary_hover};
        }}
        
        QTableWidget::item {{
            padding: 8px;
            border-bottom: 1px solid {colors.border_light};
        }}
        
        QTableWidget::item:selected {{
            background-color: {colors.primary};
            color: white;
        }}
        
        /* Dialog Styles */
        QDialog {{
            background-color: {colors.bg_secondary};
        }}
        
        QDialog QPushButton {{
            background-color: {colors.primary};
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            font-weight: 500;
            min-width: 80px;
        }}
        
        QDialog QPushButton:hover {{
            background-color: {colors.primary_hover};
        }}
        
        QDialog QPushButton:pressed {{
            background-color: {colors.primary_pressed};
        }}
        
        /* Input Styles */
        QLineEdit, QDateEdit, QTextEdit, QComboBox {{
            padding: 8px;
            border: 2px solid {colors.border};
            border-radius: 6px;
            background-color: {colors.bg_secondary};
            color: {colors.text_primary};
            selection-background-color: {colors.primary};
        }}
        
        QLineEdit:focus, QDateEdit:focus, QTextEdit:focus, QComboBox:focus {{
            border: 2px solid {colors.primary};
        }}
        
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 25px;
            border-left: 1px solid {colors.border};
            background-color: {colors.bg_secondary};
        }}
        
        QComboBox::drop-down:hover {{
            background-color: {colors.border_light};
        }}
        
        QComboBox::down-arrow {{
            width: 0;
            height: 0;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid {colors.text_primary};
            margin-right: 5px;
        }}
        
        QComboBox::down-arrow:hover {{
            border-top-color: {colors.primary};
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {colors.bg_secondary};
            color: {colors.text_primary};
            border: 1px solid {colors.border};
            selection-background-color: {colors.primary};
            selection-color: white;
            padding: 4px;
        }}
        
        QComboBox QAbstractItemView::item {{
            padding: 6px;
            border-radius: 4px;
        }}
        
        QComboBox QAbstractItemView::item:hover {{
            background-color: {colors.primary};
            color: white;
        }}
        
        /* GroupBox Styles */
        QGroupBox {{
            font-weight: bold;
            font-size: 14px;
            border: 2px solid {colors.border};
            border-radius: 8px;
            margin-top: 12px;
            padding-top: 12px;
            background-color: {colors.bg_secondary};
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 4px 10px;
            color: {colors.primary};
        }}
        
        /* Label Styles */
        QLabel {{
            color: {colors.text_primary};
        }}
        
        QFormLayout QLabel {{
            font-weight: 500;
            color: {colors.text_secondary};
        }}
        
        /* CheckBox Styles */
        QCheckBox {{
            spacing: 8px;
            color: {colors.text_primary};
        }}
        
        QCheckBox::indicator {{
            width: 20px;
            height: 20px;
            border: 2px solid {colors.border};
            border-radius: 4px;
            background-color: {colors.bg_secondary};
        }}
        
        QCheckBox::indicator:checked {{
            background-color: {colors.primary};
            border-color: {colors.primary};
        }}
        
        /* ScrollBar Styles */
        QScrollBar:vertical {{
            border: none;
            background: {colors.bg_table_alternate};
            width: 12px;
            margin: 0;
        }}
        
        QScrollBar::handle:vertical {{
            background: {colors.border};
            border-radius: 6px;
            min-height: 30px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background: {colors.primary};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        /* MenuBar Styles */
        QMenuBar {{
            background-color: {colors.bg_secondary};
            color: {colors.text_primary};
            border-bottom: 1px solid {colors.border};
            padding: 4px;
        }}
        
        QMenuBar::item {{
            padding: 6px 12px;
            border-radius: 4px;
            color: {colors.text_primary};
        }}
        
        QMenuBar::item:selected {{
            background-color: {colors.primary};
            color: white;
        }}
        
        QMenuBar::item:pressed {{
            background-color: {colors.primary_pressed};
            color: white;
        }}
        
        QMenu {{
            background-color: {colors.bg_secondary};
            color: {colors.text_primary};
            border: 1px solid {colors.border};
            border-radius: 6px;
            padding: 4px;
        }}
        
        QMenu::item {{
            padding: 8px 24px;
            border-radius: 4px;
            color: {colors.text_primary};
        }}
        
        QMenu::item:selected {{
            background-color: {colors.primary};
            color: white;
        }}

        
        /* MessageBox Styles */
        QMessageBox {{
            background-color: {colors.bg_secondary};
            color: {colors.text_primary};
        }}
        
        QMessageBox QLabel {{
            color: {colors.text_primary};
        }}
        
        QMessageBox QPushButton {{
            min-width: 80px;
            padding: 8px 16px;
        }}
        
        /* Tooltip Styles */
        QToolTip {{
            background-color: {colors.text_primary};
            color: {colors.bg_secondary};
            border: 1px solid {colors.border};
            border-radius: 4px;
            padding: 6px;
        }}
    """


def main():
    """Main application entry point"""
    try:
        # Initialize Database
        logger.info("Initializing database...")
        database.init_db()
        
        # Create Application
        app = QApplication(sys.argv)
        app.setApplicationName(config.APP_NAME)
        app.setApplicationVersion(config.APP_VERSION)
        
        # Set default font
        font = QFont("Segoe UI", 10)
        app.setFont(font)
        
        # Load settings and apply theme
        settings = utils.Settings.load()
        theme = settings.get('theme', 'light')
        
        # Apply Stylesheet
        logger.info(f"Applying {theme} theme...")
        app.setStyleSheet(get_stylesheet(theme))
        
        # Create and Show Main Window
        logger.info("Creating main window...")
        window = MainWindow()
        window.show()
        
        logger.info("Application ready")
        
        # Run Event Loop
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

