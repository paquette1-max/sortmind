#!/usr/bin/env python3
"""
Setup script for Stripe payment integration.

This script helps configure the Stripe integration for File Organizer.
Run this after installing requirements-payments.txt

Usage:
    python setup_payments.py
"""
import os
import sys
from pathlib import Path

def check_dependencies():
    """Check if required packages are installed."""
    missing = []
    
    try:
        import stripe
    except ImportError:
        missing.append("stripe")
    
    try:
        import flask
    except ImportError:
        missing.append("flask")
    
    if missing:
        print("❌ Missing dependencies:")
        for pkg in missing:
            print(f"  - {pkg}")
        print(f"\nInstall with: pip install -r requirements-payments.txt")
        return False
    
    return True

def setup_env_file():
    """Create .env file from template."""
    env_file = Path(".env")
    example_file = Path(".env.example")
    
    if env_file.exists():
        print(f"⚠️  .env file already exists. Skipping creation.")
        return
    
    if not example_file.exists():
        print(f"❌ .env.example not found!")
        return
    
    print("📝 Creating .env file from template...")
    
    # Copy template
    with open(example_file, 'r') as f:
        content = f.read()
    
    with open(env_file, 'w') as f:
        f.write(content)
    
    print(f"✅ Created {env_file}")
    print("   Edit this file and add your Stripe API keys.")

def get_stripe_keys():
    """Interactive prompt for Stripe configuration."""
    print("\n" + "="*60)
    print("Stripe Configuration")
    print("="*60)
    
    print("\n🚀 Getting your Stripe API keys:")
    print("1. Go to https://dashboard.stripe.com/apikeys")
    print("2. Copy your Secret key (starts with sk_live_ or sk_test_)")
    print("3. Copy your Publishable key (starts with pk_live_ or pk_test_)")
    
    print("\n⚠️  Use TEST keys for development, LIVE keys for production")
    
    secret_key = input("\nStripe Secret Key: ").strip()
    publishable_key = input("Stripe Publishable Key: ").strip()
    
    # Detect test mode
    is_test = "test" in secret_key
    mode = "TEST" if is_test else "LIVE"
    print(f"\n✅ Detected {mode} mode")
    
    return secret_key, publishable_key, is_test

def get_product_ids(is_test: bool):
    """Get Stripe product price IDs."""
    print("\n" + "="*60)
    print("Product Configuration")
    print("="*60)
    
    dashboard_url = "https://dashboard.stripe.com/test/products" if is_test else "https://dashboard.stripe.com/products"
    
    print(f"\n📝 Create products in Stripe:")
    print(f"1. Go to {dashboard_url}")
    print(f"2. Create two products:")
    print(f"   - File Organizer Pro ($49)")
    print(f"   - File Organizer Enterprise ($199)")
    print(f"3. Copy the Price IDs (start with 'price_')")
    
    print("\n💡 Or use the Stripe CLI to create products:")
    print("   stripe products create --name='File Organizer Pro'")
    print("   stripe prices create --product=prod_xxx --unit-amount=4900 --currency=usd")
    
    pro_price = input("\nPro Price ID (price_xxx): ").strip()
    ent_price = input("Enterprise Price ID (price_xxx): ").strip()
    
    return pro_price, ent_price

def get_webhook_secret(is_test: bool):
    """Instructions for setting up webhook."""
    print("\n" + "="*60)
    print("Webhook Configuration")
    print("="*60)
    
    print("\n🔗 For local development, use Stripe CLI:")
    print("   stripe listen --forward-to localhost:5000/webhook/stripe")
    print("\n   This will give you a webhook signing secret (whsec_xxx)")
    
    print("\n🌐 For production, configure in Stripe Dashboard:")
    print("   Endpoint URL: https://yourdomain.com/webhook/stripe")
    print("   Events to listen for:")
    print("     - checkout.session.completed")
    print("     - charge.refunded")
    
    webhook_secret = input("\nWebhook Secret (whsec_xxx, or press Enter to skip): ").strip()
    
    return webhook_secret

def get_email_config():
    """Get email configuration."""
    print("\n" + "="*60)
    print("Email Configuration")
    print("="*60)
    
    print("\n📧 Choose email provider:")
    print("1. Gmail SMTP (easiest for testing)")
    print("2. SendGrid (recommended for production)")
    print("3. AWS SES (if already using AWS)")
    
    choice = input("\nChoice (1-3): ").strip()
    
    if choice == "1":
        print("\n📧 Gmail Setup:")
        print("1. Enable 2FA on your Google account")
        print("2. Generate an App Password:")
        print("   https://myaccount.google.com/apppasswords")
        
        smtp_user = input("Gmail address: ").strip()
        smtp_pass = input("App Password: ").strip()
        
        return {
            "EMAIL_BACKEND": "smtp",
            "SMTP_USER": smtp_user,
            "SMTP_PASSWORD": smtp_pass
        }
    
    elif choice == "2":
        print("\n📧 SendGrid Setup:")
        print("1. Create account at sendgrid.com")
        print("2. Create an API key")
        
        api_key = input("SendGrid API Key: ").strip()
        sender = input("Sender email: ").strip()
        
        return {
            "EMAIL_BACKEND": "sendgrid",
            "SENDGRID_API_KEY": api_key,
            "SMTP_FROM": sender
        }
    
    elif choice == "3":
        print("\n📧 AWS SES Setup:")
        aws_key = input("AWS Access Key ID: ").strip()
        aws_secret = input("AWS Secret Key: ").strip()
        region = input("AWS Region [us-east-1]: ").strip() or "us-east-1"
        sender = input("Verified sender email: ").strip()
        
        return {
            "EMAIL_BACKEND": "ses",
            "AWS_ACCESS_KEY_ID": aws_key,
            "AWS_SECRET_ACCESS_KEY": aws_secret,
            "AWS_REGION": region,
            "SMTP_FROM": sender
        }
    
    return {}

def save_config(config: dict):
    """Save configuration to .env file."""
    env_file = Path(".env")
    
    # Read existing or create new
    if env_file.exists():
        with open(env_file, 'r') as f:
            lines = f.readlines()
    else:
        lines = []
    
    # Update with new values
    existing_keys = set()
    for i, line in enumerate(lines):
        if '=' in line and not line.startswith('#'):
            key = line.split('=')[0].strip()
            if key in config:
                lines[i] = f"{key}={config[key]}\n"
                existing_keys.add(key)
    
    # Add new keys
    for key, value in config.items():
        if key not in existing_keys:
            lines.append(f"{key}={value}\n")
    
    # Write back
    with open(env_file, 'w') as f:
        f.writelines(lines)
    
    print(f"\n✅ Configuration saved to {env_file}")

def test_stripe_connection(secret_key: str):
    """Test Stripe API connection."""
    try:
        import stripe
        stripe.api_key = secret_key
        
        # Try to retrieve account info
        account = stripe.Account.retrieve()
        print(f"\n✅ Stripe connection successful!")
        print(f"   Account: {account.settings.get('dashboard', {}).get('display_name', 'Unknown')}")
        print(f"   Email: {account.email}")
        return True
    except Exception as e:
        print(f"\n❌ Stripe connection failed: {e}")
        return False

def main():
    """Main setup flow."""
    print("="*60)
    print("File Organizer - Payment Integration Setup")
    print("="*60)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Create .env file
    setup_env_file()
    
    # Get configuration
    secret_key, publishable_key, is_test = get_stripe_keys()
    pro_price, ent_price = get_product_ids(is_test)
    webhook_secret = get_webhook_secret(is_test)
    email_config = get_email_config()
    
    # Build config dict
    config = {
        "STRIPE_SECRET_KEY": secret_key,
        "STRIPE_PUBLISHABLE_KEY": publishable_key,
        "STRIPE_WEBHOOK_SECRET": webhook_secret,
        "STRIPE_PRO_PRICE_ID": pro_price,
        "STRIPE_ENT_PRICE_ID": ent_price,
        **email_config
    }
    
    # Save config
    save_config(config)
    
    # Test connection
    if secret_key:
        test_stripe_connection(secret_key)
    
    print("\n" + "="*60)
    print("Setup Complete!")
    print("="*60)
    
    print("\n🚀 Next Steps:")
    print("1. Review .env file to ensure all values are correct")
    print("2. Start the webhook server:")
    print("   python src/core/webhook_server.py")
    print("3. For local testing, run Stripe CLI:")
    print("   stripe listen --forward-to localhost:5000/webhook/stripe")
    print("4. Test purchase flow in the app")
    
    print("\n📚 Documentation: PAYMENT_INTEGRATION.md")

if __name__ == "__main__":
    main()
