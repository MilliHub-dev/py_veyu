# ZeptoMail Integration Guide

This guide explains how to set up and use ZeptoMail for sending emails in your Django application.

## Prerequisites

1. A ZeptoMail account (https://www.zoho.com/zeptomail/)
2. API key from your ZeptoMail account
3. Verified sender email address in ZeptoMail

## Configuration

### Environment Variables

Add the following environment variables to your `.env` file:

```bash
# ZeptoMail Configuration
ZEPTOMAIL_API_KEY=your_zeptomail_api_key
ZEPTOMAIL_SENDER_EMAIL=your_sender@yourdomain.com
ZEPTOMAIL_SENDER_NAME="Your Sender Name"
```

### Required Settings

Make sure your Django settings include:

```python
# In settings.py
EMAIL_BACKEND = 'utils.zeptomail.ZeptoMailBackend'
DEFAULT_FROM_EMAIL = 'Your Name <your_sender@yourdomain.com>'
SERVER_EMAIL = 'Your Name <your_sender@yourdomain.com>'
```

## Usage

### Sending Emails

You can use Django's standard email sending functions:

```python
from django.core.mail import send_mail

# Simple text email
send_mail(
    'Subject here',
    'Here is the message.',
    'from@example.com',
    ['to@example.com'],
    fail_silently=False,
)

# HTML email
from django.core.mail import EmailMultiAlternatives

subject, from_email, to = 'Hello', 'from@example.com', 'to@example.com'
text_content = 'This is an important message.'
html_content = '<p>This is an <strong>important</strong> message.</p>'
msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
msg.attach_alternative(html_content, "text/html")
msg.send()
```

### Using Templates

You can also use the provided utility function to send templated emails:

```python
from utils.zeptomail import send_templated_email

context = {
    'username': 'John Doe',
    'reset_link': 'https://example.com/reset/12345',
}

send_templated_email(
    template_name='password_reset',  # looks for emails/password_reset.html
    context=context,
    subject='Password Reset Request',
    recipient_list=['user@example.com'],
)
```

## Testing

In development, emails are saved to the `sent_emails` directory instead of being sent.

To test in production:
1. Set `DEBUG = False` in your settings
2. Ensure all required environment variables are set
3. Send a test email using the methods above
4. Check your ZeptoMail dashboard for delivery status

## Troubleshooting

- **Emails not sending**: Check the logs for any error messages
- **Authentication errors**: Verify your API key is correct and has the right permissions
- **Sender not verified**: Make sure your sender email is verified in the ZeptoMail dashboard
- **Rate limiting**: ZeptoMail has rate limits, check their documentation for details

## Security Considerations

- Never commit your API key to version control
- Use environment variables for sensitive information
- Regularly rotate your API keys
- Monitor your email sending activity in the ZeptoMail dashboard
