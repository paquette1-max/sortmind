"""
3-Tier License Poller Monitor

Monitors Stripe poller results and escalates based on activity level.
Uses local models for efficiency, escalates to cloud only when needed.

Usage:
    # Check and report (run from cron)
    python poller_monitor.py --check
    
    # Force summary report
    python poller_monitor.py --report
    
    # Test escalation
    python poller_monitor.py --test-alert
"""
import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple

# State file
MONITOR_STATE_FILE = Path.home() / ".config" / "sortmind" / "monitor_state.json"
POLLER_STATE_FILE = Path.home() / ".config" / "sortmind" / "poller_state.json"

# Alert thresholds
ALERT_THRESHOLDS = {
    "sales_today": 1,        # Any sale today = notify
    "sales_week": 3,         # 3+ sales this week = escalation
    "errors_streak": 3,      # 3 failed polls in a row = alert
    "no_check_hours": 12,    # No check in 12 hours = warning
}


class PollerMonitor:
    """Monitors poller activity and manages alerts."""
    
    def __init__(self):
        self.state = self._load_state()
        self.poller_state = self._load_poller_state()
    
    def _load_state(self) -> Dict:
        """Load monitor state."""
        if not MONITOR_STATE_FILE.exists():
            return {
                "last_check": None,
                "last_alert": None,
                "alert_count": 0,
                "notified_sales": [],
                "error_streak": 0
            }
        
        try:
            with open(MONITOR_STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            return {
                "last_check": None,
                "last_alert": None,
                "alert_count": 0,
                "notified_sales": [],
                "error_streak": 0
            }
    
    def _load_poller_state(self) -> Dict:
        """Load poller state."""
        if not POLLER_STATE_FILE.exists():
            return {"processed_payments": [], "total_licenses_generated": 0}
        
        try:
            with open(POLLER_STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            return {"processed_payments": [], "total_licenses_generated": 0}
    
    def _save_state(self):
        """Save monitor state."""
        MONITOR_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(MONITOR_STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def _count_recent_sales(self, hours: int) -> int:
        """Count sales in the last N hours."""
        # For polling mode, we track via poller state
        # This is simplified - in webhook mode we'd have timestamps
        total = self.poller_state.get("total_licenses_generated", 0)
        
        # If we have notified_sales, calculate recent ones
        notified = self.state.get("notified_sales", [])
        cutoff = datetime.now() - timedelta(hours=hours)
        
        recent = 0
        for sale in notified:
            try:
                sale_time = datetime.fromisoformat(sale.get("time", "2000-01-01"))
                if sale_time > cutoff:
                    recent += 1
            except:
                pass
        
        return recent
    
    def check_status(self) -> Tuple[str, str, Dict]:
        """
        Check poller status and determine alert level.
        
        Returns:
            (tier, message, details)
            tier: "none", "tier1", "tier2", "tier3"
        """
        now = datetime.now()
        
        # Check 1: Recent sales today (Tier 1 - good news)
        sales_today = self._count_recent_sales(24)
        if sales_today > 0:
            return "tier1", f"🎉 {sales_today} sale(s) today!", {
                "type": "sale",
                "count": sales_today,
                "action": "notify"
            }
        
        # Check 2: Multiple sales this week (Tier 2 - business growing)
        sales_week = self._count_recent_sales(168)  # 7 days
        if sales_week >= ALERT_THRESHOLDS["sales_week"]:
            return "tier2", f"📈 {sales_week} sales this week - consider upgrading to webhooks!", {
                "type": "growth",
                "count": sales_week,
                "action": "escalate_consider_webhooks"
            }
        
        # Check 3: Poller hasn't run recently (Tier 2 - warning)
        last_check = self.state.get("last_check")
        if last_check:
            try:
                last = datetime.fromisoformat(last_check)
                hours_since = (now - last).total_seconds() / 3600
                
                if hours_since > ALERT_THRESHOLDS["no_check_hours"]:
                    return "tier2", f"⚠️ Poller hasn't run in {hours_since:.1f} hours", {
                        "type": "missed_check",
                        "hours": hours_since,
                        "action": "check_cron"
                    }
            except:
                pass
        
        # Check 4: Error streak (Tier 3 - urgent)
        error_streak = self.state.get("error_streak", 0)
        if error_streak >= ALERT_THRESHOLDS["errors_streak"]:
            return "tier3", f"🚨 {error_streak} consecutive poll failures - needs attention!", {
                "type": "errors",
                "streak": error_streak,
                "action": "urgent_fix"
            }
        
        # Nothing to report
        return "none", "No alerts - system healthy", {
            "type": "healthy",
            "sales_today": sales_today,
            "sales_week": sales_week
        }
    
    def run_check(self, dry_run: bool = False) -> str:
        """
        Run monitoring check and return formatted result.
        
        Args:
            dry_run: Don't actually send alerts
            
        Returns:
            Status message
        """
        tier, message, details = self.check_status()
        
        # Update state
        self.state["last_check"] = datetime.now().isoformat()
        
        if tier == "none":
            self._save_state()
            return "HEARTBEAT_OK"
        
        # Format alert based on tier
        timestamp = datetime.now().strftime("%H:%M")
        
        if tier == "tier1":
            # Good news - simple notification
            alert = f"[{timestamp}] {message}"
            if not dry_run:
                self._send_alert(alert, priority="low")
            
        elif tier == "tier2":
            # Worth escalating - moderate attention
            alert = f"[{timestamp}] {message}\nDetails: {json.dumps(details, indent=2)}"
            if not dry_run:
                self._send_alert(alert, priority="medium")
            
        elif tier == "tier3":
            # Urgent - needs immediate attention
            alert = f"[{timestamp}] 🚨 URGENT: {message}\nAction required: {details.get('action', 'unknown')}"
            if not dry_run:
                self._send_alert(alert, priority="high")
        
        self._save_state()
        return alert if dry_run else f"Alert sent: {tier}"
    
    def _send_alert(self, message: str, priority: str = "low"):
        """Send alert via configured channel."""
        # Log to file
        log_file = Path.home() / ".openclaw" / "logs" / "poller_alerts.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(log_file, 'a') as f:
            f.write(f"{datetime.now().isoformat()} [{priority.upper()}] {message}\n")
        
        # For high priority, could also send iMessage/email
        if priority == "high":
            # iMessage notification
            try:
                import subprocess
                subprocess.run([
                    "osascript", "-e",
                    f'display notification "{message[:100]}..." with title "File Organizer Alert"'
                ], check=False)
            except:
                pass
        
        print(message)
    
    def record_sale(self, charge_id: str, amount: int, email: str):
        """Record a sale for tracking."""
        sale_record = {
            "charge_id": charge_id,
            "amount": amount,
            "email": email[:5] + "***",  # Mask email for privacy
            "time": datetime.now().isoformat()
        }
        
        if "notified_sales" not in self.state:
            self.state["notified_sales"] = []
        
        self.state["notified_sales"].append(sale_record)
        
        # Keep only last 100 sales
        self.state["notified_sales"] = self.state["notified_sales"][-100:]
        
        self._save_state()
    
    def record_error(self):
        """Record a poller error."""
        self.state["error_streak"] = self.state.get("error_streak", 0) + 1
        self._save_state()
    
    def record_success(self):
        """Record a successful poll."""
        self.state["error_streak"] = 0
        self._save_state()
    
    def get_summary(self) -> str:
        """Get summary of recent activity."""
        total_licenses = self.poller_state.get("total_licenses_generated", 0)
        recent_sales = self._count_recent_sales(168)  # 7 days
        
        last_check = self.state.get("last_check", "Never")
        if last_check and last_check != "Never":
            try:
                last = datetime.fromisoformat(last_check)
                last_check = last.strftime("%Y-%m-%d %H:%M")
            except:
                pass
        
        summary = f"""
📊 File Organizer Payment Monitor Summary
═══════════════════════════════════════════

Total Licenses Generated: {total_licenses}
Sales This Week: {recent_sales}
Last Check: {last_check}

Current Mode: Polling (no 24/7 server required)
Escalation Threshold: {ALERT_THRESHOLDS['sales_week']} sales/week

Next Steps:
- When you hit {ALERT_THRESHOLDS['sales_week']}+ sales/week, switch to webhook mode
- Webhook mode = instant license delivery, no polling needed
- Run 'python poll_stripe.sh' manually or set up cron job

Status: {'🎉 Active sales!' if recent_sales > 0 else '⏳ Waiting for first sale'}
"""
        return summary


def main():
    parser = argparse.ArgumentParser(description="Monitor Stripe poller status")
    parser.add_argument("--check", action="store_true", help="Run status check")
    parser.add_argument("--report", action="store_true", help="Show summary report")
    parser.add_argument("--dry-run", action="store_true", help="Don't send alerts")
    parser.add_argument("--record-sale", nargs=3, metavar=("CHARGE", "AMOUNT", "EMAIL"),
                        help="Record a sale (for testing)")
    parser.add_argument("--record-error", action="store_true", help="Record an error")
    parser.add_argument("--record-success", action="store_true", help="Record success")
    
    args = parser.parse_args()
    
    monitor = PollerMonitor()
    
    if args.record_sale:
        monitor.record_sale(args.record_sale[0], int(args.record_sale[1]), args.record_sale[2])
        print(f"✅ Recorded sale: {args.record_sale[0]}")
        return
    
    if args.record_error:
        monitor.record_error()
        print("❌ Recorded error")
        return
    
    if args.record_success:
        monitor.record_success()
        print("✅ Recorded success")
        return
    
    if args.report:
        print(monitor.get_summary())
        return
    
    # Default: run check
    result = monitor.run_check(dry_run=args.dry_run)
    print(result)


if __name__ == "__main__":
    main()
