"""
Verification script for refactoring.
Tests database operations and GUI imports.
"""
import sys
import os
import logging
from datetime import date

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VERIFY")

def test_database():
    logger.info("Testing Database Refactoring...")
    try:
        import database
        
        # 1. Initialize DB
        database.init_db()
        logger.info("✅ Database initialized")
        
        # 2. Add Order
        order_data = {
            'order_date': date.today().isoformat(),
            'platform': 'TestPlatform',
            'description': 'Test Order',
            'estimated_delivery': date.today().isoformat()
        }
        order_id = database.add_order(order_data)
        if order_id:
            logger.info(f"✅ Order added with ID: {order_id}")
        else:
            logger.error("❌ Failed to add order")
            return False
            
        # 3. Get Order
        order = database.get_order_by_id(order_id)
        if order and order['description'] == 'Test Order':
            logger.info("✅ Order retrieved correctly")
        else:
            logger.error("❌ Failed to retrieve order")
            return False
            
        # 4. Update Order
        order['description'] = 'Updated Order'
        if database.update_order(order_id, order):
            logger.info("✅ Order updated correctly")
        else:
            logger.error("❌ Failed to update order")
            return False
            
        # 5. Export (Test CSV)
        if database.export_to_csv("test_export.csv", [order]):
            logger.info("✅ CSV Export successful")
            os.remove("test_export.csv")
        else:
            logger.error("❌ Failed to export CSV")
            
        # 6. Delete Order
        if database.delete_order(order_id):
            logger.info("✅ Order deleted correctly")
        else:
            logger.error("❌ Failed to delete order")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Database test failed: {e}")
        return False

def test_gui_imports():
    logger.info("Testing GUI Imports...")
    try:
        from gui import MainWindow
        logger.info("✅ Imported MainWindow from gui")
        
        from gui.dialogs import OrderDialog, SettingsDialog
        logger.info("✅ Imported dialogs from gui.dialogs")
        
        return True
    except ImportError as e:
        logger.error(f"❌ GUI Import failed: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ GUI Test unexpected error: {e}")
        return False

if __name__ == "__main__":
    db_success = test_database()
    gui_success = test_gui_imports()
    
    if db_success and gui_success:
        logger.info("\n🎉 ALL CHECKS PASSED!")
        sys.exit(0)
    else:
        logger.error("\n⚠️ SOME CHECKS FAILED!")
        sys.exit(1)
