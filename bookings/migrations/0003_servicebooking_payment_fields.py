from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0002_initial'),
        ('wallet', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='servicebooking',
            name='payment_method',
            field=models.CharField(default='paystack', max_length=20),
        ),
        migrations.AddField(
            model_name='servicebooking',
            name='payment_status',
            field=models.CharField(default='pending', max_length=20),
        ),
        migrations.AddField(
            model_name='servicebooking',
            name='amount_paid',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
        migrations.AddField(
            model_name='servicebooking',
            name='paid_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='servicebooking',
            name='payment_transaction',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='booking_payments', to='wallet.transaction'),
        ),
    ]

