from django.contrib import admin
from .models import Wallet, Transaction

models = [Wallet]

for model in models:
    admin.site.register(model)



@admin.register(Transaction)
class TransactionManager(admin.ModelAdmin):
    list_display = [
        "sender",
        "sender_wallet",
        "recipient",
        "type",
        "amount",
        'status',
        "date_created",
    ]

    list_filter = (
        "type",
        "amount",
        'status'
 
    )
    list_editable = (
     
    )
    search_fields = (
        "sender_wallet__user__email",
        "type",
        "recipient_wallet__user__email",
        "recipient_wallet__user__first_name",
        "amount",
        'status'
    )
