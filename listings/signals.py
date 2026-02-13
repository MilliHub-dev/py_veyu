from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Listing, ListingBoost
from accounts.models import Customer
from feedback.models import Notification
import threading
import logging

logger = logging.getLogger(__name__)

def _broadcast_worker(subject, message, cta_link=None, cta_text=None, level='info'):
    try:
        customers = Customer.objects.select_related('user').all()
        count = 0
        for customer in customers:
            # Create Notification with channel='push' to ensure it attempts to send push
            # It will also be visible in the in-app list
            n = Notification.objects.create(
                user=customer.user,
                subject=subject,
                message=message,
                level=level,
                channel='push', 
                cta_link=cta_link,
                cta_text=cta_text
            )
            n.send()
            count += 1
        logger.info(f"Broadcasted notification '{subject}' to {count} customers.")
    except Exception as e:
        logger.error(f"Error broadcasting notification: {e}")

def broadcast_notification(subject, message, cta_link=None, cta_text=None, level='info'):
    # Run in thread to avoid blocking response
    t = threading.Thread(
        target=_broadcast_worker, 
        args=(subject, message, cta_link, cta_text, level), 
        daemon=True
    )
    t.start()

# --- Listing Signals ---

@receiver(pre_save, sender=Listing)
def listing_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Listing.objects.get(pk=instance.pk)
            instance._old_verified = old_instance.verified
        except Listing.DoesNotExist:
            instance._old_verified = False
    else:
        instance._old_verified = False

@receiver(post_save, sender=Listing)
def listing_post_save(sender, instance, created, **kwargs):
    # Check if listing became verified (Published)
    was_verified = getattr(instance, '_old_verified', False)
    is_verified = instance.verified
    
    # Only notify if it's a RENTAL and it just became verified
    if instance.listing_type == 'rental' and is_verified and not was_verified:
        subject = "New Rental Available!"
        message = f"A new rental vehicle '{instance.title}' is now available. Check it out!"
        # Assuming frontend URL structure
        cta_link = f"/listings/{instance.id}" 
        cta_text = "View Rental"
        
        broadcast_notification(subject, message, cta_link, cta_text, level='success')

# --- ListingBoost Signals ---

@receiver(pre_save, sender=ListingBoost)
def boost_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = ListingBoost.objects.get(pk=instance.pk)
            instance._old_active = old_instance.active
        except ListingBoost.DoesNotExist:
            instance._old_active = False
    else:
        instance._old_active = False

@receiver(post_save, sender=ListingBoost)
def boost_post_save(sender, instance, created, **kwargs):
    # Check if boost became active
    was_active = getattr(instance, '_old_active', False)
    is_active = instance.active
    
    if is_active and not was_active:
        # Boost Activated -> Notify Users
        # Listing might be Sale or Rental, request said "new listings(only boosted listing)"
        listing = instance.listing
        subject = "Featured Listing!"
        message = f"Check out this featured vehicle: {listing.title}"
        cta_link = f"/listings/{listing.id}"
        cta_text = "View Listing"
        
        broadcast_notification(subject, message, cta_link, cta_text, level='info')
