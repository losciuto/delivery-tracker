# Delivery Tracker v2.6.0

A modern and comprehensive Python desktop application to manage delivery deadlines from various online platforms.

## 🔄 Updates v2.5.1
- ✅ **Maintenance Cleanup**: Removed obsolete HTML parsers, test scripts, and temporary documentation for a cleaner project structure.
- ✅ **Repository Optimization**: Streamlined project files and removed residue from older versions.

## 🔄 Updates v2.5.0
- ✅ **Extreme Performance**: Implemented O(1) in-memory lookup for duplicate detection. Analysis is now instantaneous even with thousands of orders.
- ✅ **Smart Date Parser**: New intelligent parser recognizes international formats, natural language (IT/EN), and varied separators.
- ✅ **Fuzzy Toolkit**: Centralized text comparison logic in `utils.py` for consistent "Best-Match" behavior.
- ✅ **UI Similarity Disclosure**: Import dialog now shows exact similarity percentages in tooltips.
 
 ## 🔄 Updates v2.6.0
 - ✅ **Optimized Global Search**: Search extended to all fields (Tracking, Site Order ID, Destination, Carrier, etc.).
 - ✅ **Persistence Imaging (BLOB)**: Product images are now downloaded and stored directly in the database.
 - ✅ **Thumbnail Tooltips**: Instant article preview (150x150) when hovering over any cell in the row.
 - ✅ **AliExpress Deep Scraping**: Automatic extraction of Vendor, Destination, Tracking Number, and Estimated Delivery.

## 🔄 Updates v2.4.0
Features

## ✨ Main Features

### 📦 Complete Order Management
- **Detailed Tracking**: Monitor orders with complete information:
  - Order Date and Estimated Delivery
  - Platform (with predefined suggestions: Amazon, eBay, AliExpress, etc.)
  - Seller and Destination
  - Item Description
  - Clickable product link
  - Quantity
  - **Site Order ID** (e.g., Amazon, eBay IDs)
  - **Dynamic Order Status** (Waiting, Shipped, In Transit, Delivered, etc.)
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
  - Global search across all fields (Tracking, Order ID, Destination, etc.)
  - Platform and Category filters
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
- **Local Image Storage**: Automatic download and saving of images in the DB (BLOB) for offline use.

### ⚙️ Customizable Settings
- Theme selection (Light/Dark)
- Notification configuration
- Days in advance for alarms
- **OAuth2 Email Integration** (Hotmail/Outlook)
- Automatic backup
- Show/hide delivered orders

### 📧 Pro Email Synchronization
- **Auto-Extraction**: Automatic tracking number, carrier and status detection.
- **Multi-language Support**: Recognizes English and Italian shipment terms.
- **Smart Matching**: Priority matching by tracking or Site Order ID.

### 🔍 Advanced Features
- **Context Menu**: Right-click for quick actions
- **Double Click**: Quick order editing
- **Input Validation**: Checks on URL, quantity, and required fields
- **Complete Logging**: Tracking of all operations
- **Optimized Performance**: Database indices for fast queries
- **Column Sorting**: Click on headers to sort
- **Global Search**: Find orders by Tracking Number, Site ID, or Destination instantly.
- **Image Previews**: Tooltips with thumbnails (150px) sourced from the local database when hovering over any cell.

## 🛍️ Supported Platforms

The application includes advanced parsers and optimized workflows for the following main platforms:
- ✅ **Amazon** (Automatic extraction and smart date parsing)
- ✅ **AliExpress** (Deep Scraping of tracking, vendor, and dates)
- ✅ **eBay** (Assisted import workflow)
- ✅ **Temu** (Assisted import workflow)

> [!IMPORTANT]
> Do you need support for another platform (e.g., Vinted, Shein, Zalando, etc.)? 
> **[Open an Issue on GitHub](https://github.com/losciuto/delivery-tracker/issues/new)** to make a specific request! We will develop new parsers based on community feedback.

## 📥 Quick Installation (Linux)

The easiest way to set everything up is using the automated setup script:

```bash
git clone https://github.com/losciuto/delivery-tracker.git
cd delivery-tracker
chmod +x setup.sh
./setup.sh
```

This script will configure the virtual environment, install dependencies, and verify system libraries.

---

## 🛠️ Requirements

- Python 3.8+
- PyQt6
- PyQt6-Charts
- openpyxl (for Excel export)

## 📥 Manual Installation

If you prefer to install manually:

1. Clone or download the repository:
```bash
git clone https://github.com/losciuto/delivery-tracker.git
cd delivery-tracker
```

2. Install dependencies (virtual environment recommended):
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
├── gui/                 # Graphical interface package
│   ├── __init__.py      # Exposes MainWindow
│   ├── main_window.py   # Main window logic
│   └── dialogs.py       # Dialogs (Order, Settings)
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

## 🔄 Updates v2.3.0
- ✅ **Universal Import**: Support for Excel, CSV, and JSON with instant preview and smart duplicate detection.
- ✅ **Product Insights**: New database fields for Price and Image Link, with clickable visual feedback in the main table.
- ✅ **AI Scraping Integration**: Optimized workflow for extracting Temu orders directly via browser.
- ✅ **UI Cleanup**: Removed obsolete HTML/URL import methods for a more streamlined and stable experience.

## 🔄 Updates v2.2.1
- ✅ **UI Optimization**: Improved layout for 19" monitors and sidebar reorganization.
- ✅ **Quick Actions**: Refresh button moved to a priority position.

## 🔄 Updates v2.2.0
- ✅ **Email Sync 2.0**:
    - Dynamic IMAP scan based on active database platforms.
    - Optimized support for **Too Good To Go**.
    - Improved Temu ID extraction (15-20 digits support).
    - Priority-based extraction (Order ID > Tracking) to prevent overlaps.
    - "Smart State" logic: subject priority and order confirmation recognition.
- ✅ **UI & UX**:
    - **Order Grouping**: Dynamic highlighting of articles with the same Order ID.
    - **Visual Indicator**: 🔗 icon for multiple-item orders.
    - **Smart Duplication**: Feature to copy existing orders for faster entry.
    - Default LIFO sorting and alphabetical ordering of platforms/categories.

## 🔄 Updates v2.1.1
- ✅ **Settings Fix**: Email field is now manually editable.

## 🔄 Updates v2.1.0
- ✅ **Site Order ID**: New field for professional site tracking.
- ✅ **Dynamic Status**: State management with conditional coloring.
- ✅ **Email Sync Pro**: 
    - Full IT/EN multi-language support.
    - Optimized IMAP search (by date) and stabilized folder scanning.
    - Advanced matching logic and detailed debug logging.

## 🔄 Updates v2.0.2
- ✅ **Fix**: Resolved missing dependency issue (PyQt6-Charts)
- ✅ **UI**: More intuitive and modern sidebar icons
- ✅ **Improvements**: General stability and code cleanup

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
