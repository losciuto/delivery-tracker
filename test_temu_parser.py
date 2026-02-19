
import sys
import logging
from html_order_parser import HtmlOrderParser

# Configura logging per vedere i warning del parser
logging.basicConfig(level=logging.INFO)

def test_parse():
    try:
        with open('temu_ordine.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        parser = HtmlOrderParser()
        result = parser.parse_with_meta(html_content)
        
        print(f"Platform: {result.get('platform')}")
        print(f"Page Type: {result.get('page_type')}")
        
        orders = result.get('orders', [])
        print(f"Found {len(orders)} items/orders in result list.")
        
        for i, order in enumerate(orders):
            print(f"\nResult {i+1}:")
            print(f"  Order ID: {order.get('order_id')}")
            print(f"  Description: {order.get('description')}")
            print(f"  Quantity: {order.get('quantity')}")
            print(f"  Status: {order.get('status')}")
            print(f"  Tracking: {order.get('tracking_number')}")
                
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_parse()

if __name__ == "__main__":
    test_parse()
