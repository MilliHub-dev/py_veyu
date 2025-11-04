from django.db import models
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.contrib.sites.models import Site
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class Newsletter(models.Model):
    """
    Model to store newsletter content and metadata
    """
    SUBJECT_MAX_LENGTH = 200
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('failed', 'Failed')
    ]
    
    AUDIENCE_CHOICES = [
        ('all', 'All Users'),
        ('customers', 'Customers Only'),
        ('mechanics', 'Mechanics Only'),
        ('dealers', 'Dealerships Only'),
        ('custom', 'Custom Recipients')
    ]
    
    title = models.CharField(max_length=200)
    subject = models.CharField(max_length=SUBJECT_MAX_LENGTH)
    content = models.TextField(help_text="HTML content of the newsletter")
    preview_text = models.CharField(
        max_length=200, 
        blank=True, 
        help_text="Short preview text shown in email clients"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='draft'
    )
    audience = models.CharField(
        max_length=20, 
        choices=AUDIENCE_CHOICES, 
        default='all'
    )
    custom_recipients = models.ManyToManyField(
        User, 
        blank=True, 
        related_name='newsletter_recipients',
        help_text="Select specific users to receive this newsletter"
    )
    scheduled_for = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Schedule for future sending (leave blank to send immediately)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    total_recipients = models.PositiveIntegerField(default=0)
    total_sent = models.PositiveIntegerField(default=0)
    total_failed = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Newsletter'
        verbose_name_plural = 'Newsletters'
    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
    
    def get_recipients(self):
        """Get the recipients based on the audience selection"""
        if self.audience == 'custom' and self.custom_recipients.exists():
            return self.custom_recipients.all()
            
        base_query = User.objects.filter(is_active=True, email_verified=True)
        
        if self.audience == 'customers':
            return base_query.filter(user_type='customer')
        elif self.audience == 'mechanics':
            return base_query.filter(user_type='mechanic')
        elif self.audience == 'dealers':
            return base_query.filter(user_type='dealer')
        else:  # all users
            return base_query
    
    def prepare_email(self, recipient):
        """Prepare the email message for a single recipient"""
        current_site = Site.objects.get_current()
        context = {
            'newsletter': self,
            'recipient': recipient,
            'site_name': current_site.name,
            'site_domain': current_site.domain,
            'unsubscribe_url': f"https://{current_site.domain}/unsubscribe/?email={recipient.email}",
            'current_year': timezone.now().year,
        }
        
        # Render HTML content
        html_content = render_to_string('emails/newsletter.html', context)
        text_content = strip_tags(html_content)
        
        # Create email
        email = EmailMultiAlternatives(
            subject=self.subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient.email],
            reply_to=[settings.DEFAULT_FROM_EMAIL],
        )
        email.attach_alternative(html_content, "text/html")
        
        return email
    
    def send_test(self, test_emails):
        """Send a test version of the newsletter to specified emails"""
        if not isinstance(test_emails, list):
            test_emails = [test_emails]
            
        success_count = 0
        for email in test_emails:
            try:
                # Create a test user for the recipient
                test_user = User(
                    email=email,
                    first_name="Test",
                    last_name="User"
                )
                
                # Prepare and send the test email
                email_msg = self.prepare_email(test_user)
                email_msg.send()
                success_count += 1
                
            except Exception as e:
                logger.error(f"Failed to send test email to {email}: {str(e)}")
                
        return success_count, len(test_emails) - success_count
    
    def send(self):
        """Send the newsletter to all recipients"""
        if self.status == 'sent':
            logger.warning(f"Newsletter {self.id} has already been sent")
            return False
            
        recipients = self.get_recipients()
        self.total_recipients = recipients.count()
        self.status = 'sending'
        self.save(update_fields=['status', 'total_recipients'])
        
        success_count = 0
        fail_count = 0
        
        for user in recipients:
            try:
                email_msg = self.prepare_email(user)
                email_msg.send()
                success_count += 1
                
                # Update progress periodically
                if success_count % 10 == 0:
                    self.total_sent = success_count
                    self.save(update_fields=['total_sent'])
                    
            except Exception as e:
                logger.error(f"Failed to send newsletter {self.id} to {user.email}: {str(e)}")
                fail_count += 1
        
        # Update final status
        self.status = 'sent' if success_count > 0 else 'failed'
        self.sent_at = timezone.now()
        self.total_sent = success_count
        self.total_failed = fail_count
        self.save(update_fields=['status', 'sent_at', 'total_sent', 'total_failed'])
        
        return success_count > 0
    
    def save(self, *args, **kwargs):
        # If this is a scheduled send and status is draft, update to scheduled
        if self.scheduled_for and self.status == 'draft' and not self.sent_at:
            self.status = 'scheduled'
        
        # If sending now, update status to sending
        if self.status == 'scheduled' and not self.scheduled_for and not self.sent_at:
            self.status = 'sending'
        
        super().save(*args, **kwargs)


class NewsletterAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'status', 'audience', 'created_at', 'sent_at')
    list_filter = ('status', 'audience', 'created_at')
    search_fields = ('title', 'subject', 'content')
    readonly_fields = ('status', 'total_recipients', 'total_sent', 'total_failed', 'sent_at')
    fieldsets = (
        ('Newsletter Details', {
            'fields': ('title', 'subject', 'preview_text', 'content')
        }),
        ('Audience', {
            'fields': ('audience', 'custom_recipients')
        }),
        ('Scheduling', {
            'fields': ('status', 'scheduled_for')
        }),
        ('Statistics', {
            'fields': ('total_recipients', 'total_sent', 'total_failed', 'sent_at'),
            'classes': ('collapse',)
        }),
    )
    actions = ['send_newsletter', 'send_test_newsletter']
    
    def send_newsletter(self, request, queryset):
        """Admin action to send selected newsletters"""
        sent_count = 0
        for newsletter in queryset:
            if newsletter.status not in ['sent', 'sending']:
                # In a real implementation, you'd want to use a task queue here
                newsletter.send()
                sent_count += 1
        
        if sent_count == 1:
            message = "1 newsletter was sent."
        else:
            message = f"{sent_count} newsletters were sent."
            
        self.message_user(request, message)
    
    send_newsletter.short_description = "Send selected newsletters"
    
    def send_test_newsletter(self, request, queryset):
        """Admin action to send a test version of the newsletter"""
        if request.method == 'POST':
            test_emails = request.POST.get('test_emails', '').split(',')
            test_emails = [email.strip() for email in test_emails if email.strip()]
            
            if not test_emails:
                self.message_user(request, "Please enter at least one test email address.", level='error')
                return
                
            for newsletter in queryset:
                success, failed = newsletter.send_test(test_emails)
                if success > 0:
                    self.message_user(
                        request, 
                        f"Test email sent to {success} out of {success + failed} addresses for '{newsletter.title}'",
                        level='success'
                    )
                if failed > 0:
                    self.message_user(
                        request, 
                        f"Failed to send test email to {failed} addresses for '{newsletter.title}'. Check logs for details.",
                        level='error'
                    )
            return
            
        # Show the test email form
        from django import forms
        from django.shortcuts import render
        
        class TestEmailForm(forms.Form):
            test_emails = forms.CharField(
                label='Test Email Addresses',
                help_text='Enter comma-separated email addresses',
                widget=forms.Textarea(attrs={'rows': 3, 'cols': 50})
            )
        
        context = {
            'newsletters': queryset,
            'form': TestEmailForm(),
            'opts': self.model._meta,
            'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
        }
        
        return render(
            request,
            'admin/accounts/newsletter/send_test_email.html',
            context
        )
    
    send_test_newsletter.short_description = "Send test email"

# Register the admin class
admin.site.register(Newsletter, NewsletterAdmin)
