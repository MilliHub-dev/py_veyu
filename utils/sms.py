import africastalking
from africastalking.SMS import SMSService
from veyu import settings
# import vonage

username = 'Motaa' # 'sandbox'
# api_key = settings.SMS_API_KEY
# api_key = "atsk_42d1a7b512f793e7eb3382340f4c3565cdca0c0430a325d9599816dacc0c5fd76f0d7cdb" # sandbox
api_key="atsk_42e7f18bae53ab9f80e226feabe3a79351a6c1c8cf3af4fd0a823a93fb6643c02bf9e1a1"


# vonage_client = vonage.Client(key="e1c5efae", secret="wUdmQL7BK3K3hukn");
# # Vonage
# def send_sms(message, recipient:str, fail_silently=False):
#     recipient = f'+234{recipient}'
#     try:
#         sender = vonage.Sms(vonage_client)
#         response = sender.send_message({
#             'from': 'Motaa',
#             'text':message,
#             'to': recipient,
#         })

#         if response['messages'][0]['status'] == "0":
#             print("SMS sent Successfully")
#         else:
#             raise Exception(response['messages'][0]['error-text'])
#     except Exception as error:
#         if fail_silently:
#             return print(f'An error occurred when sending sms: {error}')
#         raise error



# Afirca's Talking
def send_sms(message, recipient:str, fail_silently=False):
    try:
        sender = SMSService(username=username, api_key=api_key)
        progress = sender.send(
            recipients=[recipient],
            message=message,
            # senderi='Motaa'
        )
        print("SENT", progress)
        return progress
    except Exception as error:
        if fail_silently:
            return print(f'An error occurred when sending sms: {error}')
        raise error


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




