# Delivery Tracker

A Python desktop application to manage delivery deadlines from various online platforms.

## Features
- **Order Management**: Track orders with full details:
    - Order Date
    - Platform
    - Seller
    - Destination
    - Item Description
    - Link (clickable)
    - Quantity
    - Estimated Delivery
    - Position (where the material is currently located)
    - Notes (for discrepancies or defects)
- **Visual Alarms**:
    - **Green**: Delivered material (entire row highlighted).
    - **Red**: Delivery overdue.
    - **Orange**: Delivery due today.
    - **Yellow**: Delivery arriving soon (within 2 days).
- **Notifications**: Popup alert on startup for overdue deliveries.
- **User Interface**:
    - Italian Language (Default).
    - Sortable and Resizable Columns.
    - Modern Sidebar Layout.
    - Collapsible Menu (Coming Soon).
- **Status**: Mark orders as "Delivered".

## Requirements
- Python 3
- PyQt6

## Installation
1. Clone or download the repository.
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage
Run the application with:
```bash
python main.py
```

## Author
Massimo Lo Sciuto
Support: Antigravity
Development: Gemini 3 Pro
