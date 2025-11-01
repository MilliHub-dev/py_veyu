import os
import json
import logging
import requests
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)

class ZeptoMailClient:
    """
    A client for sending emails through ZeptoMail's API.
    """
    
    def __init__(self):
        self.api_key = os.getenv('ZEPTOMAIL_API_KEY')
        self.sender_email = os.getenv('ZEPTOMAIL_SENDER_EMAIL')
        self.sender_name = os.getenv('ZEPTOMAIL_SENDER_NAME', 'Veyu')
        self.api_url = "https://api.zeptomail.com/v1.1/email"
        
        if not self.api_key or not self.sender_email:
            logger.error("ZeptoMail API key or sender email not configured")
            raise ValueError("ZeptoMail API key and sender email must be configured")
    
    def send_email(self, to_email, subject, html_content, text_content=None, **kwargs):
        """
        Send an email using ZeptoMail API
        
        Args:
            to_email (str or list): Email address(es) to send to
            subject (str): Email subject
            html_content (str): HTML content of the email
            text_content (str, optional): Plain text version of the email. 
                                        If not provided, will be generated from HTML.
            **kwargs: Additional parameters like cc, bcc, reply_to, etc.
            
        Returns:
            dict: Response from ZeptoMail API
        """
        if not text_content:
            text_content = strip_tags(html_content)
            
        if isinstance(to_email, str):
            to_email = [{"email_address": {"address": to_email, "name": to_email.split('@')[0]}}]
        elif isinstance(to_email, list):
            to_email = [{"email_address": {"address": email, "name": email.split('@')[0]}} for email in to_email]
            
        payload = {
            "from": {
                "address": self.sender_email,
                "name": self.sender_name
            },
            "to": to_email,
            "subject": subject,
            "htmlbody": html_content,
            "textbody": text_content,
        }
        
        # Add optional fields if provided
        if 'cc' in kwargs:
            payload['cc'] = [{"email_address": {"address": email} for email in kwargs['cc']}]
        if 'bcc' in kwargs:
            payload['bcc'] = [{"email_address": {"address": email} for email in kwargs['bcc']}]
        if 'reply_to' in kwargs:
            payload['reply_to'] = [{"address": email} for email in kwargs['reply_to']]
        
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Zoho-enczapikey {self.api_key}"
        }
        
        try:
            response = requests.post(self.api_url, json={"messages": [payload]}, headers=headers)
            response.raise_for_status()
            logger.info(f"Email sent successfully to {[to['email_address']['address'] for to in to_email]}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send email: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise

def send_mail(subject, message, recipient_list, html_message=None, **kwargs):
    """
    A drop-in replacement for Django's send_mail that uses ZeptoMail
    """
    client = ZeptoMailClient()
    return client.send_email(
        to_email=recipient_list,
        subject=subject,
        html_content=html_message or message,
        text_content=message if not html_message else None,
        **kwargs
    )

def send_templated_email(template_name, context, subject, recipient_list, **kwargs):
    """
    Send an email using a Django template
    
    Args:
        template_name (str): Name of the template (without .html)
        context (dict): Context variables for the template
        subject (str): Email subject
        recipient_list (list): List of recipient email addresses
        **kwargs: Additional arguments to pass to send_mail
    """
    # Render HTML content
    html_content = render_to_string(f'emails/{template_name}.html', context)
    
    # Create a plain text version
    text_content = strip_tags(html_content)
    
    # Send the email
    return send_mail(
        subject=subject,
        message=text_content,
        recipient_list=recipient_list,
        html_message=html_content,
        **kwargs
    )


class ZeptoMailBackend(BaseEmailBackend):
    """
    A Django email backend that uses ZeptoMail's API to send emails.
    """
    
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.connection = None
        self.client = ZeptoMailClient()
    
    def open(self):
        """Open a persistent connection to the email server."""
        # No persistent connection needed for API calls
        return True
    
    def close(self):
        """Close any open connections to the email server."""
        # No persistent connection to close
        pass
    
    def send_messages(self, email_messages):
        """
        Send one or more EmailMessage objects and return the number of email 
        messages sent.
        """
        if not email_messages:
            return 0
        
        num_sent = 0
        for message in email_messages:
            sent = self._send_message(message)
            if sent:
                num_sent += 1
        
        return num_sent
    
    def _send_message(self, email_message):
        """Send a single message using ZeptoMail API."""
        if not email_message.recipients():
            return False
        
        try:
            # Prepare the email data
            to_emails = [{"email_address": {"address": email}} for email in email_message.to]
            
            # Handle CC and BCC
            cc_emails = [{"email_address": {"address": email}} for email in email_message.cc] if hasattr(email_message, 'cc') and email_message.cc else []
            bcc_emails = [{"email_address": {"address": email}} for email in email_message.bcc] if hasattr(email_message, 'bcc') and email_message.bcc else []
            
            # Handle reply-to
            reply_to = [{"address": email_message.reply_to[0]}] if hasattr(email_message, 'reply_to') and email_message.reply_to else []
            
            # Determine content type
            if hasattr(email_message, 'alternatives') and email_message.alternatives:
                # HTML email with plain text alternative
                html_content = None
                text_content = None
                for content, mimetype in email_message.alternatives:
                    if mimetype == 'text/html':
                        html_content = content
                    elif mimetype == 'text/plain':
                        text_content = content
                
                # If no HTML content was found in alternatives, use the message body
                if html_content is None:
                    html_content = email_message.body
                    text_content = strip_tags(html_content)
                elif text_content is None:
                    text_content = strip_tags(html_content)
            else:
                # Plain text email
                text_content = email_message.body
                html_content = None
            
            # Prepare the payload
            payload = {
                "from": {
                    "address": self.client.sender_email,
                    "name": self.client.sender_name
                },
                "to": to_emails,
                "subject": email_message.subject,
                "textbody": text_content,
            }
            
            if html_content:
                payload["htmlbody"] = html_content
            
            if cc_emails:
                payload["cc"] = cc_emails
            if bcc_emails:
                payload["bcc"] = bcc_emails
            if reply_to:
                payload["reply_to"] = reply_to
            
            # Send the email
            response = self.client.send_email(
                to_emails=email_message.to,
                subject=email_message.subject,
                html_content=html_content,
                text_content=text_content,
                cc=email_message.cc if hasattr(email_message, 'cc') else None,
                bcc=email_message.bcc if hasattr(email_message, 'bcc') else None,
                reply_to=email_message.reply_to if hasattr(email_message, 'reply_to') and email_message.reply_to else None
            )
            
            return True
            
        except Exception as e:
            if not self.fail_silently:
                raise
            logging.error(f"Failed to send email: {str(e)}")
            return False
