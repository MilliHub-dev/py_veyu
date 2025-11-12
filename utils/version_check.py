"""
Version check endpoint to verify which code is deployed.
"""

import os
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def version_check(request):
    """
    Check which version of the code is running and email configuration.
    """
    brevo_api_key = os.getenv('BREVO_API_KEY', '')
    
    return JsonResponse({
        'version': 'v2.0-brevo-api',
        'commit': 'c711f1d',
        'email_system': 'Brevo API with SMTP fallback',
        'brevo_api_key_set': bool(brevo_api_key),
        'brevo_api_key_prefix': brevo_api_key[:15] + '...' if brevo_api_key else 'NOT SET',
        'async_email': 'enabled',
        'status': 'ready'
    })
