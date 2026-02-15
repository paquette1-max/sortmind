"""
Stripe Polling-based License Generator

This script polls the Stripe API for new successful payments and 
automatically generates/sends license keys. Designed to run periodically
via cron or manually.

Usage:
    # Check once (manual run)
    python stripe_poller.py
    
    # Check with dry-run (don't send emails)
    python stripe_poller.py --dry-run
    
    # Check last N hours
    python stripe_poller.py --hours 24

This avoids needing a 24/7 webhook server. Run it every hour via cron,
or just run it manually when you remember.
"""
import os
import sys
import json
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    import stripe
except ImportError:
    print("❌ stripe package not installed. Run: pip install stripe")
    sys.exit(1)

from stripe_integration import (
    StripeLicenseManager, LicenseInfo, 
    STRIPE_SECRET_KEY, STRIPE_PRODUCTS
)
from email_sender import send_license_email

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# State file to track processed payments
STATE_FILE = Path.home() / ".config" / "sortmind" / "poller_state.json"


class StripePoller:
    """Polls Stripe for new payments and generates licenses."""
    
    def __init__(self, dry_run: bool = False):
        """
        Initialize poller.
        
        Args:
            dry_run: If True, don't actually send emails
        """
        if not STRIPE_SECRET_KEY:
            raise ValueError("STRIPE_SECRET_KEY not set")
        
        stripe.api_key = STRIPE_SECRET_KEY
        self.dry_run = dry_run
        self.license_manager = StripeLicenseManager()
        self.state = self._load_state()
    
    def _load_state(self) -> Dict:
        """Load poller state (last check time, processed payments)."""
        if not STATE_FILE.exists():
            return {
                "last_check": None,
                "processed_payments": [],
                "total_licenses_generated": 0
            }
        
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            return {"last_check": None, "processed_payments": [], "total_licenses_generated": 0}
    
    def _save_state(self):
        """Save poller state."""
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(STATE_FILE, 'w') as f:
                json.dump(self.state, f, indent=2)
            os.chmod(STATE_FILE, 0o600)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def poll_new_payments(self, hours: int = 24) -> List[Dict]:
        """
        Poll Stripe for new successful payments in the last N hours.
        
        Args:
            hours: How far back to check
            
        Returns:
            List of payment objects needing license generation
        """
        # Calculate time range
        since = datetime.now() - timedelta(hours=hours)
        since_timestamp = int(since.timestamp())
        
        logger.info(f"Checking for payments since {since.isoformat()}")
        
        try:
            # Get successful charges
            charges = stripe.Charge.list(
                created={"gte": since_timestamp},
                limit=100
            )
            
            new_payments = []
            processed = set(self.state.get("processed_payments", []))
            
            for charge in charges.auto_paging_iter():
                charge_id = charge.id
                
                # Skip already processed
                if charge_id in processed:
                    continue
                
                # Skip refunded charges
                if charge.refunded:
                    logger.info(f"Skipping refunded charge: {charge_id}")
                    self._mark_processed(charge_id)
                    continue
                
                # Get customer email
                customer_email = self._get_customer_email(charge)
                if not customer_email:
                    logger.warning(f"No email for charge {charge_id}, skipping")
                    continue
                
                # Determine tier from amount
                tier = self._get_tier_from_amount(charge.amount)
                
                payment_info = {
                    "charge_id": charge_id,
                    "payment_intent": charge.payment_intent,
                    "customer_email": customer_email,
                    "customer_id": charge.customer,
                    "amount": charge.amount,
                    "tier": tier,
                    "created": datetime.fromtimestamp(charge.created).isoformat()
                }
                
                new_payments.append(payment_info)
            
            logger.info(f"Found {len(new_payments)} new payments")
            return new_payments
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error polling: {e}")
            return []
    
    def _get_customer_email(self, charge) -> Optional[str]:
        """Extract customer email from charge."""
        # Try billing details first
        if charge.billing_details and charge.billing_details.email:
            return charge.billing_details.email
        
        # Try customer object
        if charge.customer:
            try:
                customer = stripe.Customer.retrieve(charge.customer)
                return customer.email
            except:
                pass
        
        return None
    
    def _get_tier_from_amount(self, amount_cents: int) -> str:
        """Determine tier from payment amount."""
        # Check against configured prices
        pro_price = STRIPE_PRODUCTS.get("pro", {}).get("amount", 4900)
        ent_price = STRIPE_PRODUCTS.get("enterprise", {}).get("amount", 19900)
        
        # Allow some variance (coupons, etc.)
        if abs(amount_cents - ent_price) < 5000:
            return "enterprise"
        elif abs(amount_cents - pro_price) < 2000:
            return "pro"
        
        # Default to pro if unclear
        logger.warning(f"Unclear tier for amount {amount_cents}, defaulting to pro")
        return "pro"
    
    def generate_and_send_license(self, payment: Dict) -> Tuple[bool, Optional[str]]:
        """
        Generate license key and send email for a payment.
        
        Args:
            payment: Payment info dict from poll_new_payments
            
        Returns:
            (success, license_key)
        """
        charge_id = payment["charge_id"]
        email = payment["customer_email"]
        tier = payment["tier"]
        
        try:
            # Generate license key
            license_key = self._generate_license_key(tier)
            
            # Create license record
            license_info = LicenseInfo(
                key=license_key,
                tier=tier,
                email=email,
                created_at=datetime.now().isoformat(),
                stripe_payment_id=payment["payment_intent"],
                stripe_customer_id=payment["customer_id"]
            )
            
            # Save to database
            self._save_license(license_info)
            
            if self.dry_run:
                logger.info(f"[DRY RUN] Would send license {license_key} to {email}")
                return True, license_key
            
            # Send email
            send_license_email(license_info)
            
            logger.info(f"✅ License sent: {license_key} to {email}")
            
            # Mark as processed
            self._mark_processed(charge_id)
            
            return True, license_key
            
        except Exception as e:
            logger.error(f"Failed to generate/send license for {charge_id}: {e}")
            return False, None
    
    def _generate_license_key(self, tier: str) -> str:
        """Generate unique license key."""
        import secrets
        
        prefix = "PRO" if tier == "pro" else "ENT"
        sections = [secrets.token_hex(4).upper()[:4] for _ in range(3)]
        return f"{prefix}-{sections[0]}-{sections[1]}-{sections[2]}"
    
    def _save_license(self, license_info: LicenseInfo):
        """Save license to database."""
        # Load existing
        db_file = self.license_manager.license_db_file
        
        if db_file.exists():
            with open(db_file, 'r') as f:
                db = json.load(f)
        else:
            db = {"licenses": []}
        
        # Add new license
        from dataclasses import asdict
        db["licenses"].append(asdict(license_info))
        
        # Save
        with open(db_file, 'w') as f:
            json.dump(db, f, indent=2)
    
    def _mark_processed(self, charge_id: str):
        """Mark a charge as processed."""
        if charge_id not in self.state["processed_payments"]:
            self.state["processed_payments"].append(charge_id)
            self.state["last_check"] = datetime.now().isoformat()
            self._save_state()
    
    def run(self, hours: int = 24) -> Dict:
        """
        Run the full poll-and-process cycle.
        
        Args:
            hours: How far back to check for payments
            
        Returns:
            Summary of results
        """
        results = {
            "checked_at": datetime.now().isoformat(),
            "hours_checked": hours,
            "new_payments_found": 0,
            "licenses_generated": 0,
            "errors": 0,
            "dry_run": self.dry_run,
            "details": []
        }
        
        # Poll for new payments
        payments = self.poll_new_payments(hours)
        results["new_payments_found"] = len(payments)
        
        # Process each payment
        for payment in payments:
            success, license_key = self.generate_and_send_license(payment)
            
            detail = {
                "charge_id": payment["charge_id"],
                "email": payment["customer_email"],
                "tier": payment["tier"],
                "amount": payment["amount"],
                "success": success,
                "license_key": license_key
            }
            results["details"].append(detail)
            
            if success:
                results["licenses_generated"] += 1
            else:
                results["errors"] += 1
        
        # Update stats
        if results["licenses_generated"] > 0:
            self.state["total_licenses_generated"] = self.state.get("total_licenses_generated", 0) + results["licenses_generated"]
            self._save_state()
        
        return results
    
    def print_summary(self, results: Dict):
        """Print human-readable summary."""
        print("\n" + "="*60)
        print("Stripe License Poller - Summary")
        print("="*60)
        print(f"Checked: {results['checked_at']}")
        print(f"Time range: Last {results['hours_checked']} hours")
        print(f"Dry run: {results['dry_run']}")
        print(f"\nNew payments found: {results['new_payments_found']}")
        print(f"Licenses generated: {results['licenses_generated']}")
        print(f"Errors: {results['errors']}")
        
        if results['details']:
            print("\nDetails:")
            for detail in results['details']:
                status = "✅" if detail['success'] else "❌"
                tier = detail['tier'].upper()
                amount = f"${detail['amount']/100:.2f}"
                print(f"  {status} {detail['email']} - {tier} ({amount})")
                if detail['license_key']:
                    print(f"     Key: {detail['license_key']}")
        
        total_generated = self.state.get("total_licenses_generated", 0)
        print(f"\nTotal licenses generated (all time): {total_generated}")
        print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Poll Stripe for new payments and generate licenses"
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="How many hours back to check (default: 24)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without sending emails"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Minimal output"
    )
    
    args = parser.parse_args()
    
    try:
        poller = StripePoller(dry_run=args.dry_run)
        results = poller.run(hours=args.hours)
        
        if not args.quiet:
            poller.print_summary(results)
        else:
            if results['licenses_generated'] > 0:
                print(f"Generated {results['licenses_generated']} licenses")
            else:
                print("No new payments")
        
        # Exit with error code if there were errors
        sys.exit(0 if results['errors'] == 0 else 1)
        
    except Exception as e:
        logger.error(f"Poller failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
