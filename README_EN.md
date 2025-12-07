# Delivery Tracker v2.0.0

A modern and comprehensive Python desktop application to manage delivery deadlines from various online platforms.

## ✨ Main Features

### 📦 Complete Order Management
- **Detailed Tracking**: Monitor orders with complete information:
  - Order Date and Estimated Delivery
  - Platform (with predefined suggestions: Amazon, eBay, AliExpress, etc.)
  - Seller and Destination
  - Item Description
  - Clickable product link
  - Quantity
  - Physical Location (Warehouse, Home, Office, etc.)
  - Customizable Category
  - Notes for discrepancies or defects

### 🎨 Modern User Interface
- **Premium Design**: Modern interface with gradients and curated colors
- **Light/Dark Theme**: Support for both themes
- **Interactive Dashboard**: Statistics visualization with charts
  - Pie chart for platform distribution
  - Bar chart for delivery status
  - Real-time statistics cards
- **Collapsible Sidebar**: Optimize workspace
- **Advanced Search & Filters**:
  - Text search in description, seller, and notes
  - Platform filter
  - Category filter
  - Show/hide delivered orders

### 🔔 Visual Alarm System
- **Green**: Delivered material (entire row highlighted)
- **Red**: Delivery overdue
- **Orange**: Delivery due today
- **Yellow**: Delivery arriving soon (within 2 days)
- **Popup Notifications**: Alert on startup for overdue deliveries

### 📊 Export/Import Data
- **Multiple Export Formats**:
  - **Excel (.xlsx)**: With color formatting and styles
  - **CSV**: For universal compatibility
  - **JSON**: For complete backups
- **JSON Import**: Import orders from JSON files

### 💾 Automatic Backup
- Automatic database backup
- Automatic backup management (keeps last 10)
- Manual backup creation from settings
- Restore from backup

### ⚙️ Customizable Settings
- Theme selection (Light/Dark)
- Notification configuration
- Days in advance for alarms
- Automatic backup
- Show/hide delivered orders

### 🔍 Advanced Features
- **Context Menu**: Right-click for quick actions
- **Double Click**: Quick order editing
- **Input Validation**: Checks on URL, quantity, and required fields
- **Complete Logging**: Tracking of all operations
- **Optimized Performance**: Database indices for fast queries
- **Column Sorting**: Click on headers to sort
- **Tooltips**: Information on mouse hover

## 🛠️ Requirements

- Python 3.8+
- PyQt6
- PyQt6-Charts
- openpyxl (for Excel export)

## 📥 Installation

1. Clone or download the repository:
```bash
git clone https://github.com/losciuto/delivery-tracker.git
cd delivery-tracker
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## 🚀 Usage

Start the application with:
```bash
python main.py
```

### First Setup
1. On startup, the application will automatically create the database
2. Access Settings to configure theme and notifications
3. Start adding your orders!

### Navigation
- **Dashboard**: View statistics and general overview
- **Orders**: Manage the complete list of orders
- **Sidebar**: Quick access to all functions
- **File Menu**: Export/Import data
- **View Menu**: Quickly change view

### Order Management
- **Add**: Click "Add" in the sidebar or Ctrl+N
- **Edit**: Double-click on an order or select and click "Edit"
- **Delete**: Select and click "Delete" (with confirmation)
- **Mark Delivered**: Right-click → "Mark as Delivered"

### Search and Filters
- Use the search bar to find specific orders
- Filter by platform or category
- Hide delivered orders to focus on pending ones

## 📁 Project Structure

```
delivery-tracker/
├── main.py              # Entry point with styling
├── gui.py               # Main graphical interface
├── database.py          # SQLite database management
├── config.py            # Configurations and themes
├── utils.py             # Utility and helper functions
├── widgets.py           # Custom widgets (Dashboard, etc.)
├── export_manager.py    # Export/Import management
├── requirements.txt     # Python dependencies
├── run.sh              # Startup script
├── README.md           # Italian documentation
├── README_EN.md        # This file
├── LICENSE             # GPL-3.0 License
├── logs/               # Log files (auto-created)
├── backups/            # Database backups (auto-created)
└── delivery_tracker.db # SQLite database (auto-created)
```

## 🔧 Technologies Used

- **PyQt6**: Modern GUI framework
- **PyQt6-Charts**: Charts and visualizations
- **SQLite**: Lightweight and fast database
- **openpyxl**: Excel export with formatting
- **Python logging**: Robust logging system

## 📝 Technical Notes

### Database
- Uses SQLite with optimized indices
- Foreign keys enabled for referential integrity
- Automatic migration for new columns
- Support for categories and attachments (future)

### Performance
- Indices on frequently queried columns
- Optimized queries with filters
- Lazy data loading
- Intelligent caching

### Security
- Complete input validation
- Robust error handling
- Automatic backups
- Logging of all operations

## 🐛 Troubleshooting

### Application won't start
- Verify Python 3.8+ is installed
- Check all dependencies are installed: `pip install -r requirements.txt`
- Check logs in `logs/` for specific errors

### Excel export errors
- Make sure `openpyxl` is installed: `pip install openpyxl`

### Corrupted database
- Restore from a backup in `backups/`
- Or delete `delivery_tracker.db` to recreate it (you'll lose data)

## 🔄 Updates v2.0.0

### New Features
- ✅ Dashboard with statistics and charts
- ✅ Advanced search and filters
- ✅ Excel export with formatting
- ✅ Automatic backup system
- ✅ Category support
- ✅ Light/dark theme
- ✅ Customizable settings
- ✅ Context menu
- ✅ Improved input validation
- ✅ Complete logging

### Improvements
- ✅ Completely redesigned UI/UX
- ✅ Performance optimized with database indices
- ✅ Modular and maintainable code
- ✅ Robust error handling
- ✅ Complete documentation

## 👨‍💻 Author

**Massimo Lo Sciuto**
- Support: Antigravity
- Development: Gemini 3 Pro

## 📄 License

This project is released under the GPL-3.0 license. See the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## 📧 Support

For support or questions, open an issue on GitHub.

---

**Happy tracking of your deliveries! 📦✨**
