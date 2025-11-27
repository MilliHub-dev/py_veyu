import requests, os
from paystackapi.paystack import Paystack
from .payment_gateway import PaymentGateway
from decouple import config
from decimal import Decimal
from django.conf import settings


class WalletPaymentAdapter(PaymentGateway):
    # Do not move import to top 
    from wallet.models import Wallet, Transaction
    def w2w_transfer(self, amount, src_wallet:Wallet, dst_wallet:Wallet, **kwargs) -> tuple:
        """
            Example usage:
            wallet_provider = WalletPaymentAdapter()
            message, status = wallet_provider.w2w_transfer(25000) 
        """

        # check balance
        if amount <= (src_wallet.balance + self.get_transfer_fees(amount)):
            transfer_out = Transaction(
                recipient=dst_wallet.user.name,
                sender=src_wallet.user.name,
                sender_wallet=src_wallet,
                source='wallet',
                type='transfer_out',
                recipient_wallet=dst_wallet,
                tx_ref='',
                status='completed',
                amount=amount,
            )
            transfer_in = Transaction(
                recipient=dst_wallet.user.name,
                sender=src_wallet.user.name,
                sender_wallet=src_wallet,
                source='wallet',
                type='transfer_in',
                recipient_wallet=dst_wallet,
                tx_ref='',
                status='completed',
                amount=amount,
            )
            if kwargs.get('related_order', False):
                transfer_in.related_order = kwargs['related_order']
                transfer_out.related_order = kwargs['related_order']
                transfer_in.save()
                transfer_out.save()
                
            dst_wallet.apply_transaction(transfer_in)
            src_wallet.apply_transaction(transfer_out)

        else:
            return ("Error", False)

    def get_conv_rate(self, pair:tuple) -> tuple:
        """
            returns (buy, sell) rate between two currency pairs
            @arg: pair => ('USD', 'NGN')

            For example a user is paying for a car in Kenya, to be shipped from Nigeria,
            they will be charged an unfair amount without checking the conversion rate

            This will ensure that if @ 1 KYN to 15 NGN and the charge is NGN 3.2M 
            the amount charged from the kenyan is charged only KYN 213,333.333
        """
        response = requests.get('')
        data = response.json()
        
        
        return ()
    
    def get_wallet_currency(self):
        # return the wallet currency
        return

    def get_transfer_fees(self, amount):
        return 0 


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
                'title': 'Veyu Wallet Top up',
                'logo': 'wallet/gatway/assets/Veyu Logo.png'
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
    if settings.DEBUG:
        public_key=os.environ['PAYSTACK_TEST_PUBLIC_KEY']
        secret_key=os.environ['PAYSTACK_TEST_SECRET_KEY']

    client = Paystack(secret_key=secret_key)
    countries = [
        'nigeria',
        'ghana',
        'kenya',
        'south africa',
    ]

    def initiate_deposit(self, amount, currency, customer_details, notes):pass

    def verify_transaction(self, reference):
        try:
            verified_data = self.client.transaction.verify(reference)
            return verified_data
        except Exception as error:
            return {'status': 'error', 'message': str(error)}


    def get_banks(self, country="nigeria"):
        headers = {
            'Authorization': f"Bearer {self.secret_key}"
        }
        url = "https://api.paystack.co/bank"

        response = requests.get(url, headers=headers)
        data = response.json()
        if data['status'] == True:
            return data['data']
        else:
            return data
    
    def resolve_account(self, account_number, bank_code):
        """
        Verify bank account details with Paystack
        Returns account name if valid
        """
        headers = {
            'Authorization': f"Bearer {self.secret_key}",
            'Content-Type': 'application/json'
        }
        url = f"https://api.paystack.co/bank/resolve?account_number={account_number}&bank_code={bank_code}"
        
        try:
            response = requests.get(url, headers=headers)
            data = response.json()
            return data
        except Exception as error:
            return {'status': False, 'message': str(error)}


