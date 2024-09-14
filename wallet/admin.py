from django.contrib import admin
from .models import Wallet, Transaction, MotaaWalletEmail

models = [MotaaWalletEmail, Wallet]

for model in models:
    admin.site.register(model)



@admin.register(Transaction)
class TransactionManager(admin.ModelAdmin):
    list_display = [
        "wallet",
        "type",
        "recipient",
        "amount",
        'status',
        "reference",
        "timestamp"
    ]

    list_filter = (
        "type",
        "amount",
        "timestamp",
        'status'
 
    )
    list_editable = (
     
    )
    search_fields = (
        "wallet__user__email",
        "type",
        "recipient",
        "amount",
        "reference",
        "timestamp",
        'status'
    )
