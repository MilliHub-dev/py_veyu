from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from .models import Wallet, Transaction
from accounts.models import Mechanic, Dealer, Customer
from decouple import config

from .serializers import *

from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import TokenAuthentication
from decimal import Decimal

from .gateway.payment_factory import get_payment_gateway
from .gateway.payment_adapter import FlutterwaveAdapter
import uuid
from drf_yasg.utils import swagger_auto_schema

User = get_user_model()

class Transfer(APIView):

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(operation_summary="Endpoint for wallet to wallet transfer")
    def post(self, request):
        serializer = TransferSerializer(data=request.data)
        if serializer.is_valid():
            recipient_email = serializer.validated_data['recipient']
            amount = serializer.validated_data['amount']
            
            recipient = get_object_or_404(User, email=recipient_email)
            sender_wallet = get_object_or_404(Wallet, user=request.user)
            recipient_wallet = get_object_or_404(Wallet, user=recipient)

            if sender_wallet.balance < amount:
                return Response({'error': 'Insufficient funds'}, status=status.HTTP_403_FORBIDDEN)

            if sender_wallet.transfer(amount=amount, recipient_wallet=recipient_wallet):
                return Response(f'{amount} transferred to {recipient.email} successfully', status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Unable to perform this operation'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        

class Balance(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    allowed_methods = ["GET"]
    
    @swagger_auto_schema(operation_summary="Endpoint to get user balance")
    def get(self, request:Request):
        user = request.user
        user_wallet = get_object_or_404(Wallet, user= user)
        data = {
            'error': False,
            'data': WalletSerializer(user_wallet).data
        }
        return Response(data)



class TransactionsView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TransactionSerializer

    def get(self, request):
        wallet = Wallet.objects.get(user=request.user)
        transactions = wallet.transactions.all()
        data = {
            'error': False,
            'transactions': TransactionSerializer(transactions, many=True).data
        }
        return Response(data, 200)


class InitiateDeposit(APIView):
    @swagger_auto_schema(operation_summary="Endpoint to initiate wallet top up. It returns a payment link")
    def post(self, request:Request):

        serializer = InitiateDepositSerializer(data=request.data)
        if serializer.is_valid():

            amount_decimal = serializer._validated_data['amount']
            amount = str(amount_decimal)
            currency = serializer._validated_data['currency']
            customer_details = request.user
            gateway_name = serializer._validated_data['gateway_name']

            id = str(uuid.uuid4())
            parts = id.split('-')
            reference = 'motta-' + ''.join(parts[1:])

            try:
                gateway_to_use = get_payment_gateway(gateway_name)
                response = gateway_to_use.initiate_deposit(amount=amount, currency=currency, customer_details=customer_details, reference=reference)
            except ValueError as e:
                return Response({'error': str(e)}, status=400) 

            return Response(response)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CompleteWalletDepositFlutterwave(APIView):  
    permission_classes = [IsAuthenticated]  
    flutterwave = FlutterwaveAdapter()
    allowed_methods = ["POST"]

    @swagger_auto_schema(operation_summary="Endpoint called by flutterwave webhook to complete wallet top up")
    def post(self, request:Request):
        data = request.data
        
        deposit_status = data.get('status')
        reference = data.get('tx_ref')
        transaction_id = data.get('transaction_id')
        currency = data.get('currency')
        amount = data.get('amount')

        # confirm the deposit from flutterwave
        response = self.flutterwave.verify_deposit(transaction_id=transaction_id)
        print("Confirming Transaction", data['transaction_id'])
        
        if response['status'] == 'success':
            user_wallet = get_object_or_404(Wallet, user=request.user)
            transaction = Transaction(
                sender=request.user.name,
                recipient_wallet=user_wallet,
                type="deposit",
                narration=f'Deposit of {amount}',
                source='bank',
                amount=Decimal(amount),
                status='completed'
            )
            transaction.save()
            user_wallet.transactions.add(transaction,)
            user_wallet.save()

            # # send a notification
            # Notification.objects.create(
            # )

            data = {
                'error': False,
                'transaction': TransactionSerializer(transaction).data,
                'message': 'Deposit successfully received!'
            }
            return Response(data, status=status.HTTP_200_OK)
        else:
            return Response('Invalid hash', status=status.HTTP_400_BAD_REQUEST)


 
class ResolveAccountNumber(APIView):

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(operation_summary="Endpoint for resolving account number")
    def post(self, request:Request):
        seralizer = ResolveAccountNumberSerializer(data=request.data)

        if seralizer.is_valid():
            account_details = seralizer.validated_data
            gateway = FlutterwaveAdapter()
            response = gateway.resolve(account_details)

            return Response(response)
        else:
            return Response(seralizer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetBanks(APIView):
    permission_classes = [AllowAny]

    def post(self, request:Request):
        country = request.data.get('country')
        gateway = FlutterwaveAdapter()
        response = gateway.get_banks(country=country)
        return Response('ok', status=status.HTTP_200_OK)


class WithdrawalFlutterwave(APIView):

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(operation_summary="Endpoint for withdrawal to bank account from wallet")
    def post(self, request:Request):
        data = request.data
        user = request.user
        user_wallet = get_object_or_404(Wallet, user=user)
        serializer = WithdrawalSerializer(data=data)
        if serializer.is_valid():
            amount = serializer.validated_data['amount']
            account_number = serializer.validated_data['account_number']
            account_name = serializer.validated_data['account_name']
            bank_code = serializer.validated_data['bank_code']
            account_details = {'account_number': account_number, 'bank_code': bank_code, 'account_name': account_name}
            narration = 'Withdrawal from motta wallet'
            
            uid = str(uuid.uuid4())
            parts = uid.split('-')
            reference = 'motta-' + ''.join(parts[1:])

            if user_wallet.balance < amount:
                return Response({'error': 'Insufficient funds'}, status=status.HTTP_403_FORBIDDEN)
            
            withdrawal_gateway = FlutterwaveAdapter()
            response = withdrawal_gateway.initiate_withdrawal(amount=str(amount), account_details=account_details, narration=narration, reference=reference)
            transaction_status = response["status"]
            if transaction_status == 'success':
                user_wallet.withdraw(amount=amount, transaction_status=transaction_status, account_details=account_details, reference=reference)
                return Response(response, status=status.HTTP_200_OK)
            elif transaction_status == 'error':
                Transaction.objects.create(wallet=user_wallet, type=f'withdrwal', amount=amount, status=transaction_status, recipient= account_details,reference=reference)
                return Response(response, status=status.HTTP_200_OK)
        else: 
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

class GetTransferFees(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(operation_summary="Endpoint to get withdrawal fee")
    def post(self, request:Request):
        data = request.data
        serializer = GetTranferFeeSerializer(data=data)
        if serializer.is_valid():
            amount = serializer.validated_data['amount']

            gateway = FlutterwaveAdapter()
            response = gateway.get_transfer_fees(amount=amount)

            return Response(response, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



