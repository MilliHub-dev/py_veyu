import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get ZeptoMail API credentials
ZEPTOMAIL_API_KEY = os.getenv('ZEPTOMAIL_API_KEY')
ZEPTOMAIL_SENDER_EMAIL = os.getenv('ZEPTOMAIL_SENDER_EMAIL')
ZEPTOMAIL_SENDER_NAME = os.getenv('ZEPTOMAIL_SENDER_NAME')

# Print configuration for debugging
print("Testing ZeptoMail configuration...")
print(f"ZEPTOMAIL_API_KEY: {'Set' if ZEPTOMAIL_API_KEY else 'Not set'}")
print(f"ZEPTOMAIL_SENDER_EMAIL: {ZEPTOMAIL_SENDER_EMAIL or 'Not set'}")
print(f"ZEPTOMAIL_SENDER_NAME: {ZEPTOMAIL_SENDER_NAME or 'Not set'}")

# ZeptoMail API endpoint
url = "https://api.zeptomail.com/v1.1/email"

# Email data
payload = {
    "from": {
        "address": ZEPTOMAIL_SENDER_EMAIL,
        "name": ZEPTOMAIL_SENDER_NAME
    },
    "to": [{
        "email_address": {
            "address": "ekeminieffiong22@gmail.com"
        }
    }],
    "subject": "Test Email from Veyu (Direct API)",
    "htmlbody": "<h1>Test Email</h1><p>This is a test email sent directly via ZeptoMail API.</p>",
    "textbody": "This is a test email sent directly via ZeptoMail API.",
    "track_clicks": True,
    "track_opens": True
}

# Headers
headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "authorization": f"Zoho-enczapikey {ZEPTOMAIL_API_KEY.split(' ')[1]}"  # Extract just the API key part
}

# Send the request
try:
    print("\nSending test email via ZeptoMail API...")
    response = requests.post(url, json=payload, headers=headers)
    
    print(f"Status Code: {response.status_code}")
    print("Response:")
    print(json.dumps(response.json(), indent=2))
    
    if response.status_code == 200 or response.status_code == 202:
        print("\nEmail sent successfully!")
    else:
        print(f"\nFailed to send email. Status code: {response.status_code}")
        
except Exception as e:
    print(f"\nError sending email: {str(e)}")
    
    # Print detailed error information
    import traceback
    traceback.print_exc()

print("\nTest completed.")
