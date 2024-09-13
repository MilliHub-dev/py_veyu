from django.core.mail import send_mass_mail, send_mail
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from pathlib import Path
from django.conf import settings


def send_email(subject, template, context, recipients):
    html_message = render_to_string(
        settings.BASE_DIR / template,
        context
    )
    email = EmailMessage(
        subject,
        html_message,
        'Motaa <motaa@gmail.com>',
        recipients
    )
    email.content_subtype = 'html'
    email.send(fail_silently=False)







