from django.urls import path
from .views import (
    Balance,
    Deposit,
    Transfer,
    Withdrawal,
    WalletOverview,
    TransactionsView,
    TransactionAnalyticsView,
    UserTransactionSummaryView,
    GetBanks,
    ResolveAccountNumber,
    GetTransferFees,
)

urlpatterns = [
    path('', WalletOverview.as_view(), name='wallet-overview'),
    path('transfer/', Transfer.as_view(), name='wallet-transfer'),
    path('transactions/', TransactionsView.as_view(), name='wallet-transactions'),
    path('transactions/summary/', UserTransactionSummaryView.as_view(), name='transaction-summary'),
    path('analytics/', TransactionAnalyticsView.as_view(), name='transaction-analytics'),
    path('balance/', Balance.as_view(), name='wallet-balance'),
    path('deposit/', Deposit.as_view(), name='wallet-deposit'),
    path('withdraw/', Withdrawal.as_view(), name='wallet-withdraw'),
    path('banks/', GetBanks.as_view(), name='get-banks'),
    path('resolve-account/', ResolveAccountNumber.as_view(), name='resolve-account'),
    path('transfer-fees/', GetTransferFees.as_view(), name='transfer-fees'),
]