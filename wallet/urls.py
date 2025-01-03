from django.urls import path
from .views import *


urlpatterns = [
    path('transfer/', Transfer.as_view()),
    path('balance/', Balance.as_view()),
    path('initiate_deposit/', InitiateDeposit.as_view()),
    path('complete-deposit-flutter/', CompleteWalletDepositFlutterwave.as_view()),

    # will do get banks and resolve from frontend
    path('resolve-account/', ResolveAccountNumber.as_view()),
    path('banks/', GetBanks.as_view()),
    path('withdrawal/', WithdrawalFlutterwave.as_view()),
    path('get-transfer-fee/', GetTransferFees.as_view()),


    # no transaction histor??
]