"""
Custom email backends for improved reliability and SSL handling.
"""
import ssl
import smtplib
import logging
from django.core.mail.backends.smtp import EmailBackend as DjangoSMTPBackend
from django.conf import settings

logger = logging.getLogger('utils.mail')


class ReliableSMTPBackend(DjangoSMTPBackend):
    """
    Enhanced SMTP backend with better SSL handling and connection management.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ssl_context = None
        self._setup_ssl_context()
    
    def _setup_ssl_context(self):
        """Setup SSL context with appropriate certificate verification settings."""
        try:
            self.ssl_context = ssl.create_default_context()
            
            # Provider-specific SSL configuration
            if hasattr(settings, 'EMAIL_HOST'):
                host = settings.EMAIL_HOST.lower()
                
                if 'sendgrid' in host:
                    logger.debug("Configuring SSL context for SendGrid compatibility")
                    self.ssl_context.check_hostname = False
                    self.ssl_context.verify_mode = ssl.CERT_NONE
                elif 'gmail' in host:
                    logger.debug("Configuring SSL context for Gmail compatibility")
                    self.ssl_context.check_hostname = True
                    self.ssl_context.verify_mode = ssl.CERT_REQUIRED
                    # Gmail requires proper SSL verification
                else:
                    logger.debug("Using default SSL context")
            
            # Allow configuration override
            if hasattr(settings, 'EMAIL_SSL_VERIFY'):
                if settings.EMAIL_SSL_VERIFY:
                    logger.debug("SSL certificate verification enabled via settings")
                    self.ssl_context.check_hostname = True
                    self.ssl_context.verify_mode = ssl.CERT_REQUIRED
                else:
                    logger.debug("SSL certificate verification disabled via settings")
                    self.ssl_context.check_hostname = False
                    self.ssl_context.verify_mode = ssl.CERT_NONE
                
        except Exception as e:
            logger.warning(f"Failed to setup SSL context: {e}")
            self.ssl_context = None
    
    def open(self):
        """
        Ensure an open connection to the email server with enhanced error handling.
        """
        if self.connection:
            # Connection exists, test if it's still alive
            try:
                status = self.connection.noop()[0]
                if status == 250:
                    return False  # Connection is alive
            except (smtplib.SMTPServerDisconnected, smtplib.SMTPException):
                # Connection is dead, close it
                self.close()
        
        connection_params = {
            'timeout': self.timeout,
        }
        
        # Add SSL context if available
        if self.ssl_context:
            connection_params['context'] = self.ssl_context
        
        try:
            if self.use_ssl:
                self.connection = smtplib.SMTP_SSL(
                    self.host, 
                    self.port, 
                    **connection_params
                )
            else:
                self.connection = smtplib.SMTP(
                    self.host, 
                    self.port, 
                    timeout=self.timeout
                )
                
                if self.use_tls:
                    self.connection.ehlo()
                    if self.ssl_context:
                        self.connection.starttls(context=self.ssl_context)
                    else:
                        self.connection.starttls()
                    self.connection.ehlo()
            
            if self.username and self.password:
                self.connection.login(self.username, self.password)
                
            logger.debug(f"SMTP connection established to {self.host}:{self.port}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            raise
        except smtplib.SMTPConnectError as e:
            logger.error(f"SMTP connection failed: {e}")
            raise
        except ssl.SSLError as e:
            logger.error(f"SSL error during SMTP connection: {e}")
            # Try without SSL verification as fallback
            if self.ssl_context and self.ssl_context.verify_mode != ssl.CERT_NONE:
                logger.warning("Retrying SMTP connection without SSL verification")
                self.ssl_context.check_hostname = False
                self.ssl_context.verify_mode = ssl.CERT_NONE
                return self.open()  # Recursive retry
            raise
        except Exception as e:
            logger.error(f"Unexpected error during SMTP connection: {e}")
            raise
    
    def close(self):
        """Close the connection to the email server with proper error handling."""
        if self.connection is None:
            return
        
        try:
            try:
                self.connection.quit()
            except (smtplib.SMTPServerDisconnected, smtplib.SMTPException):
                # Server already disconnected, just close the socket
                self.connection.close()
        except Exception as e:
            logger.debug(f"Error closing SMTP connection: {e}")
        finally:
            self.connection = None
    
    def send_messages(self, email_messages):
        """
        Send one or more EmailMessage objects with enhanced error handling.
        """
        if not email_messages:
            return 0
        
        new_conn_created = self.open()
        if not self.connection or self.connection is None:
            # Failed to create connection
            return 0
        
        num_sent = 0
        try:
            for message in email_messages:
                try:
                    sent = self._send_message(message)
                    if sent:
                        num_sent += 1
                except Exception as e:
                    logger.error(f"Failed to send individual message: {e}")
                    # Continue with other messages
                    continue
        finally:
            if new_conn_created:
                self.close()
        
        return num_sent
    
    def _send_message(self, message):
        """Send a single message with detailed error logging."""
        try:
            from_email = message.from_email
            recipients = message.recipients()
            message_str = message.message().as_bytes(linesep='\r\n')
            
            self.connection.sendmail(from_email, recipients, message_str)
            logger.debug(f"Message sent successfully to {recipients}")
            return True
            
        except smtplib.SMTPRecipientsRefused as e:
            logger.error(f"All recipients refused: {e}")
            return False
        except smtplib.SMTPSenderRefused as e:
            logger.error(f"Sender refused: {e}")
            return False
        except smtplib.SMTPDataError as e:
            logger.error(f"SMTP data error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending message: {e}")
            return False


class FallbackEmailBackend:
    """
    Email backend that tries multiple backends in sequence.
    """
    
    def __init__(self, *args, **kwargs):
        self.backends = []
        self._setup_backends()
    
    def _setup_backends(self):
        """Setup the list of backends to try."""
        # Primary backend (SMTP)
        primary_backend = getattr(settings, 'EMAIL_BACKEND', 'utils.email_backends.ReliableSMTPBackend')
        if primary_backend != 'utils.email_backends.FallbackEmailBackend':  # Avoid recursion
            try:
                from django.utils.module_loading import import_string
                backend_class = import_string(primary_backend)
                self.backends.append(('primary', backend_class))
            except Exception as e:
                logger.error(f"Failed to load primary email backend {primary_backend}: {e}")
        
        # Fallback backend
        fallback_backend = getattr(settings, 'EMAIL_FALLBACK_BACKEND', 'django.core.mail.backends.console.EmailBackend')
        if fallback_backend != primary_backend:
            try:
                from django.utils.module_loading import import_string
                backend_class = import_string(fallback_backend)
                self.backends.append(('fallback', backend_class))
            except Exception as e:
                logger.error(f"Failed to load fallback email backend {fallback_backend}: {e}")
    
    def send_messages(self, email_messages):
        """Try to send messages using available backends."""
        if not email_messages:
            return 0
        
        for backend_name, backend_class in self.backends:
            try:
                backend_instance = backend_class()
                num_sent = backend_instance.send_messages(email_messages)
                
                if num_sent > 0:
                    logger.info(f"Successfully sent {num_sent} messages using {backend_name} backend")
                    return num_sent
                else:
                    logger.warning(f"{backend_name} backend sent 0 messages")
                    
            except Exception as e:
                logger.error(f"Failed to send messages using {backend_name} backend: {e}")
                continue
        
        logger.error("All email backends failed")
        return 0
    
    def open(self):
        """Not implemented for fallback backend."""
        return True
    
    def close(self):
        """Not implemented for fallback backend."""
        pass