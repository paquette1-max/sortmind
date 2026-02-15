#!/usr/bin/env python3
"""
Stripe Setup Wizard for File Organizer

Interactive script to configure Stripe payments step-by-step.
No technical knowledge required.

Usage:
    python setup_stripe.py
"""
import os
import sys
import json
import webbrowser
from pathlib import Path
from typing import Optional, Dict, Tuple

# Configuration paths
WORKSPACE = Path("/Users/ripley/.openclaw/workspace/file_organizer")
ENV_FILE = WORKSPACE / ".env"
ENV_EXAMPLE = WORKSPACE / ".env.example"

def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")

def print_step(number: int, title: str):
    """Print a step header."""
    print(f"\n{'─'*70}")
    print(f"  STEP {number}: {title}")
    print(f"{'─'*70}\n")

def ask_yes_no(question: str, default: bool = False) -> bool:
    """Ask a yes/no question."""
    suffix = " [Y/n]: " if default else " [y/N]: "
    response = input(question + suffix).strip().lower()
    if not response:
        return default
    return response in ['y', 'yes']

def open_url(url: str, description: str):
    """Open a URL in browser."""
    print(f"\n🌐 Opening: {description}")
    print(f"   URL: {url}")
    
    if ask_yes_no("Open in browser?", default=True):
        webbrowser.open(url)

def check_stripe_cli() -> bool:
    """Check if Stripe CLI is installed."""
    result = os.system("which stripe > /dev/null 2>&1")
    return result == 0

def install_stripe_cli():
    """Guide to install Stripe CLI."""
    print("\n📦 Stripe CLI Installation")
    print("The Stripe CLI makes setup much easier.")
    
    if ask_yes_no("Install Stripe CLI now?", default=True):
        print("\nInstalling via Homebrew...")
        os.system("brew install stripe/stripe-cli/stripe")
        
        if check_stripe_cli():
            print("✅ Stripe CLI installed successfully!")
            return True
        else:
            print("❌ Installation failed. You can continue without it.")
            return False
    return False

def create_stripe_account():
    """Guide to create Stripe account."""
    print_step(1, "Create Stripe Account")
    
    print("""
To accept payments, you need a Stripe account.

Stripe will need:
  • Your LLC's legal name
  • LLC EIN (Employer Identification Number)
  • Business bank account for payouts
  • Your website or app description

⚠️  Use your LLC info, not personal info!
""")
    
    open_url("https://dashboard.stripe.com/register", "Stripe Registration")
    
    print("\n📋 After creating your account:")
    print("  1. Verify your email")
    print("  2. Complete business verification")
    print("  3. Connect your LLC bank account")
    
    input("\nPress Enter when you've created your account...")

def get_api_keys() -> Tuple[str, str]:
    """Guide to get API keys."""
    print_step(2, "Get API Keys")
    
    print("""
API keys let your app talk to Stripe.

You'll need TWO keys:
  1. Secret Key (starts with sk_live_ or sk_test_) - for your app
  2. Publishable Key (starts with pk_live_ or pk_test_) - for checkout

💡 Use TEST keys first to practice!
💰 Switch to LIVE keys when ready for real sales.
""")
    
    open_url("https://dashboard.stripe.com/apikeys", "API Keys Page")
    
    print("\n📋 To find your keys:")
    print("  1. Go to Developers → API keys")
    print("  2. Copy the Secret key")
    print("  3. Copy the Publishable key")
    print("  4. Toggle 'Test mode' to see test keys")
    
    print("\n" + "─"*50)
    
    # Get keys from user
    secret_key = input("\n🔑 Secret Key (sk_...): ").strip()
    publishable_key = input("🔑 Publishable Key (pk_...): ").strip()
    
    # Detect mode
    is_test = "test" in secret_key
    mode = "TEST" if is_test else "LIVE"
    
    print(f"\n✅ Detected {mode} mode")
    
    if not is_test:
        print("\n⚠️  WARNING: You're using LIVE keys!")
        print("   Real money will be charged. Continue only when ready.")
        if not ask_yes_no("Continue with LIVE mode?", default=False):
            print("\n💡 Switch to test mode in Stripe Dashboard and try again.")
            sys.exit(0)
    
    return secret_key, publishable_key

def create_products(secret_key: str) -> Tuple[str, str]:
    """Guide to create products in Stripe."""
    print_step(3, "Create Products")
    
    print("""
You need to create two products in Stripe:

  1. File Organizer Pro - $49 (one-time payment)
  2. File Organizer Enterprise - $199 (one-time payment)
""")
    
    use_cli = False
    if check_stripe_cli():
        use_cli = ask_yes_no("Use Stripe CLI to create products automatically?", default=True)
    else:
        print("\n💡 Install Stripe CLI for faster setup:")
        if ask_yes_no("Install it now?", default=True):
            use_cli = install_stripe_cli()
    
    pro_price_id = ""
    ent_price_id = ""
    
    if use_cli:
        print("\n🚀 Creating products via CLI...")
        
        # Set API key for CLI
        os.environ["STRIPE_API_KEY"] = secret_key
        
        # Create Pro product
        print("\n  Creating File Organizer Pro ($49)...")
        result = os.popen(
            'stripe products create --name="File Organizer Pro" '
            '--description="Unlimited AI analysis and batch processing"'
        ).read()
        
        try:
            pro_product = json.loads(result)
            pro_product_id = pro_product["id"]
            
            # Create price for Pro
            result = os.popen(
                f'stripe prices create --product={pro_product_id} '
                f'--unit-amount=4900 --currency=usd --name="Pro License"'
            ).read()
            pro_price = json.loads(result)
            pro_price_id = pro_price["id"]
            print(f"  ✅ Pro: {pro_price_id}")
            
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            use_cli = False
    
    if not use_cli or not pro_price_id:
        # Manual creation
        print("\n📋 Manual Product Creation:")
        print("\n1. Go to Products in Stripe Dashboard")
        print("2. Click 'Add Product'")
        print("3. Create these products:")
        print()
        print("   📝 File Organizer Pro")
        print("      Price: $49.00")
        print("      Billing: One time")
        print()
        print("   📝 File Organizer Enterprise")
        print("      Price: $199.00")
        print("      Billing: One time")
        
        open_url("https://dashboard.stripe.com/products", "Products Page")
        
        print("\n📋 After creating products:")
        print("  1. Click on each product")
        print("  2. Find the Price ID (starts with 'price_')")
        print("  3. Copy it below")
        
        print("\n" + "─"*50)
        pro_price_id = input("\n💰 Pro Price ID (price_...): ").strip()
        ent_price_id = input("💰 Enterprise Price ID (price_...): ").strip()
    
    return pro_price_id, ent_price_id

def configure_email() -> Dict[str, str]:
    """Guide to configure email."""
    print_step(4, "Configure Email")
    
    print("""
You need a way to send license emails to customers.

Choose your email provider:

  1. Gmail (easiest, good for testing)
     • Use your existing Gmail
     • Need to create an App Password
     • Free

  2. SendGrid (best for production)
     • 100 emails/day free
     • Better deliverability
     • Professional

  3. AWS SES (if you use AWS)
     • Very cheap ($0.10 per 1000 emails)
     • More complex setup
""")
    
    choice = input("\nChoice [1-3, default=1]: ").strip() or "1"
    
    config = {}
    
    if choice == "1":
        print("\n📧 Gmail Setup")
        print("\nYou'll need an App Password (not your regular password):")
        print("  1. Enable 2FA on your Google account")
        print("  2. Go to https://myaccount.google.com/apppasswords")
        print("  3. Generate password for 'Mail'")
        
        open_url("https://myaccount.google.com/apppasswords", "App Passwords")
        
        config["EMAIL_BACKEND"] = "smtp"
        config["SMTP_HOST"] = "smtp.gmail.com"
        config["SMTP_PORT"] = "587"
        config["SMTP_USER"] = input("\nGmail address: ").strip()
        config["SMTP_PASSWORD"] = input("App Password: ").strip()
        config["SMTP_FROM"] = config["SMTP_USER"]
        
    elif choice == "2":
        print("\n📧 SendGrid Setup")
        print("\n  1. Create account at sendgrid.com")
        print("  2. Verify sender email")
        print("  3. Create API key")
        
        open_url("https://signup.sendgrid.com", "SendGrid Signup")
        
        config["EMAIL_BACKEND"] = "sendgrid"
        config["SENDGRID_API_KEY"] = input("\nSendGrid API Key (SG...): ").strip()
        config["SMTP_FROM"] = input("Sender email (must be verified): ").strip()
        
    elif choice == "3":
        print("\n📧 AWS SES Setup")
        config["EMAIL_BACKEND"] = "ses"
        config["AWS_ACCESS_KEY_ID"] = input("AWS Access Key ID: ").strip()
        config["AWS_SECRET_ACCESS_KEY"] = input("AWS Secret Key: ").strip()
        config["AWS_REGION"] = input("AWS Region [us-east-1]: ").strip() or "us-east-1"
        config["SMTP_FROM"] = input("Verified sender email: ").strip()
    
    return config

def save_config(config: Dict[str, str]):
    """Save configuration to .env file."""
    print_step(5, "Save Configuration")
    
    # Read existing or create new
    if ENV_FILE.exists():
        with open(ENV_FILE, 'r') as f:
            lines = f.readlines()
    else:
        lines = []
    
    # Build config dict from existing
    existing = {}
    for line in lines:
        if '=' in line and not line.startswith('#'):
            key, value = line.strip().split('=', 1)
            existing[key] = value
    
    # Update with new values
    existing.update(config)
    
    # Write back
    with open(ENV_FILE, 'w') as f:
        for key, value in existing.items():
            f.write(f"{key}={value}\n")
    
    # Secure permissions
    os.chmod(ENV_FILE, 0o600)
    
    print(f"✅ Configuration saved to {ENV_FILE}")
    print(f"🔒 File permissions set to secure (600)")

def test_configuration():
    """Test the configuration."""
    print_step(6, "Test Configuration")
    
    print("Testing your setup...\n")
    
    # Test 1: Load .env
    print("1. Loading configuration...")
    if not ENV_FILE.exists():
        print("   ❌ .env file not found!")
        return False
    
    # Load env vars
    with open(ENV_FILE, 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value
    
    print("   ✅ Configuration loaded")
    
    # Test 2: Stripe connection
    print("\n2. Testing Stripe connection...")
    try:
        import stripe
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        account = stripe.Account.retrieve()
        print(f"   ✅ Connected to Stripe!")
        print(f"   📧 Account: {account.email}")
        print(f"   🏢 Business: {account.settings.get('dashboard', {}).get('display_name', 'N/A')}")
    except Exception as e:
        print(f"   ❌ Stripe connection failed: {e}")
        return False
    
    # Test 3: Email configuration
    print("\n3. Checking email configuration...")
    email_backend = os.getenv("EMAIL_BACKEND")
    if email_backend:
        print(f"   ✅ Email backend: {email_backend}")
        if email_backend == "smtp":
            smtp_user = os.getenv("SMTP_USER")
            if smtp_user:
                print(f"   ✅ SMTP user: {smtp_user}")
    else:
        print("   ❌ Email backend not configured")
        return False
    
    print("\n" + "="*50)
    print("✅ All tests passed!")
    print("="*50)
    
    return True

def show_next_steps():
    """Show what to do next."""
    print_header("Setup Complete!")
    
    print("""
🎉 Your Stripe payment integration is configured!

Next Steps:

1. TEST THE FLOW (Recommended)
   python src/core/stripe_poller.py --dry-run

2. RUN MANUALLY
   python src/core/stripe_poller.py

3. SET UP AUTOMATIC POLLING
   # Copy the launchd config
   cp com.openclaw.fileorganizer.stripe-poller.plist ~/Library/LaunchAgents/
   
   # Enable it
   launchctl load ~/Library/LaunchAgents/com.openclaw.fileorganizer.stripe-poller.plist
   
   # Check status
   launchctl list | grep stripe-poller

4. MONITOR ACTIVITY
   python src/core/poller_monitor.py --report

5. TEST PURCHASE (Test Mode)
   - Run File Organizer
   - Click "Buy Pro"
   - Use Stripe test card: 4242 4242 4242 4242
   - Run poller to generate license

📚 Documentation: PAYMENT_INTEGRATION_README.md

💬 Questions? The poller_monitor.py will alert you when:
   • You make a sale (good news!)
   • You should switch to webhooks (3+ sales/week)
   • Something needs attention (errors)
""")

def main():
    """Main setup flow."""
    print_header("File Organizer - Stripe Setup Wizard")
    
    print("""
This wizard will help you set up Stripe payments for File Organizer.

You'll need:
  • About 20 minutes
  • Your LLC's EIN and bank info (for Stripe account)
  • A Gmail account (for sending license emails)

Ready to start earning? Let's go!
""")
    
    if not ask_yes_no("Start setup?", default=True):
        print("\nSetup cancelled. Run again when ready.")
        return
    
    # Step 1: Create account
    create_stripe_account()
    
    # Step 2: Get API keys
    secret_key, publishable_key = get_api_keys()
    
    # Step 3: Create products
    pro_price_id, ent_price_id = create_products(secret_key)
    
    # Step 4: Configure email
    email_config = configure_email()
    
    # Build full config
    config = {
        "STRIPE_SECRET_KEY": secret_key,
        "STRIPE_PUBLISHABLE_KEY": publishable_key,
        "STRIPE_PRO_PRICE_ID": pro_price_id,
        "STRIPE_ENT_PRICE_ID": ent_price_id,
        **email_config
    }
    
    # Step 5: Save
    save_config(config)
    
    # Step 6: Test
    if test_configuration():
        show_next_steps()
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
        print("You can fix issues and run: python setup_stripe.py")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
