from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from .models import Wallet, Transaction
from accounts.models import Mechanic, Dealer, Customer
from decouple import config
from drf_yasg import openapi
from .serializers import *

from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import TokenAuthentication
from decimal import Decimal
from utils.dispatch import (
    on_wallet_deposit,
)
from .gateway.payment_factory import get_payment_gateway
from .gateway.payment_adapter import (
    FlutterwaveAdapter,
    PaystackAdapter
)
import uuid
from drf_yasg.utils import swagger_auto_schema

User = get_user_model()

class WalletOverview(APIView):
    permission_classes = [IsAuthenticated, ]
    allowed_methods = ["GET"]
    serializer_class = WalletSerializer

    @swagger_auto_schema(operation_summary="Endpoint to get user wallet")
    def get(self, request:Request):
        user = request.user
        user_wallet = get_object_or_404(Wallet, user= user)
        data = {
            'error': False,
            'data': WalletSerializer(user_wallet).data
        }
        return Response(data)


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
            'data': WalletBalanceSerializer(user_wallet).data
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



deposit_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=["reference"],
    properties={
        "reference": openapi.Schema(type=openapi.TYPE_STRING, description="flutterwave/paystack reference"),
    },
    responses={
        '200': {
            'transaction_id': str,
            'status': bool
        }
    }
)

class Deposit(APIView):  
    permission_classes = [IsAuthenticated]  
    # gateway = FlutterwaveAdapter()
    gateway = PaystackAdapter()
    allowed_methods = ["POST"]

    @swagger_auto_schema(
        operation_summary="Endpoint to deposit funds to wallet",
        # request_body=deposit_schema
    )
    def post(self, request:Request):
        data = request.data
        
        # raise Exception
        deposit_status = data.get('status')
        reference = data.get('tx_ref')
        transaction_id = data.get('reference')
        currency = data.get('currency')
        amount = data.get('amount')

        # confirm the deposit from flutterwave
        response = self.gateway.verify_transaction()
        print("Verifying transaction:", transaction_id)

        print("Response:", response)
        
        response = {'status': 'success'}        
        if response['status'] == 'success':
            user_wallet = get_object_or_404(Wallet, user=request.user)
            user_wallet.ledger_balance += Decimal(amount)
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
            on_wallet_deposit.send(request.user, wallet=user_wallet, amount=amount)

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

    def get(self, request:Request):
        country = request.GET.get('country', 'NG')
        gateway = FlutterwaveAdapter()
        response = gateway.get_banks(country=country)
        return Response({'error': False, 'data': response}, status=status.HTTP_200_OK)


class Withdrawal(APIView):

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



