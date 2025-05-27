from django.core.mail import send_mass_mail, send_mail
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template.loader import render_to_string
from pathlib import Path
from django.conf import settings


def send_email(subject, recipients: list, message=None, template=None, context={}):
    content = message
    
    if template:
        html_message = render_to_string(
            settings.BASE_DIR / template,
            context
        )
        content = html_message

    email = EmailMessage(
        subject=subject,
        body=content,
        from_email='Motaa <motaa@gmail.com>',
        to=recipients,
    )
    email.content_subtype = 'html'
    try:
        email.send(fail_silently=False)
    except Exception as e:
        raise e
        print(f"Failed to send email: {e}")








