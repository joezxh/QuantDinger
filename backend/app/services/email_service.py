"""
Email Service - Handles email verification codes and notifications.
"""
import os
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Tuple, Optional
from app.database.session import get_session
from app.database.repositories.verification_repository import VerificationRepository
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Singleton instance
_email_service = None


def get_email_service():
    """Get singleton EmailService instance"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service


class EmailService:
    """Email service for verification codes and notifications"""
    
    def __init__(self):
        self._load_config()
    
    def _load_config(self):
        """Load email configuration from environment variables"""
        self.smtp_host = os.getenv('SMTP_HOST', '')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.smtp_from = os.getenv('SMTP_FROM', '') or self.smtp_user
        self.smtp_use_tls = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
        self.smtp_use_ssl = os.getenv('SMTP_USE_SSL', 'false').lower() == 'true'
        
        # Verification code settings
        self.code_expire_minutes = int(os.getenv('VERIFICATION_CODE_EXPIRE_MINUTES', '10'))
        self.code_length = 6
        
        # Verification code attempt limits (anti-brute-force)
        self.code_max_attempts = int(os.getenv('VERIFICATION_CODE_MAX_ATTEMPTS', '5'))
        self.code_lock_minutes = int(os.getenv('VERIFICATION_CODE_LOCK_MINUTES', '30'))
        
        # Check if email is properly configured
        self.email_enabled = bool(self.smtp_host and self.smtp_user and self.smtp_password)
        
        if not self.email_enabled:
            logger.warning("Email service is not configured. SMTP settings are missing.")
    
    def is_configured(self) -> bool:
        """Check if email service is properly configured"""
        return self.email_enabled
    
    # =========================================================================
    # Verification Code Generation & Storage
    # =========================================================================
    
    def generate_code(self) -> str:
        """Generate a random numeric verification code"""
        return ''.join(random.choices(string.digits, k=self.code_length))
    
    def create_verification_code(self, email: str, code_type: str,
                                  ip_address: str = None) -> Tuple[bool, str]:
        """
        Create and store a new verification code.

        Args:
            email: Email address
            code_type: Type of verification (register, reset_password, change_password, change_email)
            ip_address: Requester's IP address

        Returns:
            (success, code_or_message)
        """
        try:
            code = self.generate_code()
            expires_at = datetime.now() + timedelta(minutes=self.code_expire_minutes)

            with get_session() as session:
                repo = VerificationRepository(session)
                repo.invalidate_old_codes(email, code_type)
                repo.create_code(
                    email=email,
                    code=code,
                    code_type=code_type,
                    expires_at=expires_at,
                    ip_address=ip_address,
                )

            return True, code

        except Exception as e:
            logger.error(f"Failed to create verification code: {e}")
            return False, 'Failed to generate verification code'
    
    def verify_code(self, email: str, code: str, code_type: str) -> Tuple[bool, str]:
        """
        Verify a submitted code with brute-force protection.

        Args:
            email: Email address
            code: The code to verify
            code_type: Type of verification

        Returns:
            (valid, message)
        """
        try:
            with get_session() as session:
                repo = VerificationRepository(session)

                # Check if locked due to too many failed attempts
                lock_window = datetime.now() - timedelta(minutes=self.code_lock_minutes)
                locked_count = repo.count_locked(
                    email, code_type, self.code_max_attempts, lock_window
                )
                if locked_count > 0:
                    return False, f'Too many failed attempts. Please try again in {self.code_lock_minutes} minutes'

                # Find latest unused code for this email/type
                record = repo.get_latest_unused(email, code_type)
                if not record:
                    return False, 'Invalid verification code'

                # Check if code matches
                if record.code != code:
                    new_attempts = repo.increment_attempts(record.id)
                    remaining = self.code_max_attempts - new_attempts
                    if remaining <= 0:
                        return False, f'Too many failed attempts. Please try again in {self.code_lock_minutes} minutes'
                    return False, f'Invalid verification code. {remaining} attempts remaining'

                # Check expiration
                expires_at = record.expires_at
                if isinstance(expires_at, str):
                    expires_at = datetime.fromisoformat(expires_at)
                if datetime.now() > expires_at:
                    return False, 'Verification code has expired'

                # Mark as used
                repo.mark_used(record.id)
                return True, 'verified'

        except Exception as e:
            logger.error(f"Failed to verify code: {e}")
            return False, 'Verification failed'
    
    # =========================================================================
    # Email Sending
    # =========================================================================
    
    def send_email(self, to_email: str, subject: str, html_body: str) -> Tuple[bool, str]:
        """
        Send an email.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML body content
        
        Returns:
            (success, message)
        """
        if not self.email_enabled:
            logger.warning(f"Email not sent (service disabled): {subject} to {to_email}")
            return False, 'Email service is not configured'
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_from
            msg['To'] = to_email
            
            # Plain text version (fallback)
            text_body = html_body.replace('<br>', '\n').replace('<br/>', '\n')
            # Simple HTML tag removal for plain text
            import re
            text_body = re.sub('<[^<]+?>', '', text_body)
            
            part1 = MIMEText(text_body, 'plain', 'utf-8')
            part2 = MIMEText(html_body, 'html', 'utf-8')
            
            msg.attach(part1)
            msg.attach(part2)
            
            # Connect and send
            if self.smtp_use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                if self.smtp_use_tls:
                    server.starttls()
            
            server.login(self.smtp_user, self.smtp_password)
            server.sendmail(self.smtp_from, to_email, msg.as_string())
            server.quit()
            
            logger.info(f"Email sent successfully: {subject} to {to_email}")
            return True, 'sent'
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            return False, 'Email authentication failed'
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return False, 'Failed to send email'
        except Exception as e:
            logger.error(f"Email error: {e}")
            return False, 'Failed to send email'
    
    def send_verification_code(self, email: str, code_type: str, 
                                ip_address: str = None) -> Tuple[bool, str]:
        """
        Generate and send a verification code email.
        
        Args:
            email: Recipient email address
            code_type: Type of verification (register, reset_password, change_password)
            ip_address: Requester's IP address
        
        Returns:
            (success, message)
        """
        # Generate code
        success, code_or_msg = self.create_verification_code(email, code_type, ip_address)
        if not success:
            return False, code_or_msg
        
        code = code_or_msg
        
        # Prepare email content based on type
        if code_type == 'register':
            subject = 'QuantDinger - Verification Code for Registration'
            action_text = 'complete your registration'
        elif code_type == 'login':
            subject = 'QuantDinger - Quick Login Verification Code'
            action_text = 'log in to your account'
        elif code_type == 'reset_password':
            subject = 'QuantDinger - Password Reset Verification Code'
            action_text = 'reset your password'
        elif code_type == 'change_password':
            subject = 'QuantDinger - Verification Code for Password Change'
            action_text = 'change your password'
        elif code_type == 'change_email':
            subject = 'QuantDinger - Verification Code for Email Change'
            action_text = 'change your email address'
        else:
            subject = 'QuantDinger - Verification Code'
            action_text = 'complete the verification'
        
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #1890ff; margin: 0;">QuantDinger</h1>
                <p style="color: #666; margin-top: 5px;">AI-Driven Quantitative Insights</p>
            </div>
            
            <div style="background: #f5f5f5; border-radius: 8px; padding: 30px; text-align: center;">
                <p style="color: #333; font-size: 16px; margin: 0 0 20px 0;">
                    Your verification code to {action_text} is:
                </p>
                <div style="background: #fff; border: 2px solid #1890ff; border-radius: 8px; padding: 20px; display: inline-block;">
                    <span style="font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #1890ff;">{code}</span>
                </div>
                <p style="color: #999; font-size: 14px; margin-top: 20px;">
                    This code will expire in {self.code_expire_minutes} minutes.
                </p>
            </div>
            
            <div style="margin-top: 30px; padding: 20px; background: #fff8e6; border-radius: 8px;">
                <p style="color: #d48806; font-size: 14px; margin: 0;">
                    <strong>Security Notice:</strong> If you did not request this code, 
                    please ignore this email. Do not share this code with anyone.
                </p>
            </div>
            
            <div style="text-align: center; margin-top: 30px; color: #999; font-size: 12px;">
                <p>&copy; QuantDinger. All rights reserved.</p>
            </div>
        </div>
        """
        
        # Send email
        return self.send_email(email, subject, html_body)
    
    # =========================================================================
    # Email Validation
    # =========================================================================
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Basic email format validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
