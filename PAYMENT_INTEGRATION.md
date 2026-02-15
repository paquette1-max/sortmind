# Payment Integration Options for File Organizer

## Option 1: Paddle (Recommended for Simplicity)

### Setup Steps:
1. Create account at paddle.com
2. Create a product (File Organizer Pro - $49)
3. Get your API keys (Vendor ID + API Key)
4. Set webhook URL for license generation

### Code Integration:

```python
# paddle_integration.py
import requests
import secrets
import hashlib
from datetime import datetime
from typing import Optional, Dict

PADDLE_VENDOR_ID = "your_vendor_id"
PADDLE_API_KEY = "your_api_key"
PADDLE_PUBLIC_KEY = "your_public_key"  # For webhook verification

class PaddleLicenseManager:
    """Handles Paddle checkout and license generation."""
    
    def __init__(self):
        self.api_base = "https://vendors.paddle.com/api/2.0"
    
    def generate_checkout_url(self, product_id: str, customer_email: str) -> str:
        """Generate a Paddle checkout URL for the customer."""
        # This opens Paddle's hosted checkout page
        return f"https://pay.paddle.com/checkout/{product_id}?email={customer_email}"
    
    def handle_webhook(self, webhook_data: Dict) -> Optional[str]:
        """
        Called when Paddle sends payment success webhook.
        Returns license key to email to customer.
        """
        # Verify webhook signature (security)
        if not self._verify_webhook(webhook_data):
            return None
        
        if webhook_data.get("alert_name") == "payment_succeeded":
            email = webhook_data.get("email")
            product_id = webhook_data.get("product_id")
            
            # Generate license key
            license_key = self._generate_license_key(product_id)
            
            # Store in your database (email -> license_key)
            self._save_license(email, license_key, product_id)
            
            # Paddle will email the customer, or you can
            return license_key
        
        return None
    
    def _generate_license_key(self, product_id: str) -> str:
        """Generate a unique license key."""
        # Format: PRO-XXXX-XXXX-XXXX
        prefix = "PRO" if "pro" in product_id else "ENT"
        sections = [secrets.token_hex(4).upper()[:4] for _ in range(3)]
        return f"{prefix}-{sections[0]}-{sections[1]}-{sections[2]}"
    
    def _verify_webhook(self, data: Dict) -> bool:
        """Verify webhook came from Paddle (prevents fraud)."""
        # Implementation: verify signature with PADDLE_PUBLIC_KEY
        return True  # Simplified - implement actual verification
    
    def _save_license(self, email: str, key: str, product_id: str):
        """Save license to database."""
        # Your database logic here
        pass

# Flask/FastAPI webhook endpoint example:
from flask import Flask, request, jsonify

app = Flask(__name__)
paddle = PaddleLicenseManager()

@app.route("/webhook/paddle", methods=["POST"])
def paddle_webhook():
    """Receive Paddle payment notifications."""
    data = request.form.to_dict()
    
    license_key = paddle.handle_webhook(data)
    
    if license_key:
        # Optionally send your own email with the key
        # Or let Paddle handle it
        send_license_email(data.get("email"), license_key)
    
    return jsonify({"status": "ok"})

# In your license_dialog.py - replace get_purchase_url():
def get_purchase_url(self) -> str:
    """Open Paddle checkout."""
    paddle = PaddleLicenseManager()
    return paddle.generate_checkout_url(
        product_id="pro_product_id",
        customer_email="customer@example.com"  # Pre-fill if known
    )
```

### Webhook Events to Handle:
- `payment_succeeded` → Generate & email license
- `subscription_created` → For recurring billing
- `subscription_cancelled` → Revoke license after period

### Advantages:
- Paddle hosts checkout page (no UI work)
- Automatic tax compliance
- Built-in license email templates
- Handles VAT, refunds, chargebacks

---

## Option 2: Stripe (More Control, More Work)

### Setup Steps:
1. Create Stripe account
2. Create product + price in dashboard
3. Build checkout page (or use Stripe Checkout)
4. Set webhook endpoint
5. **Tax setup:** Enable Stripe Tax (adds 0.5% fee) or handle yourself

### Code Integration:

```python
# stripe_integration.py
import stripe
import secrets
from typing import Optional, Dict

stripe.api_key = "sk_live_..."  # Secret key
STRIPE_WEBHOOK_SECRET = "whsec_..."

STRIPE_PRODUCTS = {
    "pro": {
        "price_id": "price_1234567890",
        "amount": 4900,  # $49.00 in cents
        "name": "File Organizer Pro"
    },
    "enterprise": {
        "price_id": "price_0987654321",
        "amount": 19900,  # $199.00
        "name": "File Organizer Enterprise"
    }
}

class StripeLicenseManager:
    """Handles Stripe checkout and license generation."""
    
    def create_checkout_session(self, tier: str, customer_email: str) -> str:
        """
        Create Stripe Checkout session.
        Returns URL to redirect customer to.
        """
        product = STRIPE_PRODUCTS.get(tier)
        if not product:
            raise ValueError(f"Unknown tier: {tier}")
        
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": product["price_id"],
                "quantity": 1,
            }],
            mode="payment",  # One-time purchase
            success_url="https://yourapp.com/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="https://yourapp.com/cancel",
            customer_email=customer_email,
            metadata={
                "tier": tier,
                "product": "file_organizer"
            }
        )
        
        return session.url
    
    def handle_webhook(self, payload: bytes, signature: str) -> Optional[str]:
        """
        Verify and process Stripe webhook.
        Returns license key if payment succeeded.
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, STRIPE_WEBHOOK_SECRET
            )
        except stripe.error.SignatureVerificationError:
            return None
        
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            
            # Extract info
            customer_email = session.get("customer_email")
            tier = session.get("metadata", {}).get("tier", "pro")
            
            # Generate license
            license_key = self._generate_license_key(tier)
            
            # Save to database
            self._save_license(customer_email, license_key, tier)
            
            # Send email with license
            self._send_license_email(customer_email, license_key, tier)
            
            return license_key
        
        return None
    
    def _generate_license_key(self, tier: str) -> str:
        """Generate license key."""
        prefix = "PRO" if tier == "pro" else "ENT"
        sections = [secrets.token_hex(4).upper()[:4] for _ in range(3)]
        return f"{prefix}-{sections[0]}-{sections[1]}-{sections[2]}"
    
    def _save_license(self, email: str, key: str, tier: str):
        """Save to database."""
        # Your DB logic
        pass
    
    def _send_license_email(self, email: str, key: str, tier: str):
        """Send license email via SendGrid/SES/etc."""
        # Your email logic
        pass

# Flask webhook endpoint:
@app.route("/webhook/stripe", methods=["POST"])
def stripe_webhook():
    """Receive Stripe events."""
    payload = request.data
    signature = request.headers.get("Stripe-Signature")
    
    stripe_mgr = StripeLicenseManager()
    license_key = stripe_mgr.handle_webhook(payload, signature)
    
    if license_key:
        print(f"License generated: {license_key}")
    
    return jsonify({"status": "success"})

# In-app purchase flow:
def purchase_license(tier: str):
    """Called when user clicks 'Buy Pro' in app."""
    stripe_mgr = StripeLicenseManager()
    
    # Open browser to Stripe Checkout
    checkout_url = stripe_mgr.create_checkout_session(
        tier=tier,
        customer_email="user@example.com"  # Pre-fill
    )
    
    import webbrowser
    webbrowser.open(checkout_url)
```

### Stripe Tax Setup (Optional but Recommended):

```python
# Enable automatic tax calculation
session = stripe.checkout.Session.create(
    payment_method_types=["card"],
    line_items=[{...}],
    mode="payment",
    automatic_tax={"enabled": True},  # Calculates tax by location
    success_url=...,
    cancel_url=...
)
```

---

## Integration with Existing License Manager

Replace the `get_purchase_url()` method in your existing `license_manager.py`:

```python
# In license_manager.py

class LicenseManager:
    # ... existing code ...
    
    def get_purchase_url(self, tier: str = "pro") -> str:
        """Get purchase URL for license."""
        # Option 1: Paddle (simple)
        # return f"https://pay.paddle.com/checkout/{PRODUCT_ID}"
        
        # Option 2: Stripe (create checkout session)
        stripe_mgr = StripeLicenseManager()
        return stripe_mgr.create_checkout_session(tier, "")
    
    def activate_online_license(self, license_key: str) -> bool:
        """
        Optional: Verify license against your server.
        Prevents key sharing (one key = one active device).
        """
        # Call your API to check if license is valid
        # and register this device
        pass
```

---

## Recommended: Hybrid Approach

For fastest time-to-revenue with room to grow:

**Phase 1 (Now):** Paddle
- Zero tax headache
- Hosted checkout (no UI dev)
- Get revenue flowing

**Phase 2 (Later):** Migrate to Stripe
- Lower fees at scale
- More customization
- When you have an accountant for taxes

---

## Quick Start Checklist

### Paddle Route (~1 hour setup):
- [ ] Create Paddle account
- [ ] Add product ($49 Pro, $199 Enterprise)
- [ ] Copy webhook URL from your server
- [ ] Deploy webhook endpoint
- [ ] Update `get_purchase_url()` in license_manager.py
- [ ] Test with Paddle sandbox mode

### Stripe Route (~4 hour setup):
- [ ] Create Stripe account
- [ ] Create products + prices
- [ ] Build/checkout page (or use Stripe Checkout)
- [ ] Deploy webhook endpoint
- [ ] Set up Stripe Tax (or handle taxes yourself)
- [ ] Configure email delivery (SendGrid/AWS SES)
- [ ] Test with Stripe test keys

---

Both work. Paddle gets you selling faster. Stripe saves money at scale.
