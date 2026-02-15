# File Organizer - Payment Integration

This document describes the Stripe payment integration for File Organizer Pro licensing.

## Quick Decision: Which Mode?

### 🔄 POLLING MODE (Recommended to Start)
**No server required** - Run periodically on your Mac

✅ Good for: Getting started, testing, low volume (< 3 sales/week)  
❌ Trade-off: 4-hour delay max, manual or scheduled runs  
💰 Cost: $0 (runs on your existing Mac)  

**Start here.** Switch to webhooks when you have consistent sales.

### ⚡ WEBHOOK MODE (For Scale)
**24/7 server** - Instant license delivery

✅ Good for: High volume, instant delivery, professional feel  
❌ Trade-off: Need always-on server ($5-10/month)  
💰 Cost: VPS or cloud hosting

---

## Overview

The payment system handles:
- **Stripe Checkout**: Secure payment processing
- **License Generation**: Unique license key creation
- **Email Delivery**: Automatic license key emails
- **License Validation**: Key verification in the app

### Two Architectures

**Polling Mode (Current):**
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  File Organizer │────▶│  Stripe Checkout │────▶│  Customer Pays  │
│     (Qt App)    │     │   (Hosted Page)  │     │  (Credit Card)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                          │
                              ┌─────────────────┐        │
                              │  Poller Script  │◀───────┘
                              │  (Every 4 hrs)  │ (checks Stripe API)
                              └────────┬────────┘
                                       │
                              ┌────────▼────────┐
                              │  License DB     │
                              │  Email Sender   │
                              └─────────────────┘
```

**Webhook Mode (Future):**
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  File Organizer │────▶│  Stripe Checkout │────▶│  Customer Pays  │
│     (Qt App)    │     │   (Hosted Page)  │     │  (Credit Card)  │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                          │
┌─────────────────┐     ┌─────────────────┐              │
│  Customer Gets  │◀────│  Email Sender   │◀─────────────┘
│  License Email  │     │                 │    (Webhook)
└─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │ Webhook Server  │
                        │ (Flask)         │
                        └─────────────────┘
```

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  File Organizer │────▶│  Stripe Checkout │────▶│  Customer Pays  │
│     (Qt App)    │     │   (Hosted Page)  │     │  (Credit Card)  │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                          │
┌─────────────────┐     ┌─────────────────┐              │
│  Customer Gets  │◀────│  Email Sender   │◀─────────────┘
│  License Email  │     │                 │    (Webhook)
└─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │ Webhook Server  │
                        │ (Flask)         │
                        └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │ License DB      │
                        │ (JSON file)     │
                        └─────────────────┘
```

## File Structure

```
file_organizer/
├── src/
│   └── core/
│       ├── stripe_integration.py    # Main Stripe integration
│       ├── email_sender.py          # Email delivery
│       ├── webhook_server.py        # Webhook endpoint
│       └── license_manager.py       # Existing license management
├── src/ui/dialogs/
│   └── license_dialog.py            # Updated purchase UI
├── .env                             # Your API keys (gitignored)
├── .env.example                     # Template
├── requirements-payments.txt        # Dependencies
├── setup_payments.py                # Interactive setup
└── PAYMENT_INTEGRATION.md           # This file
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements-payments.txt
```

Or manually:
```bash
pip install stripe flask python-dotenv
```

### 2. Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit with your API keys
nano .env
```

Required variables:
```env
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRO_PRICE_ID=price_...
STRIPE_ENT_PRICE_ID=price_...
EMAIL_BACKEND=smtp
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### 3. Run Setup Script (Optional but Recommended)

```bash
python setup_payments.py
```

This interactive script will:
- Check dependencies
- Collect your Stripe API keys
- Create products and get price IDs
- Configure email settings
- Test the connection

### 4. Start the Webhook Server

For local development:
```bash
# Terminal 1: Start webhook server
python src/core/webhook_server.py

# Terminal 2: Forward Stripe webhooks
stripe listen --forward-to localhost:5000/webhook/stripe
```

For production:
```bash
# Deploy webhook server
export FLASK_DEBUG=false
export PORT=5000
python src/core/webhook_server.py
```

Then configure webhook URL in Stripe Dashboard:
- URL: `https://yourdomain.com/webhook/stripe`
- Events: `checkout.session.completed`, `charge.refunded`

## Stripe Setup

### Create Stripe Account

1. Go to [stripe.com](https://stripe.com)
2. Create account (use your LLC info)
3. Complete verification (business docs, bank account)
4. Get API keys from Dashboard

### Create Products

**Option 1: Via Dashboard**
1. Go to Products → Add Product
2. Create "File Organizer Pro" - $49
3. Create "File Organizer Enterprise" - $199
4. Copy the Price IDs (start with `price_`)

**Option 2: Via CLI**
```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Login
stripe login

# Create products
stripe products create --name="File Organizer Pro" --description="Unlimited AI analysis"
stripe prices create --product=prod_xxx --unit-amount=4900 --currency=usd

stripe products create --name="File Organizer Enterprise" --description="Business features"
stripe prices create --product=prod_yyy --unit-amount=19900 --currency=usd
```

### Webhook Configuration

**Local Development:**
```bash
stripe listen --forward-to localhost:5000/webhook/stripe
```

This outputs a webhook secret (whsec_xxx) to use in your .env file.

**Production:**
1. Go to Stripe Dashboard → Developers → Webhooks
2. Add endpoint: `https://yourdomain.com/webhook/stripe`
3. Select events:
   - `checkout.session.completed`
   - `charge.refunded`
4. Copy the signing secret to your .env file

## Email Configuration

### Option 1: Gmail (Easiest for Testing)

1. Enable 2FA on your Google account
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Set in .env:
```env
EMAIL_BACKEND=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-app@gmail.com
SMTP_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

### Option 2: SendGrid (Production)

1. Create account at [sendgrid.com](https://sendgrid.com)
2. Verify sender email
3. Create API key
4. Set in .env:
```env
EMAIL_BACKEND=sendgrid
SENDGRID_API_KEY=SG.xxx
SMTP_FROM=noreply@yourdomain.com
```

### Option 3: AWS SES

1. Verify domain in SES Console
2. Create SMTP credentials
3. Set in .env:
```env
EMAIL_BACKEND=ses
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
SMTP_FROM=noreply@yourdomain.com
```

## Usage

### In the Application

1. User clicks "Buy Pro" or "Buy Enterprise"
2. Dialog prompts for email (optional)
3. Stripe Checkout opens in browser
4. User completes payment
5. Webhook triggers license generation
6. License email sent automatically
7. User enters key in app to activate

### Testing the Flow

```bash
# 1. Start webhook server
python src/core/webhook_server.py

# 2. In another terminal, forward Stripe events
stripe listen --forward-to localhost:5000/webhook/stripe

# 3. Trigger test checkout (use Stripe test keys)
python -c "
from src.core.stripe_integration import create_checkout_url
url, err = create_checkout_url('pro', 'test@example.com')
print(f'Checkout URL: {url}')
"

# 4. Complete checkout with test card: 4242 4242 4242 4242

# 5. Check webhook server logs for license generation

# 6. Validate the license
python -c "
from src.core.stripe_integration import validate_license
is_valid, info = validate_license('PRO-XXXX-XXXX-XXXX')
print(f'Valid: {is_valid}, Info: {info}')
"
```

## API Reference

### stripe_integration.py

```python
from src.core.stripe_integration import (
    StripeLicenseManager,
    create_checkout_url,
    validate_license
)

# Create checkout session
url, error = create_checkout_url(tier="pro", email="customer@example.com")

# Validate license
is_valid, license_info = validate_license("PRO-XXXX-XXXX-XXXX")

# Direct manager usage
manager = StripeLicenseManager()
url, error = manager.create_checkout_session("enterprise", email)
success, error, license = manager.handle_webhook(payload, signature)
```

### email_sender.py

```python
from src.core.email_sender import send_license_email
from src.core.stripe_integration import LicenseInfo

license_info = LicenseInfo(...)
send_license_email(license_info)
```

### webhook_server.py

```python
# Standalone server
python src/core/webhook_server.py

# Or integrate into existing Flask app
from src.core.webhook_server import create_webhook_blueprint
app.register_blueprint(create_webhook_blueprint(), url_prefix='/webhook')
```

## Security

### API Key Storage

- ✅ Use environment variables (`.env` file)
- ✅ Never commit `.env` to git
- ✅ Use different keys for test/production
- ✅ Rotate keys periodically

### Webhook Security

- ✅ Always verify webhook signatures
- ✅ Use HTTPS in production
- ✅ Return 200 quickly (process async if needed)
- ✅ Log all webhook events

### License Key Security

- Keys are cryptographically random (secrets.token_hex)
- Database file has restricted permissions (0o600)
- No server-side license validation required (optional)

## License Database

Location: `~/.config/sortmind/stripe_licenses.json`

Structure:
```json
{
  "licenses": [
    {
      "key": "PRO-ABCD-EFGH-IJKL",
      "tier": "pro",
      "email": "customer@example.com",
      "created_at": "2026-02-15T09:30:00",
      "stripe_payment_id": "pi_xxx",
      "stripe_customer_id": "cus_xxx",
      "activated_at": "2026-02-15T09:35:00"
    }
  ]
}
```

## Troubleshooting

### Webhook not receiving events

1. Check webhook URL is correct in Stripe Dashboard
2. Verify STRIPE_WEBHOOK_SECRET is set correctly
3. Check firewall isn't blocking port 5000
4. Use `stripe listen` to see events in real-time

### Emails not sending

1. Check EMAIL_BACKEND is set correctly
2. Verify SMTP credentials
3. Check spam folders
4. Review logs: `~/.openclaw/logs/`

### License key not working

1. Check license exists in database
2. Verify not marked as refunded
3. Check expiration date (if set)
4. Look for typos in key entry

### Stripe errors

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check Stripe response
import stripe
stripe.api_key = "sk_test_..."
print(stripe.Account.retrieve())
```

## Deployment

### Production Checklist

- [ ] Use Stripe LIVE keys (not test)
- [ ] Webhook endpoint uses HTTPS
- [ ] Webhook secret configured
- [ ] Email backend configured (not Gmail for volume)
- [ ] Database backups scheduled
- [ ] Logging configured
- [ ] Error monitoring (Sentry recommended)

### Server Requirements

- Python 3.8+
- 512MB RAM minimum
- Port 5000 (or configurable)
- HTTPS certificate (Let's Encrypt free)

### Docker (Optional)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements-payments.txt .
RUN pip install -r requirements-payments.txt

COPY src/ ./src/
COPY .env .

EXPOSE 5000

CMD ["python", "src/core/webhook_server.py"]
```

## Pricing

### Stripe Fees

- **Payment processing**: 2.9% + 30¢ per transaction
- **International cards**: +1%
- **Total for $49 Pro**: ~$1.72 fee, $47.28 net
- **Total for $199 Enterprise**: ~$6.07 fee, $192.93 net

### Payout Schedule

- **Automatic**: Daily (2-day rolling)
- **Manual**: Request anytime
- **Minimum**: None

## Support

### Resources

- [Stripe Documentation](https://stripe.com/docs)
- [Stripe API Reference](https://stripe.com/docs/api)
- [Webhook Best Practices](https://stripe.com/docs/webhooks/best-practices)

### Getting Help

1. Check logs: `~/.openclaw/logs/`
2. Stripe Dashboard → Logs
3. Webhook delivery attempts in Dashboard
4. Contact: support@yourdomain.com

## License

This payment integration is part of File Organizer Pro.
