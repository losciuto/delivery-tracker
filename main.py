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
        app.setStyleSheet(utils.get_stylesheet(theme))
        
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
