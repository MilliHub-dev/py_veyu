from django.core.mail import send_mass_mail, send_mail
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from pathlib import Path
from django.conf import settings


def send_email(subject, template, context, recipient):
    html_message = render_to_string(
        settings.BASE_DIR / template,
        context
    )

    email = EmailMessage(
        subject=subject,
        html_message=html_message,
        from_email='Motaa <motaa@gmail.com>',
        to=[recipient],
    )
    email.content_subtype = 'html'
    try:
        email.send(fail_silently=False)
    except Exception as e:
        print(f"Failed to send email: {e}")
    







