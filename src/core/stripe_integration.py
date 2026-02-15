"""
Stripe integration for SortMind Pro license management.

This module handles:
- Creating Stripe Checkout sessions
- Processing webhooks for payment events
- Generating and validating license keys
- Sending license emails to customers
"""
import os
import json
import secrets
import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass, asdict

# Stripe import with fallback
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    logging.warning("stripe package not installed. Run: pip install stripe")

logger = logging.getLogger(__name__)

# Configuration - Load from environment or config file
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")

# Product configuration
STRIPE_PRODUCTS = {
    "pro": {
        "price_id": os.getenv("STRIPE_PRO_PRICE_ID", ""),
        "amount": 4900,  # $49.00 in cents
        "name": "SortMind Pro",
        "description": "Unlimited AI analysis, batch processing, and custom patterns"
    },
    "enterprise": {
        "price_id": os.getenv("STRIPE_ENT_PRICE_ID", ""),
        "amount": 19900,  # $199.00 in cents
        "name": "SortMind Enterprise",
        "description": "Everything in Pro plus cloud sync and priority support"
    }
}


@dataclass
class LicenseInfo:
    """License information structure."""
    key: str
    tier: str  # "pro", "enterprise"
    email: str
    created_at: str
    expires_at: Optional[str] = None
    stripe_payment_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    activated_at: Optional[str] = None
    
    def is_valid(self) -> bool:
        """Check if license is still valid."""
        if self.expires_at is None:
            return True  # Perpetual license
        try:
            expiry = datetime.fromisoformat(self.expires_at)
            return datetime.now() < expiry
        except:
            return False


class StripeLicenseManager:
    """
    Manages Stripe checkout and license generation for SortMind.
    """
    
    def __init__(self, license_db_path: Optional[Path] = None):
        """
        Initialize the license manager.
        
        Args:
            license_db_path: Path to store license database
        """
        if not STRIPE_AVAILABLE:
            raise ImportError("stripe package required. Install with: pip install stripe")
        
        if not STRIPE_SECRET_KEY:
            raise ValueError("STRIPE_SECRET_KEY not set in environment")
        
        stripe.api_key = STRIPE_SECRET_KEY
        
        if license_db_path is None:
            license_db_path = Path.home() / ".config" / "sortmind"
        
        self.license_db_path = license_db_path
        self.license_db_path.mkdir(parents=True, exist_ok=True)
        
        self.license_db_file = self.license_db_path / "stripe_licenses.json"
        self._ensure_db()
        
        logger.info(f"StripeLicenseManager initialized. DB: {self.license_db_file}")
    
    def _ensure_db(self):
        """Ensure license database exists."""
        if not self.license_db_file.exists():
            self._save_db({"licenses": []})
    
    def _load_db(self) -> Dict:
        """Load license database."""
        try:
            with open(self.license_db_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load license DB: {e}")
            return {"licenses": []}
    
    def _save_db(self, data: Dict):
        """Save license database."""
        try:
            with open(self.license_db_file, 'w') as f:
                json.dump(data, f, indent=2)
            os.chmod(self.license_db_file, 0o600)
        except Exception as e:
            logger.error(f"Failed to save license DB: {e}")
    
    def create_checkout_session(self, tier: str, customer_email: str = "") -> Tuple[str, Optional[str]]:
        """
        Create a Stripe Checkout session for license purchase.
        
        Args:
            tier: "pro" or "enterprise"
            customer_email: Optional email to pre-fill
            
        Returns:
            (checkout_url, error_message)
        """
        if tier not in STRIPE_PRODUCTS:
            return None, f"Invalid tier: {tier}"
        
        product = STRIPE_PRODUCTS[tier]
        
        if not product["price_id"]:
            return None, f"Stripe price ID not configured for tier: {tier}"
        
        try:
            session_params = {
                "payment_method_types": ["card"],
                "line_items": [{
                    "price": product["price_id"],
                    "quantity": 1,
                }],
                "mode": "payment",
                "success_url": "https://sortmind.app/success?session_id={CHECKOUT_SESSION_ID}",
                "cancel_url": "https://sortmind.app/cancel",
                "metadata": {
                    "tier": tier,
                    "product": "file_organizer"
                }
            }
            
            # Add customer email if provided
            if customer_email:
                session_params["customer_email"] = customer_email
            
            session = stripe.checkout.Session.create(**session_params)
            
            logger.info(f"Created checkout session: {session.id} for tier: {tier}")
            return session.url, None
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating checkout: {e}")
            return None, str(e)
        except Exception as e:
            logger.error(f"Unexpected error creating checkout: {e}")
            return None, str(e)
    
    def handle_webhook(self, payload: bytes, signature: str) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        Process Stripe webhook events.
        
        Args:
            payload: Raw request body
            signature: Stripe-Signature header value
            
        Returns:
            (success, error_message, license_info)
        """
        if not STRIPE_WEBHOOK_SECRET:
            logger.error("STRIPE_WEBHOOK_SECRET not configured")
            return False, "Webhook secret not configured", None
        
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            logger.error(f"Invalid payload: {e}")
            return False, "Invalid payload", None
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {e}")
            return False, "Invalid signature", None
        
        event_type = event.get("type")
        logger.info(f"Received Stripe webhook: {event_type}")
        
        if event_type == "checkout.session.completed":
            return self._handle_checkout_completed(event["data"]["object"])
        
        elif event_type == "charge.refunded":
            return self._handle_refund(event["data"]["object"])
        
        # Acknowledge other events
        return True, None, None
    
    def _handle_checkout_completed(self, session: Dict) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """Handle successful checkout."""
        try:
            customer_email = session.get("customer_email") or session.get("customer_details", {}).get("email")
            tier = session.get("metadata", {}).get("tier", "pro")
            payment_intent = session.get("payment_intent")
            customer_id = session.get("customer")
            
            if not customer_email:
                logger.error("No customer email in session")
                return False, "No customer email", None
            
            # Generate license key
            license_key = self._generate_license_key(tier)
            
            # Create license record
            license_info = LicenseInfo(
                key=license_key,
                tier=tier,
                email=customer_email,
                created_at=datetime.now().isoformat(),
                stripe_payment_id=payment_intent,
                stripe_customer_id=customer_id
            )
            
            # Save to database
            self._save_license(license_info)
            
            # Send license email
            self._send_license_email(license_info)
            
            logger.info(f"License generated for {customer_email}: {license_key}")
            
            return True, None, asdict(license_info)
            
        except Exception as e:
            logger.error(f"Error processing checkout: {e}")
            return False, str(e), None
    
    def _handle_refund(self, charge: Dict) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """Handle refund - revoke license."""
        try:
            payment_intent = charge.get("payment_intent")
            
            # Find license by payment ID
            db = self._load_db()
            for i, lic in enumerate(db["licenses"]):
                if lic.get("stripe_payment_id") == payment_intent:
                    # Mark as refunded/revoked
                    db["licenses"][i]["refunded"] = True
                    db["licenses"][i]["refunded_at"] = datetime.now().isoformat()
                    self._save_db(db)
                    
                    logger.info(f"License revoked due to refund: {lic['key']}")
                    return True, None, lic
            
            return True, None, None
            
        except Exception as e:
            logger.error(f"Error processing refund: {e}")
            return False, str(e), None
    
    def _generate_license_key(self, tier: str) -> str:
        """
        Generate a unique license key.
        Format: PRO-XXXX-XXXX-XXXX or ENT-XXXX-XXXX-XXXX
        """
        prefix = "PRO" if tier == "pro" else "ENT"
        
        # Generate random sections
        sections = []
        for _ in range(3):
            # Use secrets for cryptographically secure random
            section = secrets.token_hex(4).upper()[:4]
            sections.append(section)
        
        key = f"{prefix}-{sections[0]}-{sections[1]}-{sections[2]}"
        
        # Check for collisions
        db = self._load_db()
        existing_keys = {lic["key"] for lic in db["licenses"]}
        
        if key in existing_keys:
            # Regenerate if collision
            return self._generate_license_key(tier)
        
        return key
    
    def _save_license(self, license_info: LicenseInfo):
        """Save license to database."""
        db = self._load_db()
        db["licenses"].append(asdict(license_info))
        self._save_db(db)
    
    def _send_license_email(self, license_info: LicenseInfo):
        """
        Send license email to customer.
        Uses configured email provider (SMTP, SendGrid, etc.)
        """
        # This will be implemented in email_sender.py
        from .email_sender import send_license_email
        
        try:
            send_license_email(license_info)
        except Exception as e:
            logger.error(f"Failed to send license email: {e}")
    
    def validate_license_key(self, key: str) -> Tuple[bool, Optional[LicenseInfo]]:
        """
        Validate a license key.
        
        Args:
            key: License key to validate
            
        Returns:
            (is_valid, license_info)
        """
        if not key or len(key) < 10:
            return False, None
        
        db = self._load_db()
        
        for lic_data in db["licenses"]:
            if lic_data["key"] == key:
                license_info = LicenseInfo(**lic_data)
                
                # Check if refunded
                if lic_data.get("refunded"):
                    logger.warning(f"License {key} was refunded")
                    return False, None
                
                # Check validity
                if license_info.is_valid():
                    # Update activation time if first use
                    if not license_info.activated_at:
                        license_info.activated_at = datetime.now().isoformat()
                        self._update_license(license_info)
                    
                    return True, license_info
                else:
                    logger.warning(f"License {key} expired")
                    return False, None
        
        return False, None
    
    def _update_license(self, license_info: LicenseInfo):
        """Update existing license in database."""
        db = self._load_db()
        for i, lic in enumerate(db["licenses"]):
            if lic["key"] == license_info.key:
                db["licenses"][i] = asdict(license_info)
                self._save_db(db)
                return
    
    def get_license_by_email(self, email: str) -> Optional[LicenseInfo]:
        """Find license by email address."""
        db = self._load_db()
        
        for lic_data in db["licenses"]:
            if lic_data["email"].lower() == email.lower():
                return LicenseInfo(**lic_data)
        
        return None
    
    def revoke_license(self, key: str) -> bool:
        """Revoke a license (for refunds or fraud)."""
        db = self._load_db()
        
        for i, lic in enumerate(db["licenses"]):
            if lic["key"] == key:
                db["licenses"][i]["revoked"] = True
                db["licenses"][i]["revoked_at"] = datetime.now().isoformat()
                self._save_db(db)
                logger.info(f"License revoked: {key}")
                return True
        
        return False


# Singleton instance
_stripe_manager: Optional[StripeLicenseManager] = None


def get_stripe_manager() -> StripeLicenseManager:
    """Get or create the global Stripe license manager."""
    global _stripe_manager
    if _stripe_manager is None:
        _stripe_manager = StripeLicenseManager()
    return _stripe_manager


# Convenience functions for use in other modules
def create_checkout_url(tier: str, email: str = "") -> Tuple[str, Optional[str]]:
    """Create a checkout URL for the given tier."""
    manager = get_stripe_manager()
    return manager.create_checkout_session(tier, email)


def validate_license(key: str) -> Tuple[bool, Optional[Dict]]:
    """Validate a license key."""
    manager = get_stripe_manager()
    is_valid, license_info = manager.validate_license_key(key)
    if is_valid and license_info:
        return True, asdict(license_info)
    return False, None
