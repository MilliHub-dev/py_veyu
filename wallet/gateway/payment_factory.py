from .payment_adapter import FlutterwaveAdapter, PaystackAdapter

def get_payment_gateway(gateway_name):
    if gateway_name.lower() == 'flutterwave':
        return FlutterwaveAdapter()
    elif gateway_name.lower() == 'paystack':
        return PaystackAdapter()

    else:
        raise ValueError('Unsupported payment gateway: {}'.format(gateway_name))