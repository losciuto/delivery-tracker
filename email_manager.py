"""
Email manager module for Delivery Tracker.
Handles IMAP connection, searching, and parsing of delivery-related emails.
"""
import imaplib
import email
from email.header import decode_header
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
import utils
import database

logger = utils.get_logger(__name__)

# IMAP Settings for Hotmail/Outlook
IMAP_SERVER = "imap-mail.outlook.com"
IMAP_PORT = 993

class EmailSyncManager:
    """Manages email synchronization and parsing"""
    
    def __init__(self):
        self.settings = utils.Settings.load()
        self.email_addr = self.settings.get('email_address', '')
        self.email_pass = self.settings.get('email_password', '')
        self.enabled = self.settings.get('email_sync_enabled', False)

    def connect(self) -> Optional[imaplib.IMAP4_SSL]:
        """Connect and login to IMAP server"""
        if not self.email_addr or not self.email_pass:
            logger.warning("Email credentials not configured")
            return None
            
        try:
            logger.info(f"Connecting to {IMAP_SERVER}...")
            mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
            mail.login(self.email_addr, self.email_pass)
            return mail
        except Exception as e:
            logger.error(f"Email connection error: {e}")
            return None

    def fetch_updates(self) -> List[Dict[str, Any]]:
        """Fetch and parse recent delivery emails"""
        if not self.enabled:
            return []
            
        mail = self.connect()
        if not mail:
            return []
            
        updates = []
        try:
            mail.select("INBOX")
            # Search for unread emails or emails within last 7 days
            # For simplicity, we search for specific keywords in subject
            # Keywords: "spedito", "consegnato", "tracking", "delivery", "shipped"
            search_query = '(OR OR OR (SUBJECT "spedito") (SUBJECT "consegnato") (SUBJECT "tracking") (SUBJECT "delivery") (SUBJECT "shipped"))'
            
            status, messages = mail.search(None, search_query)
            if status != "OK":
                return []
                
            email_ids = messages[0].split()
            # Process last 20 matching emails
            for e_id in email_ids[-20:]:
                try:
                    res, msg_data = mail.fetch(e_id, "(RFC822)")
                    if res != "OK":
                        continue
                        
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    
                    # Get subject
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding if encoding else "utf-8")
                    
                    # Get body
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition"))
                            if content_type == "text/plain" and "attachment" not in content_disposition:
                                body = part.get_payload(decode=True).decode()
                                break
                    else:
                        body = msg.get_payload(decode=True).decode()

                    # Simple parsing logic
                    # 1. Identify tracking number
                    tracking_match = re.search(r'\b[A-Z0-9]{10,25}\b', body) # Generic tracking pattern
                    if tracking_match:
                        tracking_num = tracking_match.group(0)
                        
                        # Check if we have an order with this tracking or info
                        # For now, we try to match by description if mentioned in email
                        # or by extracting more info.
                        
                        updates.append({
                            'email_id': e_id.decode(),
                            'subject': subject,
                            'tracking': tracking_num,
                            'received_at': msg["Date"],
                            'body_snippet': body[:200]
                        })
                except Exception as ex:
                    logger.error(f"Error processing email ID {e_id}: {ex}")
                    
            mail.logout()
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            
        return updates

    def sync_with_db(self):
        """Match email updates with database orders"""
        updates = self.fetch_updates()
        applied_count = 0
        
        for update in updates:
            # Logic to find matching order
            # 1. Match by tracking number (if we had it in DB)
            # 2. Match by keywords in subject/body vs order description
            orders = database.get_orders(include_delivered=False)
            
            for order in orders:
                # If order description is in subject or body
                if order['description'].lower() in update['subject'].lower() or \
                   order['description'].lower() in update['body_snippet'].lower():
                    
                    # Update order status if not already updated by this email
                    if order.get('last_email_id') != update['email_id']:
                        # Determine new status/date from email
                        is_delivered = "consegnato" in update['subject'].lower() or "delivered" in update['subject'].lower()
                        
                        # Try to find a date in the body if it's a delivery notification
                        est_delivery = order['estimated_delivery']
                        date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', update['body_snippet'])
                        if date_match:
                            # Simplistic date update
                            est_delivery = "-".join(date_match.groups())

                        # Update DB
                        update_data = dict(order)
                        update_data['is_delivered'] = is_delivered
                        update_data['last_email_id'] = update['email_id']
                        update_data['last_sync_at'] = datetime.now().isoformat()
                        if not is_delivered and est_delivery != order['estimated_delivery']:
                            update_data['estimated_delivery'] = est_delivery
                        
                        # Add a note about the email
                        new_note = f"\n[Aggiornamento Email {datetime.now().strftime('%d/%m/%Y')}]: {update['subject']}"
                        update_data['notes'] = (update_data['notes'] or "") + new_note
                        
                        if database.update_order(order['id'], update_data):
                            applied_count += 1
                            logger.info(f"Updated order {order['id']} from email: {update['subject']}")
                            break # Move to next update
                            
        return applied_count
