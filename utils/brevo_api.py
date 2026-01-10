"""
Brevo API email backend - faster and more reliable than SMTP.
Uses HTTP API instead of SMTP to avoid network/firewall issues.
"""

import logging
import requests
from typing import List, Dict, Any, Optional
from django.conf import settings

logger = logging.getLogger(__name__)

# Brevo API configuration
BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"
# Get API key from environment (different from SMTP password)
import os
BREVO_API_KEY = os.getenv('BREVO_API_KEY', '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')


def send_email_via_brevo_api(
    subject: str,
    recipients: List[str],
    html_content: str = None,
    text_content: str = None,
    from_email: str = None,
    from_name: str = "Veyu"
) -> Dict[str, Any]:
    """
    Send email using Brevo's HTTP API (much faster than SMTP).
    
    Args:
        subject: Email subject
        recipients: List of recipient email addresses
        html_content: HTML email content
        text_content: Plain text email content
        from_email: Sender email address
        from_name: Sender name
    
    Returns:
        Dict with success status and message ID or error
    """
    try:
        from_email = from_email or getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@veyu.cc')
        
        # Prepare recipient list
        to_list = [{"email": email} for email in recipients]
        
        # Prepare email payload
        payload = {
            "sender": {
                "name": from_name,
                "email": from_email
            },
            "to": to_list,
            "subject": subject,
        }
        
        # Add content
        if html_content:
            payload["htmlContent"] = html_content
        if text_content:
            payload["textContent"] = text_content
        
        # Make API request
        headers = {
            "accept": "application/json",
            "api-key": BREVO_API_KEY,
            "content-type": "application/json"
        }
        
        response = requests.post(
            BREVO_API_URL,
            json=payload,
            headers=headers,
            timeout=10  # Much shorter timeout since it's HTTP
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            logger.info(f"✅ Email sent via Brevo API to {recipients}, Message ID: {result.get('messageId')}")
            return {
                'success': True,
                'message_id': result.get('messageId'),
                'recipients': recipients
            }
        else:
            error_msg = f"Brevo API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'status_code': response.status_code
            }
            
    except requests.Timeout:
        error_msg = "Brevo API request timed out"
        logger.error(error_msg)
        return {'success': False, 'error': error_msg}
    
    except Exception as e:
        error_msg = f"Brevo API error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {'success': False, 'error': error_msg}


def send_template_email_via_api(
    subject: str,
    recipients: List[str],
    template_name: str,
    context: Dict[str, Any] = None,
    from_email: str = None
) -> bool:
    """
    Send email using template via Brevo SMTP (API skipped to avoid IP restrictions).
    
    Args:
        subject: Email subject
        recipients: List of recipient email addresses
        template_name: Template file name
        context: Template context variables
        from_email: Sender email address
    
    Returns:
        bool: True if email was sent successfully
    """
    try:
        from django.template.loader import render_to_string
        from django.utils.html import strip_tags
        from utils.simple_mail import send_simple_email
        
        context = context or {}
        
        # Add default context
        context.setdefault('logo_url', 'https://dev.veyu.cc/static/veyu/logo.png')
        context.setdefault('app_name', 'Veyu')
        context.setdefault('support_email', settings.DEFAULT_FROM_EMAIL)
        context.setdefault('frontend_url', getattr(settings, 'FRONTEND_URL', 'https://veyu.cc'))
        
        # Try to render template
        template_paths = [template_name, f'emails/{template_name}']
        
        html_content = None
        for template_path in template_paths:
            try:
                html_content = render_to_string(template_path, context)
                logger.info(f"Successfully rendered template: {template_path}")
                break
            except Exception:
                continue
        
        # Fallback if template not found
        if not html_content:
            logger.warning(f"Template {template_name} not found, using plain text")
            text_content = f"Hello,\n\nThis is a notification from Veyu.\n\nBest regards,\nThe Veyu Team"
            html_content = f"<p>{text_content}</p>"
        
        # Create plain text version
        text_content = strip_tags(html_content)
        
        # DIRECT SMTP USAGE (Skipping API due to IP restrictions)
        logger.info("Using SMTP directly for email sending (API skipped)")
        return send_simple_email(
            subject=subject,
            recipients=recipients,
            message=text_content,
            html_message=html_content,
            from_email=from_email
        )
        
    except Exception as e:
        logger.error(f"Error sending template email: {e}", exc_info=True)
        return False
