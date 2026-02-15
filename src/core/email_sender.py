"""
Email sender for license delivery.

Supports multiple backends:
- SMTP (Gmail, etc.)
- SendGrid (recommended)
- AWS SES
- Mailgun
"""
import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict
from dataclasses import asdict

logger = logging.getLogger(__name__)

# Email configuration from environment
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "smtp")  # smtp, sendgrid, ses

# SMTP settings
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER)

# SendGrid settings
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")

# AWS SES settings
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")


def send_license_email(license_info) -> bool:
    """
    Send license email to customer.
    
    Args:
        license_info: LicenseInfo object with key, tier, email
        
    Returns:
        True if sent successfully
    """
    backend = EMAIL_BACKEND.lower()
    
    try:
        if backend == "smtp":
            return _send_via_smtp(license_info)
        elif backend == "sendgrid":
            return _send_via_sendgrid(license_info)
        elif backend == "ses":
            return _send_via_ses(license_info)
        else:
            logger.error(f"Unknown email backend: {backend}")
            return False
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False


def _send_via_smtp(license_info) -> bool:
    """Send email via SMTP (Gmail, etc.)."""
    if not all([SMTP_USER, SMTP_PASSWORD]):
        raise ValueError("SMTP credentials not configured")
    
    tier_display = "Pro" if license_info.tier == "pro" else "Enterprise"
    
    # Create message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"Your SortMind {tier_display} License"
    msg['From'] = SMTP_FROM
    msg['To'] = license_info.email
    
    # Plain text version
    text_body = f"""
Thank you for purchasing SortMind {tier_display}!

Your license key:
{license_info.key}

To activate:
1. Open SortMind
2. Go to Help → License
3. Enter your key: {license_info.key}

Your license is valid for unlimited use on your devices.

Questions? Reply to this email.

— The Sortmind Team
"""
    
    # HTML version
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; text-align: center; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 10px; margin: 20px 0; }}
        .license-key {{ background: #fff; border: 2px dashed #667eea; padding: 20px; font-family: monospace; font-size: 24px; text-align: center; letter-spacing: 2px; margin: 20px 0; }}
        .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .footer {{ color: #666; font-size: 14px; margin-top: 30px; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 Thank You for Your Purchase!</h1>
            <p>SortMind {tier_display}</p>
        </div>
        
        <div class="content">
            <h2>Your License Key</h2>
            <div class="license-key">{license_info.key}</div>
            
            <h3>How to Activate</h3>
            <ol>
                <li>Open SortMind</li>
                <li>Go to <strong>Help → License</strong></li>
                <li>Enter your key above</li>
            </ol>
            
            <p style="text-align: center;">
                <a href="https://sortmind.app/docs/activation" class="button">View Activation Guide</a>
            </p>
        </div>
        
        <div class="footer">
            <p>Your license is valid for unlimited use on your devices.</p>
            <p>Questions? Reply to this email or contact support@sortmind.app</p>
            <p>— The Sortmind Team</p>
        </div>
    </div>
</body>
</html>
"""
    
    msg.attach(MIMEText(text_body, 'plain'))
    msg.attach(MIMEText(html_body, 'html'))
    
    # Send via SMTP
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM, license_info.email, msg.as_string())
    
    logger.info(f"License email sent to {license_info.email} via SMTP")
    return True


def _send_via_sendgrid(license_info) -> bool:
    """Send email via SendGrid."""
    if not SENDGRID_API_KEY:
        raise ValueError("SENDGRID_API_KEY not configured")
    
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
    except ImportError:
        raise ImportError("sendgrid package required. Install with: pip install sendgrid")
    
    tier_display = "Pro" if license_info.tier == "pro" else "Enterprise"
    
    message = Mail(
        from_email=SMTP_FROM,
        to_emails=license_info.email,
        subject=f"Your SortMind {tier_display} License",
        html_content=f"""
        <h1>Thank You for Your Purchase!</h1>
        <p>Your license key: <code>{license_info.key}</code></p>
        <p>To activate: Open SortMind → Help → License → Enter your key</p>
        """
    )
    
    sg = SendGridAPIClient(SENDGRID_API_KEY)
    response = sg.send(message)
    
    if response.status_code in [200, 202]:
        logger.info(f"License email sent to {license_info.email} via SendGrid")
        return True
    else:
        logger.error(f"SendGrid error: {response.status_code}")
        return False


def _send_via_ses(license_info) -> bool:
    """Send email via AWS SES."""
    if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY]):
        raise ValueError("AWS credentials not configured")
    
    try:
        import boto3
    except ImportError:
        raise ImportError("boto3 package required. Install with: pip install boto3")
    
    client = boto3.client(
        'ses',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )
    
    tier_display = "Pro" if license_info.tier == "pro" else "Enterprise"
    
    response = client.send_email(
        Source=SMTP_FROM,
        Destination={'ToAddresses': [license_info.email]},
        Message={
            'Subject': {'Data': f"Your SortMind {tier_display} License"},
            'Body': {
                'Html': {
                    'Data': f"""
                    <h1>Thank You!</h1>
                    <p>Your license key: {license_info.key}</p>
                    """
                }
            }
        }
    )
    
    logger.info(f"License email sent to {license_info.email} via SES")
    return True


def send_welcome_email(email: str) -> bool:
    """Send welcome email to new users (optional)."""
    if EMAIL_BACKEND == "smtp":
        msg = MIMEMultipart()
        msg['Subject'] = "Welcome to SortMind!"
        msg['From'] = SMTP_FROM
        msg['To'] = email
        
        body = """
Welcome to SortMind!

Thanks for downloading. Here are some quick tips:

1. Drag any folder to get started
2. Use AI suggestions for intelligent organization
3. Preview changes before applying them

Questions? Visit https://sortmind.app/help

Enjoy!
— The Sortmind Team
"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, email, msg.as_string())
        
        return True
    
    return False
