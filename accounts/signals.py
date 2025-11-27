"""
Signal handlers for accounts app.
Handles automatic profile updates when business verification status changes
and auto-creates user profiles based on user type.
"""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from utils.async_email import send_email_async

logger = logging.getLogger(__name__)


@receiver(post_save, sender='accounts.Account')
def create_user_profile(sender, instance, created, **kwargs):
    """
    Automatically create appropriate profile (Customer, Dealership, or Mechanic)
    when a new Account is created based on user_type.
    
    This prevents AttributeError when accessing profile relationships like
    request.user.customer_profile, request.user.dealership_profile, etc.
    
    Args:
        sender: The model class (Account)
        instance: The Account instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if not created:
        return
    
    try:
        from accounts.models import Customer, Dealership, Mechanic
        
        # Create profile based on user_type
        if instance.user_type == 'customer':
            Customer.objects.get_or_create(user=instance)
            logger.info(f"Created Customer profile for user {instance.email}")
            
        elif instance.user_type == 'dealer':
            Dealership.objects.get_or_create(user=instance)
            logger.info(f"Created Dealership profile for user {instance.email}")
            
        elif instance.user_type == 'mechanic':
            Mechanic.objects.get_or_create(user=instance)
            logger.info(f"Created Mechanic profile for user {instance.email}")
            
        # Admin and staff don't need profiles
        
    except Exception as e:
        logger.error(
            f"Failed to create profile for user {instance.email} "
            f"with user_type '{instance.user_type}': {str(e)}",
            exc_info=True
        )


@receiver(post_save, sender='accounts.BusinessVerificationSubmission')
def update_business_profile_on_verification(sender, instance, created, update_fields=None, **kwargs):
    """
    Automatically update Dealership or Mechanic profile when verification status changes.
    
    This signal handler:
    - Updates profile fields with verified business information on approval
    - Sets verified_business flag to True on approval, False on rejection
    - Handles errors gracefully with logging
    
    Note: Email notifications are handled by the model's _send_status_notification() method.
    
    Args:
        sender: The model class (BusinessVerificationSubmission)
        instance: The BusinessVerificationSubmission instance being saved
        created: Boolean indicating if this is a new instance
        update_fields: Set of fields being updated (if partial update)
        **kwargs: Additional keyword arguments
    """
    # Only process status changes to 'verified' or 'rejected'
    if instance.status not in ['verified', 'rejected']:
        return
    
    # Skip if this is a new instance (shouldn't happen for verified/rejected)
    if created:
        return
    
    # If update_fields is specified and doesn't include 'status', skip
    # This prevents unnecessary processing on unrelated updates
    if update_fields is not None and 'status' not in update_fields:
        return
    
    try:
        # Determine which profile to update
        if instance.business_type == 'dealership' and instance.dealership:
            update_dealership_profile(instance)
            profile = instance.dealership
        elif instance.business_type == 'mechanic' and instance.mechanic:
            update_mechanic_profile(instance)
            profile = instance.mechanic
        else:
            logger.warning(
                f"BusinessVerificationSubmission {instance.id} has no associated profile. "
                f"Business type: {instance.business_type}"
            )
            return
        
        logger.info(
            f"Successfully updated {instance.business_type} profile for "
            f"verification submission {instance.id} with status '{instance.status}'"
        )
        
        # Send email notification asynchronously after successful profile update
        try:
            send_verification_status_email_async(
                user=profile.user,
                status=instance.status,
                business_name=instance.business_name,
                rejection_reason=instance.rejection_reason or ''
            )
            logger.info(
                f"Email notification queued for user {profile.user.email} "
                f"regarding verification status '{instance.status}'"
            )
        except Exception as email_error:
            # Log email error but don't fail the entire operation
            logger.error(
                f"Failed to queue email notification for verification {instance.id}: {str(email_error)}",
                exc_info=True
            )
        
    except Exception as e:
        logger.error(
            f"Failed to update business profile for verification submission {instance.id}: {str(e)}",
            exc_info=True
        )
        # Don't raise exception - allow the verification status to save
        # Admin will be notified via logs


def update_dealership_profile(submission):
    """
    Update Dealership profile with verified business information.
    
    Args:
        submission: BusinessVerificationSubmission instance
    
    Raises:
        Exception: If profile update fails
    """
    dealership = submission.dealership
    
    if submission.status == 'verified':
        # Copy verification data to dealership profile
        dealership.business_name = submission.business_name
        dealership.cac_number = submission.cac_number
        dealership.tin_number = submission.tin_number
        dealership.contact_email = submission.business_email
        dealership.contact_phone = submission.business_phone
        dealership.verified_business = True
        
        logger.info(
            f"Updating dealership {dealership.id} with verified business data: "
            f"business_name={submission.business_name}, cac_number={submission.cac_number}"
        )
        
    elif submission.status == 'rejected':
        # Set verified_business to False on rejection
        dealership.verified_business = False
        
        logger.info(
            f"Setting verified_business=False for dealership {dealership.id} "
            f"due to verification rejection"
        )
    
    # Save the dealership profile
    dealership.save()
    
    logger.info(
        f"Dealership profile {dealership.id} updated successfully. "
        f"verified_business={dealership.verified_business}"
    )


def update_mechanic_profile(submission):
    """
    Update Mechanic profile with verified business information.
    
    Args:
        submission: BusinessVerificationSubmission instance
    
    Raises:
        Exception: If profile update fails
    """
    mechanic = submission.mechanic
    
    if submission.status == 'verified':
        # Copy verification data to mechanic profile
        mechanic.business_name = submission.business_name
        mechanic.contact_email = submission.business_email
        mechanic.contact_phone = submission.business_phone
        mechanic.verified_business = True
        
        logger.info(
            f"Updating mechanic {mechanic.id} with verified business data: "
            f"business_name={submission.business_name}"
        )
        
    elif submission.status == 'rejected':
        # Set verified_business to False on rejection
        mechanic.verified_business = False
        
        logger.info(
            f"Setting verified_business=False for mechanic {mechanic.id} "
            f"due to verification rejection"
        )
    
    # Save the mechanic profile
    mechanic.save()
    
    logger.info(
        f"Mechanic profile {mechanic.id} updated successfully. "
        f"verified_business={mechanic.verified_business}"
    )


def send_verification_status_email_async(user, status: str, business_name: str, rejection_reason: str = ''):
    """
    Send verification status email asynchronously to avoid blocking signal handler.
    
    Args:
        user: User account to notify
        status: Verification status ('verified' or 'rejected')
        business_name: Name of the business being verified
        rejection_reason: Reason for rejection (if applicable)
    """
    from accounts.utils.email_notifications import send_business_verification_status
    
    # Use async email sending to avoid blocking the signal handler
    send_email_async(
        send_business_verification_status,
        user=user,
        status=status,
        reason=rejection_reason,
        business_name=business_name
    )
