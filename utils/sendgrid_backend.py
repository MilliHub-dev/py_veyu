"""
SendGrid Web API email backend - works over HTTP instead of SMTP.
"""
import json
import logging
import requests
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import sanitize_address

logger = logging.getLogger('utils.mail')


class SendGridAPIBackend(BaseEmailBackend):
    """
    Email backend that uses SendGrid's Web API instead of SMTP.
    This works over HTTP and is less likely to be blocked than SMTP.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_key = getattr(settings, 'SENDGRID_API_KEY', '')
        self.api_url = 'https://api.sendgrid.com/v3/mail/send'
        
    def send_messages(self, email_messages):
        """Send messages using SendGrid Web API."""
        if not self.api_key:
            logger.error("SendGrid API key not configured")
            return 0
        
        if not email_messages:
            return 0
        
        sent_count = 0
        
        for message in email_messages:
            try:
                if self._send_message(message):
                    sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send message via SendGrid API: {e}")
                if not self.fail_silently:
                    raise
        
        return sent_count
    
    def _send_message(self, message):
        """Send a single message via SendGrid API."""
        try:
            # Prepare SendGrid API payload
            payload = self._build_sendgrid_payload(message)
            
            # Send request to SendGrid API
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=30
            )
            
            if response.status_code == 202:
                logger.info(f"Email sent successfully via SendGrid API to {message.to}")
                return True
            else:
                logger.error(f"SendGrid API error: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"SendGrid API request failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending via SendGrid API: {e}")
            return False
    
    def _build_sendgrid_payload(self, message):
        """Build SendGrid API payload from Django EmailMessage."""
        # Get sender email
        from_email = sanitize_address(message.from_email, message.encoding)
        from_name, from_addr = from_email
        
        # Prepare recipients
        to_list = []
        for recipient in message.to:
            to_name, to_addr = sanitize_address(recipient, message.encoding)
            to_list.append({
                'email': to_addr,
                'name': to_name if to_name != to_addr else ''
            })
        
        # Prepare content
        content = []
        
        # Plain text content
        if message.body:
            content.append({
                'type': 'text/plain',
                'value': message.body
            })
        
        # HTML content (from alternatives)
        for alternative_content, mimetype in getattr(message, 'alternatives', []):
            if mimetype == 'text/html':
                content.append({
                    'type': 'text/html',
                    'value': alternative_content
                })
        
        # If no content, add a default
        if not content:
            content.append({
                'type': 'text/plain',
                'value': 'This email was sent from Veyu.'
            })
        
        # Build payload
        payload = {
            'personalizations': [{
                'to': to_list,
                'subject': message.subject
            }],
            'from': {
                'email': from_addr,
                'name': from_name if from_name != from_addr else 'Veyu'
            },
            'content': content
        }
        
        # Add CC if present
        if message.cc:
            cc_list = []
            for cc_recipient in message.cc:
                cc_name, cc_addr = sanitize_address(cc_recipient, message.encoding)
                cc_list.append({
                    'email': cc_addr,
                    'name': cc_name if cc_name != cc_addr else ''
                })
            payload['personalizations'][0]['cc'] = cc_list
        
        # Add BCC if present
        if message.bcc:
            bcc_list = []
            for bcc_recipient in message.bcc:
                bcc_name, bcc_addr = sanitize_address(bcc_recipient, message.encoding)
                bcc_list.append({
                    'email': bcc_addr,
                    'name': bcc_name if bcc_name != bcc_addr else ''
                })
            payload['personalizations'][0]['bcc'] = bcc_list
        
        return payload


class HTTPEmailBackend(BaseEmailBackend):
    """
    Fallback HTTP-based email backend that tries multiple services.
    """
    
    def send_messages(self, email_messages):
        """Try SendGrid API first, then fall back to console."""
        if not email_messages:
            return 0
        
        # Try SendGrid API first
        try:
            sendgrid_backend = SendGridAPIBackend(fail_silently=True)
            sent_count = sendgrid_backend.send_messages(email_messages)
            
            if sent_count > 0:
                logger.info(f"Successfully sent {sent_count} emails via SendGrid API")
                return sent_count
        except Exception as e:
            logger.warning(f"SendGrid API failed: {e}")
        
        # Fall back to console backend
        logger.info("Falling back to console backend")
        from django.core.mail.backends.console import EmailBackend as ConsoleBackend
        console_backend = ConsoleBackend()
        return console_backend.send_messages(email_messages)