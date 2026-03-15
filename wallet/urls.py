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
    SetPinView,
    ChangePinView,
    VerifyPinView,
)
from .views_withdrawal import (
    WithdrawalRequestListCreateView,
    WithdrawalRequestDetailView,
    cancel_withdrawal_request,
    withdrawal_statistics,
    verify_account_number,
)

urlpatterns = [
    path('', WalletOverview.as_view(), name='wallet-overview'),
    path('transfer/', Transfer.as_view(), name='wallet-transfer'),
    path('transactions/', TransactionsView.as_view(), name='wallet-transactions'),
    path('transactions/summary/', UserTransactionSummaryView.as_view(), name='transaction-summary'),
    path('analytics/', TransactionAnalyticsView.as_view(), name='transaction-analytics'),
    path('balance/', Balance.as_view(), name='wallet-balance'),
    
    # PIN Management
    path('pin/set/', SetPinView.as_view(), name='set-pin'),
    path('pin/change/', ChangePinView.as_view(), name='change-pin'),
    path('pin/verify/', VerifyPinView.as_view(), name='verify-pin'),
    
    path('deposit/', Deposit.as_view(), name='wallet-deposit'),
    path('withdraw/', Withdrawal.as_view(), name='wallet-withdraw'),
    path('banks/', GetBanks.as_view(), name='get-banks'),
    path('resolve-account/', ResolveAccountNumber.as_view(), name='resolve-account'),
    path('resolve-account', ResolveAccountNumber.as_view(), name='resolve-account-noslash'),
    path('transfer-fees/', GetTransferFees.as_view(), name='transfer-fees'),
    
    # Withdrawal requests for business accounts
    path('withdrawal-requests/', WithdrawalRequestListCreateView.as_view(), name='withdrawal-requests'),
    path('withdrawal-requests/<int:request_id>/', WithdrawalRequestDetailView.as_view(), name='withdrawal-request-detail'),
    path('withdrawal-requests/<int:request_id>/cancel/', cancel_withdrawal_request, name='cancel-withdrawal-request'),
    path('withdrawal-requests/statistics/', withdrawal_statistics, name='withdrawal-statistics'),
    path('withdrawal-requests/verify-account/', verify_account_number, name='verify-account-number'),
]
