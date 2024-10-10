import africastalking, vonage
from africastalking.SMS import SMSService
from django.conf import settings

username = 'Motaa'
api_key = settings.SMS_API_KEY
vonage_client = vonage.Client(key="e1c5efae", secret="wUdmQL7BK3K3hukn")


# Vonage
def send_sms(message, recipient:str, fail_silently=False):
    recipient = f'+234{recipient}'
    try:
        sender = vonage.Sms(vonage_client)
        response = sender.send_message({
            'from': 'Motaa',
            'text':message,
            'to': recipient,
        })

        if response['messages'][0]['status'] == "0":
            print("SMS sent Successfully")
        else:
            raise Exception(response['messages'][0]['error-text'])
    except Exception as error:
        if fail_silently:
            return print(f'An error occurred when sending sms: {error}')
        raise error



# Afirca's Talking
# def send_sms(message, recipient:str, fail_silently=False):
#     try:
#         sender = SMSService(username, api_key)
#         sender.send(
#             recipients=[recipient],
#             message=message,
#             sender_id='Motaa'
#         )
#     except Exception as error:
#         if fail_silently:
#             return print(f'An error occurred when sending sms: {error}')
#         raise error


def send_bulk_sms(message, recipients:list, fail_silently=False):
    try:
        sender = africastalking.SMS.SMSService(username, api_key)
        sender.send(
            recipients=recipients,
            message=message,
        )
    except Exception as error:
        if fail_silently:
            return print(f'An error occurred when sending sms: {error}')
        raise error


def verify_phone_number(phone, fail_silently=False):
    try:
        sender = africastalking.SMS.validate_phone(phone)
        if sender is not None:
            return True
        return False
    except Exception as error:
        if fail_silently:
            return print(f'An error occurred when sending sms: {error}')
        raise error




