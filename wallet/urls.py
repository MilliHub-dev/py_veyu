from django.urls import path
from .views import (
    Transfer,
    TransactionsView,
    Balance,
    InitiateDeposit,
    CompleteWalletDepositFlutterwave,
    ResolveAccountNumber,
    WithdrawalFlutterwave,
    GetBanks,
    GetTransferFees,
)

urlpatterns = [
    path('transfer/', Transfer.as_view()),
    path('transactions/', TransactionsView.as_view()),
    path('balance/', Balance.as_view()),
    path('deposit/', CompleteWalletDepositFlutterwave.as_view()),
    path('withdraw/', WithdrawalFlutterwave.as_view()),

    # will do get banks and resolve from frontend
    path('resolve-account/', ResolveAccountNumber.as_view()),
    path('banks/', GetBanks.as_view()),
    path('get-transfer-fee/', GetTransferFees.as_view()),
]