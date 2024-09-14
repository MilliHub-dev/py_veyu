from .payment_adapter import FlutterwaveAdapter

def get_payment_gateway(gateway_name):
    if gateway_name.lower() == 'flutterwave':
        return FlutterwaveAdapter()
    else:
        raise ValueError('Unsupported payment gateway: {}'.format(gateway_name))