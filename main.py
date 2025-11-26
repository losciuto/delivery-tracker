import sys
from PyQt6.QtWidgets import QApplication
import database
from gui import MainWindow

def main():
    # Initialize Database
    database.init_db()
    
    # Create Application
    app = QApplication(sys.argv)
    
    # Apply Stylesheet
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f0f0f0;
        }
        QWidget#sidebar {
            background-color: #e0e0e0;
            border-right: 1px solid #ccc;
        }
        QWidget#sidebar QPushButton {
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 8px 15px;
            text-align: left;
            font-size: 14px;
            border-radius: 4px;
        }
        QWidget#sidebar QPushButton:hover {
            background-color: #45a049;
        }
        QWidget#sidebar QPushButton:pressed {
            background-color: #3e8e41;
        }
        QTableWidget {
            background-color: white;
            alternate-background-color: #f9f9f9;
            selection-background-color: #a8d8ea;
            selection-color: black;
            border: none;
        }
        QHeaderView::section {
            background-color: #d0d0d0;
            padding: 6px;
            border: 1px solid #ccc;
            font-weight: bold;
        }
        /* Default button style for Dialogs */
        QDialog QPushButton {
            background-color: #2196F3;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
        }
        QDialog QPushButton:hover {
            background-color: #0b7dda;
        }
        QLineEdit, QDateEdit, QTextEdit {
            padding: 6px;
            border: 1px solid #ccc;
            border-radius: 4px;
        }
        QLabel {
            font-weight: bold;
            margin-top: 8px;
        }
    """)
    
    # Create and Show Main Window
    window = MainWindow()
    window.show()
    
    # Run Event Loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
