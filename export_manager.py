"""
Export functionality for Delivery Tracker.
Supports CSV, JSON, and Excel formats with formatting.
"""
import csv
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import utils

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False
    utils.logger.warning("openpyxl not available, Excel export disabled")

logger = utils.get_logger(__name__)


class ExportManager:
    """Manager for exporting orders to various formats"""
    
    @staticmethod
    def export_to_excel(filepath: str, orders: List[Dict[str, Any]]) -> bool:
        """Export orders to Excel with formatting"""
        if not EXCEL_AVAILABLE:
            logger.error("Excel export not available: openpyxl not installed")
            return False
        
        try:
            wb = Workbook()
            ws = wb.active
            ws.title = "Ordini"
            
            # Define headers
            headers = [
                "ID", "Data Ordine", "Piattaforma", "Venditore", "Destinazione",
                "Descrizione", "Link", "Quantità", "Consegna Prevista",
                "Posizione", "Categoria", "Consegnato", "Note"
            ]
            
            # Header style
            header_font = Font(bold=True, color="FFFFFF", size=12)
            header_fill = PatternFill(start_color="2196F3", end_color="2196F3", fill_type="solid")
            header_alignment = Alignment(horizontal="center", vertical="center")
            
            # Write headers
            for col_num, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col_num)
                cell.value = header
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_alignment
            
            # Data style
            border = Border(
                left=Side(style='thin', color='E0E0E0'),
                right=Side(style='thin', color='E0E0E0'),
                top=Side(style='thin', color='E0E0E0'),
                bottom=Side(style='thin', color='E0E0E0')
            )
            
            # Write data
            for row_num, order in enumerate(orders, 2):
                # Determine row color based on status
                if order.get('is_delivered'):
                    fill = PatternFill(start_color="C8E6C9", end_color="C8E6C9", fill_type="solid")
                elif order.get('estimated_delivery'):
                    est_date = utils.DateHelper.parse_date(order['estimated_delivery'])
                    if est_date:
                        status = utils.DateHelper.get_date_status(est_date)
                        if status == 'overdue':
                            fill = PatternFill(start_color="FFCDD2", end_color="FFCDD2", fill_type="solid")
                        elif status == 'due_today':
                            fill = PatternFill(start_color="FFE082", end_color="FFE082", fill_type="solid")
                        elif status == 'upcoming':
                            fill = PatternFill(start_color="FFF9C4", end_color="FFF9C4", fill_type="solid")
                        else:
                            fill = None
                    else:
                        fill = None
                else:
                    fill = None
                
                # Write cells
                data = [
                    order.get('id', ''),
                    order.get('order_date', ''),
                    order.get('platform', ''),
                    order.get('seller', ''),
                    order.get('destination', ''),
                    order.get('description', ''),
                    order.get('link', ''),
                    order.get('quantity', 1),
                    order.get('estimated_delivery', ''),
                    order.get('position', ''),
                    order.get('category', ''),
                    "Sì" if order.get('is_delivered') else "No",
                    order.get('notes', '')
                ]
                
                for col_num, value in enumerate(data, 1):
                    cell = ws.cell(row=row_num, column=col_num)
                    cell.value = value
                    cell.border = border
                    if fill:
                        cell.fill = fill
                    
                    # Add hyperlink for link column
                    if col_num == 7 and value:  # Link column
                        cell.hyperlink = value
                        cell.font = Font(color="0000FF", underline="single")
            
            # Auto-adjust column widths
            for col_num, header in enumerate(headers, 1):
                column_letter = get_column_letter(col_num)
                
                # Calculate max width
                max_length = len(header)
                for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=col_num, max_col=col_num):
                    for cell in row:
                        try:
                            if cell.value:
                                max_length = max(max_length, len(str(cell.value)))
                        except:
                            pass
                
                adjusted_width = min(max_length + 2, 50)  # Cap at 50
                ws.column_dimensions[column_letter].width = adjusted_width
            
            # Freeze header row
            ws.freeze_panes = "A2"
            
            # Save workbook
            wb.save(filepath)
            logger.info(f"Exported {len(orders)} orders to Excel: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to Excel: {e}")
            return False
    
    @staticmethod
    def export_to_csv(filepath: str, orders: List[Dict[str, Any]]) -> bool:
        """Export orders to CSV file"""
        try:
            if not orders:
                return True
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'id', 'order_date', 'platform', 'seller', 'destination',
                    'description', 'link', 'quantity', 'estimated_delivery',
                    'position', 'category', 'is_delivered', 'notes'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(orders)
            
            logger.info(f"Exported {len(orders)} orders to CSV: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return False
    
    @staticmethod
    def export_to_json(filepath: str, orders: List[Dict[str, Any]]) -> bool:
        """Export orders to JSON file"""
        try:
            with open(filepath, 'w', encoding='utf-8') as jsonfile:
                json.dump(orders, jsonfile, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported {len(orders)} orders to JSON: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
            return False
    
    @staticmethod
    def import_from_json(filepath: str) -> tuple[bool, List[Dict[str, Any]]]:
        """Import orders from JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as jsonfile:
                orders = json.load(jsonfile)
            
            # Validate and clean data
            cleaned_orders = []
            for order in orders:
                # Remove id and timestamps to avoid conflicts
                order.pop('id', None)
                order.pop('created_at', None)
                order.pop('updated_at', None)
                cleaned_orders.append(order)
            
            logger.info(f"Loaded {len(cleaned_orders)} orders from JSON: {filepath}")
            return True, cleaned_orders
            
        except Exception as e:
            logger.error(f"Error importing from JSON: {e}")
            return False, []
    
    @staticmethod
    def import_from_csv(filepath: str) -> tuple[bool, List[Dict[str, Any]]]:
        """Import orders from CSV file"""
        try:
            orders = []
            
            with open(filepath, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row in reader:
                    # Remove id if present
                    row.pop('id', None)
                    row.pop('created_at', None)
                    row.pop('updated_at', None)
                    
                    # Convert boolean fields
                    if 'is_delivered' in row:
                        row['is_delivered'] = row['is_delivered'].lower() in ('true', '1', 'yes', 'sì')
                    if 'alarm_enabled' in row:
                        row['alarm_enabled'] = row['alarm_enabled'].lower() in ('true', '1', 'yes', 'sì')
                    
                    # Convert quantity to int
                    if 'quantity' in row:
                        try:
                            row['quantity'] = int(row['quantity'])
                        except:
                            row['quantity'] = 1
                    
                    orders.append(row)
            
            logger.info(f"Loaded {len(orders)} orders from CSV: {filepath}")
            return True, orders
            
        except Exception as e:
            logger.error(f"Error importing from CSV: {e}")
            return False, []
