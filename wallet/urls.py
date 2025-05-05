from django.urls import path
from .views import (
    Balance,
    Deposit,
    Transfer,
    Withdrawal,
    WalletOverview,
    TransactionsView,
)

urlpatterns = [
    path('', WalletOverview.as_view()),
    path('transfer/', Transfer.as_view()),
    path('transactions/', TransactionsView.as_view()),
    path('balance/', Balance.as_view()),
    path('deposit/', Deposit.as_view()),
    path('withdraw/', Withdrawal.as_view()),
]