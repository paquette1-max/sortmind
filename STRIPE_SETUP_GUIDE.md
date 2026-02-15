# Stripe Setup Guide - Step by Step

This guide walks you through setting up Stripe for File Organizer payments.

## Overview

**What you'll accomplish:**
1. Create a Stripe account (using your LLC)
2. Set up products (Pro $49, Enterprise $199)
3. Get API keys
4. Configure email delivery
5. Test the entire flow

**Time required:** 30-45 minutes

---

## Step 1: Create Stripe Account (10 min)

### 1.1 Go to Stripe
- Visit: https://dashboard.stripe.com/register
- Click "Create account"

### 1.2 Choose Account Type
- Select **"Business"** (not Individual)
- Business type: **Limited Liability Company (LLC)**
- Use your LLC's legal name

### 1.3 Enter Business Details
You'll need:
- **Business name:** Your LLC's legal name
- **EIN:** Your LLC's Employer Identification Number
- **Business address:** Your LLC's address (can be your home)
- **Business phone:** Your number
- **Website:** You can use GitHub or say "Desktop app - not launched yet"

### 1.4 Verify Email
- Check your email for verification link
- Click to confirm

### 1.5 Complete Verification (Important!)
Stripe will ask for:
1. **Business documentation**
   - Upload your LLC's Articles of Organization
   - Or EIN confirmation letter from IRS

2. **Bank account**
   - Connect your LLC's business checking account
   - This is where payouts go

3. **Representative info**
   - Your name, DOB, SSN (as LLC owner)
   - Home address

⚠️ **Use your LLC info throughout, not personal info**

### 1.6 Wait for Approval
- Usually instant for simple cases
- May take 1-2 days if manual review needed
- You'll get an email when approved

---

## Step 2: Create Products (5 min)

### 2.1 Navigate to Products
- In Stripe Dashboard, click **"Products"** in left sidebar
- Click **"Add product"**

### 2.2 Create Pro Product
Fill in:
- **Name:** File Organizer Pro
- **Description:** Unlimited AI analysis, batch processing, and custom patterns
- **Pricing model:** Standard pricing
- **Price:** $49.00
- **Billing period:** One time

Click **"Save product"**

### 2.3 Create Enterprise Product
Click **"Add product"** again:
- **Name:** File Organizer Enterprise
- **Description:** Everything in Pro plus cloud sync and priority support
- **Pricing model:** Standard pricing
- **Price:** $199.00
- **Billing period:** One time

Click **"Save product"**

### 2.4 Copy Price IDs
You need the Price IDs (start with `price_`):

1. Click on **File Organizer Pro**
2. Find the price section
3. Copy the Price ID (looks like `price_1AbCdEfGhIjKlMnOpQrStUv`)
4. Save it somewhere - you'll need it soon
5. Do the same for Enterprise

---

## Step 3: Get API Keys (3 min)

### 3.1 Go to API Keys
- In Stripe Dashboard, click **"Developers"** → **"API keys"**

### 3.2 Switch to Test Mode (Important!)
- Toggle **"Test mode"** ON (top right)
- This lets you practice without real money

### 3.3 Copy Keys
You'll see:
- **Secret key** (starts with `sk_test_`) - click "Reveal"
- **Publishable key** (starts with `pk_test_`)

Copy both and save them. The secret key is like a password - keep it safe!

### 3.4 Test vs Live
- **Test keys** (`sk_test_`, `pk_test_`): Practice, no real money
- **Live keys** (`sk_live_`, `pk_live_`): Real transactions

We'll use test keys for now and switch to live later.

---

## Step 4: Configure Email (5 min)

### Option A: Gmail (Easiest)

#### 4.1 Enable 2FA on Google Account
- Go to https://myaccount.google.com/security
- Turn on 2-Step Verification

#### 4.2 Create App Password
- Go to https://myaccount.google.com/apppasswords
- Click "Select app" → "Mail"
- Click "Select device" → "Other (Custom name)"
- Type: "File Organizer"
- Click "Generate"
- **Copy the 16-character password** (looks like: `abcd efgh ijkl mnop`)

⚠️ This is different from your regular Gmail password!

### Option B: SendGrid (Better for Production)

#### 4.1 Create SendGrid Account
- Go to https://signup.sendgrid.com
- Sign up for free plan (100 emails/day)

#### 4.2 Verify Sender Email
- In SendGrid dashboard, go to **Settings** → **Sender Authentication**
- Verify your email address (click link they send)

#### 4.3 Create API Key
- Go to **Settings** → **API Keys**
- Click **"Create API Key"**
- Name: "File Organizer"
- Permissions: **Full Access** (or Restricted Access with Mail Send)
- Click **"Create & View"**
- **Copy the API key** (starts with `SG.`)

---

## Step 5: Configure Environment (10 min)

### 5.1 Copy Template
Open Terminal and run:

```bash
cd ~/.openclaw/workspace/file_organizer
cp .env.example .env
```

### 5.2 Edit .env File
Open the file in a text editor:

```bash
nano .env
```

Or use TextEdit:
```bash
open -e .env
```

### 5.3 Fill in Your Values

Replace the placeholder values with your actual keys:

```env
# Stripe API Keys (TEST mode for now)
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxxxxxxxxxxxx

# Stripe Product Price IDs
STRIPE_PRO_PRICE_ID=price_xxxxxxxxxxxxx
STRIPE_ENT_PRICE_ID=price_xxxxxxxxxxxxx

# Email Configuration
EMAIL_BACKEND=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your.email@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop
SMTP_FROM=your.email@gmail.com
```

For SendGrid instead:
```env
EMAIL_BACKEND=sendgrid
SENDGRID_API_KEY=SG.xxxxxxxxxxxxx
SMTP_FROM=noreply@yourdomain.com
```

### 5.4 Save and Secure
Save the file. The setup script will set secure permissions automatically.

---

## Step 6: Test the Setup (5 min)

### 6.1 Test Connection

Run the test:

```bash
cd ~/.openclaw/workspace/file_organizer
python3 src/core/stripe_poller.py --dry-run
```

You should see:
```
[date/time] Checking for payments since ...
Found 0 new payments

═══════════════════════════════════════════
Stripe License Poller - Summary
═══════════════════════════════════════════
Checked: ...
...
No new payments
```

If you see errors, check your .env values.

### 6.2 Test Purchase Flow

#### Start File Organizer
```bash
python3 src/main.py
```

#### Simulate Purchase
1. In the app, go to **Help** → **License**
2. Click **"Buy Pro"** or **"Buy Enterprise"**
3. A browser window opens to Stripe Checkout (test mode)
4. Use test card: `4242 4242 4242 4242`
   - Expiry: Any future date (12/30)
   - CVC: Any 3 digits (123)
   - ZIP: Any 5 digits (12345)
5. Complete the "purchase"

#### Generate License
Back in Terminal:
```bash
python3 src/core/stripe_poller.py
```

This should:
- Find the test payment
- Generate a license key
- Send you an email (check spam!)

Check your email - you should receive the license key!

---

## Step 7: Go Live (When Ready)

### 7.1 Switch to Live Mode

1. In Stripe Dashboard, toggle **"Test mode"** OFF
2. Go to **Developers** → **API keys**
3. Copy the **LIVE** keys (start with `sk_live_`, `pk_live_`)
4. Update your `.env` file:
   - Replace test keys with live keys

### 7.2 Update Price IDs

1. Go to **Products** in live mode
2. Copy the live Price IDs
3. Update `.env` with live Price IDs

### 7.3 Test Live Mode

Make a real $1 purchase to yourself:
1. Update price to $1 temporarily in Stripe
2. Complete purchase with real card
3. Run poller
4. Check you get email
5. Change price back to $49

### 7.4 Set Up Automatic Polling

Copy and enable the launchd job:

```bash
# Copy config to LaunchAgents
cp ~/.openclaw/workspace/file_organizer/com.openclaw.fileorganizer.stripe-poller.plist ~/Library/LaunchAgents/

# Load it
launchctl load ~/Library/LaunchAgents/com.openclaw.fileorganizer.stripe-poller.plist

# Verify it's loaded
launchctl list | grep stripe-poller
```

The poller will now run every 4 hours automatically.

---

## Troubleshooting

### "Stripe API key not found"
- Check `.env` file exists in file_organizer folder
- Verify `STRIPE_SECRET_KEY` is set correctly
- Make sure no extra spaces around the = sign

### "No module named stripe"
```bash
pip3 install stripe
```

### "Authentication failed" email error
- Gmail: Make sure you used App Password, not regular password
- SendGrid: Verify sender email in SendGrid dashboard
- Check firewall isn't blocking port 587

### Poller not finding payments
- Make sure you're in the right mode (test vs live)
- Check that price IDs match your Stripe products
- Verify payment was successful in Stripe Dashboard

---

## Next Steps

### Monitor Sales

```bash
# Check status anytime
python3 src/core/poller_monitor.py --report

# Check for alerts
python3 src/core/poller_monitor.py --check
```

### Manual Poll (if needed)

```bash
# Check immediately
python3 src/core/stripe_poller.py
```

### View Logs

```bash
# Poller logs
tail -f ~/.openclaw/logs/stripe-poller.log

# Monitor alerts
tail -f ~/.openclaw/logs/poller_alerts.log
```

### Switch to Webhooks (When Ready)

When you consistently get 3+ sales/week:
1. Set up webhook server (see PAYMENT_INTEGRATION_README.md)
2. Deploy to VPS ($5/month DigitalOcean/Linode)
3. Disable polling: `launchctl unload ~/Library/LaunchAgents/com.openclaw.fileorganizer.stripe-poller.plist`

---

## Quick Reference

### Files
- `.env` - Your configuration (secrets)
- `.env.example` - Template
- `src/core/stripe_poller.py` - Polls for payments
- `src/core/poller_monitor.py` - Monitors and alerts
- `com.openclaw.fileorganizer.stripe-poller.plist` - Auto-launch config

### Commands
```bash
# Manual poll
python3 src/core/stripe_poller.py

# Dry run (test without sending)
python3 src/core/stripe_poller.py --dry-run

# Check status
python3 src/core/poller_monitor.py --report

# Enable auto-polling
launchctl load ~/Library/LaunchAgents/com.openclaw.fileorganizer.stripe-poller.plist

# Disable auto-polling
launchctl unload ~/Library/LaunchAgents/com.openclaw.fileorganizer.stripe-poller.plist
```

### Test Cards
- **Success:** 4242 4242 4242 4242
- **Decline:** 4000 0000 0000 0002
- **Require 3D Secure:** 4000 0025 0000 3155

---

## Need Help?

- Stripe Docs: https://stripe.com/docs
- Check logs: `~/.openclaw/logs/`
- Run setup wizard: `python3 setup_stripe.py`

Good luck with your first sale! 🎉
