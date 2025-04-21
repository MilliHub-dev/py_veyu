import requests, os
from .payment_gateway import PaymentGateway
from paystackapi.paystack import Paystack
from decimal import Decimal
from decouple import config


class FlutterwaveAdapter(PaymentGateway):
    def initiate_deposit(self, amount:float, currency:str, customer_details:object, reference):
        
        # Set up headers and payload for the POST request
        headers = {
            'Authorization': f'Bearer {config("FLW_SECRET_KEY")}',
            'Content-Type': 'application/json'
        }
        payload = {
            'tx_ref': reference,
            'amount': amount,
            'currency': currency,
            'redirect_url': 'https://www./',
            # 'meta': {
            #     'consumer_id': 23,
            #     'consumer_mac': '92a3-912ba-1192a'
            # },
            'customer': {
                'email': customer_details.email,
                'phonenumber': customer_details.phone_number,
                'name': f'{customer_details.first_name} {customer_details.last_name}'
            },
            'customizations': {
                'title': 'Motaa Wallet Top up',
                'logo': 'wallet/gatway/assets/Motaa Logo.png'
            }
        }

        url = 'https://api.flutterwave.com/v3/payments'

        # Send the POST request
        try:
            response = requests.post(url, headers=headers, json=payload)
            response_data = response.json()
            print(response_data['data']['link'])

            if response_data['status'] == 'success':
            
                return response_data['data']['link']


        except requests.exceptions.RequestException as e:
            print(e)
            print(e.response.text if e.response else "No response text available.")

    def verify_deposit(self, transaction_id):
       
        headers = {
            'Authorization': f'Bearer {config("FLW_SECRET_KEY")}',
            'Content-Type': 'application/json'
        }

        try:
            response = requests.get(f'https://api.flutterwave.com/v3/transactions/{transaction_id}/verify', headers=headers)
            response_data = response.json()

            if response_data['status'] == 'success':
                return response_data

        except requests.exceptions.RequestException as e:
            print(e)
            print(e.response.text if e.response else "No response text available.")

    def resolve(self, account_details):

        url = 'https://api.flutterwave.com/v3/accounts/resolve'

        payload = {
        "account_number": account_details['number'],
        "account_bank": account_details['code']
        }

        headers = {
            'Authorization': f'Bearer {config("FLW_SECRET_KEY")}',
            'Content-Type': 'application/json'
        }
        try:
            response = requests.post(url, headers=headers, json=payload)
            response_data = response.json()

            print(response_data)
            if response_data['status'] == 'success':
                return response_data['data']['account_name']
            
        except requests.exceptions.RequestException as e:
            print(e)
            print(e.response.text if e.response else "No response text available.")

    def initiate_withdrawal(self, amount:float, account_details:object, narration,reference):
        
        payload = {
            "account_bank": account_details['bank_code'],
            "account_number": account_details['account_number'],
            "amount": amount,
            "narration": narration,
            "currency": "NGN",
            "reference": reference,
            "callback_url": "https://www.flutterwave.com/ng/",
            "debit_currency": "NGN"
        }

        headers = {
            'Authorization': f'Bearer {config("FLW_SECRET_KEY")}',
            'Content-Type': 'application/json'
        }

        url = 'https://api.flutterwave.com/v3/transfers'

        try:
            response = requests.post(url, headers=headers, json=payload)
            response_data = response.json()

            return response_data

        except requests.exceptions.RequestException as e:
            print(e)
            print(e.response.text if e.response else "No response text available.")

    def get_transfer_fees(self, amount):
        url = f"https://api.flutterwave.com/v3/transfers/fee?amount={amount}&currency=NGN"
        headers = {
            'Authorization': f'Bearer {config("FLW_SECRET_KEY")}',
            'Content-Type': 'application/json'
        }
        try:
            response = requests.get(url, headers=headers)
            response_data = response.json()

            if response_data['status'] == 'success':
                return response_data['data'][0]
            else: 
                return response_data['message']
            
        except requests.exceptions.RequestException as e:
            print(e)
            print(e.response.text if e.response else "No response text available.")

    def get_banks(self, country):
        url = f"https://api.flutterwave.com/v3/banks/{country}"  # Replace NG with the correct country code if needed

        headers = {
            'Authorization': f'Bearer {config("FLW_SECRET_KEY")}',
            'Content-Type': 'application/json'
        }

        try:
            response = requests.get(url, headers=headers)
            response_data = response.json()
            if response_data['status'] == 'success':
                return response_data['data']  # List of banks

        except requests.exceptions.RequestException as e:
            print(e)
            print(e.response.text if e.response else "No response text available.")

        return None


class PaystackAdapter(PaymentGateway):
    secret_key=os.environ['PAYSTACK_LIVE_SECRET_KEY']
    public_key=os.environ['PAYSTACK_LIVE_PUBLIC_KEY']

    client = Paystack(secret_key=secret_key)
    countries = [
        'nigeria',
        'ghana',
        'kenya',
        'south africa',
    ]

    def initiate_deposit(self, amount, currency, customer_details, notes):pass

    def get_banks(self, country="nigeria"):
        headers = {
            'Authorization': f"Bearer {secret_key}"
        }
        url = "https://api.paystack.co/bank"

        response = requests.get(url, headers=headers)
        data = response.json()
        if data['status'] == True:
            return data['data']
        else:
            return data


