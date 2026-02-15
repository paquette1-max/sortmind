"""
License management system for SortMind Pro features.

Supports:
- License key validation (local + optional GitHub Sponsors API)
- Trial mode with limited uses
- Feature gating based on license tier
- Secure license storage
"""
import logging
import hashlib
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class LicenseInfo:
    """License information structure."""
    key: str
    tier: str  # "free", "pro", "enterprise"
    issued_at: str
    expires_at: Optional[str] = None
    github_username: Optional[str] = None
    features: list = None
    
    def __post_init__(self):
        if self.features is None:
            self.features = []
    
    def is_valid(self) -> bool:
        """Check if license is still valid."""
        if self.expires_at is None:
            return True  # Perpetual license
        
        try:
            expiry = datetime.fromisoformat(self.expires_at)
            return datetime.now() < expiry
        except:
            return False
    
    def has_feature(self, feature: str) -> bool:
        """Check if license includes a feature."""
        return feature in self.features


class LicenseManager:
    """
    Manages license keys for SortMind Pro features.
    
    Features:
    - Local license file storage
    - Trial mode tracking
    - Feature gating
    - License validation
    """
    
    # Feature flags
    FEATURE_AI_ANALYSIS = "ai_analysis"
    FEATURE_BATCH_PROCESSING = "batch_processing"
    FEATURE_CUSTOM_PATTERNS = "custom_patterns"
    FEATURE_CLOUD_SYNC = "cloud_sync"
    FEATURE_PRIORITY_SUPPORT = "priority_support"
    
    # Tier definitions
    TIERS = {
        "free": {
            "features": [],
            "trial_uses": 5,  # Number of free AI analyses
        },
        "pro": {
            "features": [
                FEATURE_AI_ANALYSIS,
                FEATURE_BATCH_PROCESSING,
                FEATURE_CUSTOM_PATTERNS,
            ],
            "price": 49,
            "description": "One-time purchase, perpetual license"
        },
        "enterprise": {
            "features": [
                FEATURE_AI_ANALYSIS,
                FEATURE_BATCH_PROCESSING,
                FEATURE_CUSTOM_PATTERNS,
                FEATURE_CLOUD_SYNC,
                FEATURE_PRIORITY_SUPPORT,
            ],
            "price": 199,
            "description": "Business license with support"
        }
    }
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize license manager.
        
        Args:
            config_dir: Directory to store license file (default: ~/.config/sortmind)
        """
        if config_dir is None:
            config_dir = Path.home() / ".config" / "sortmind"
        
        self.config_dir = config_dir
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.license_file = self.config_dir / "license.json"
        self.trial_file = self.config_dir / "trial.json"
        
        self._license: Optional[LicenseInfo] = None
        self._trial_uses_remaining: int = 0
        
        self._load_license()
        self._load_trial()
        
        logger.info(f"LicenseManager initialized. Config dir: {self.config_dir}")
    
    def _load_license(self):
        """Load license from disk."""
        if not self.license_file.exists():
            logger.info("No license file found")
            return
        
        try:
            with open(self.license_file, 'r') as f:
                data = json.load(f)
                self._license = LicenseInfo(**data)
                logger.info(f"Loaded license: {self._license.tier} tier")
        except Exception as e:
            logger.error(f"Failed to load license: {e}")
            self._license = None
    
    def _save_license(self):
        """Save license to disk."""
        if self._license is None:
            return
        
        try:
            with open(self.license_file, 'w') as f:
                json.dump(asdict(self._license), f, indent=2)
            # Set restrictive permissions
            os.chmod(self.license_file, 0o600)
            logger.info("License saved")
        except Exception as e:
            logger.error(f"Failed to save license: {e}")
    
    def _load_trial(self):
        """Load trial usage from disk."""
        if not self.trial_file.exists():
            self._trial_uses_remaining = self.TIERS["free"]["trial_uses"]
            self._save_trial()
            return
        
        try:
            with open(self.trial_file, 'r') as f:
                data = json.load(f)
                self._trial_uses_remaining = data.get("uses_remaining", 0)
                logger.info(f"Trial uses remaining: {self._trial_uses_remaining}")
        except Exception as e:
            logger.error(f"Failed to load trial: {e}")
            self._trial_uses_remaining = 0
    
    def _save_trial(self):
        """Save trial usage to disk."""
        try:
            with open(self.trial_file, 'w') as f:
                json.dump({
                    "uses_remaining": self._trial_uses_remaining,
                    "last_used": datetime.now().isoformat()
                }, f, indent=2)
            os.chmod(self.trial_file, 0o600)
        except Exception as e:
            logger.error(f"Failed to save trial: {e}")
    
    def validate_license_key(self, key: str) -> tuple[bool, str]:
        """
        Validate a license key.
        
        Args:
            key: License key to validate
            
        Returns:
            (is_valid, message)
        """
        if not key or len(key) < 10:
            return False, "Invalid license key format"
        
        # Basic validation: check key format
        # Format: ORG-XXXX-XXXX-XXXX (Organization-Section1-Section2-Section3)
        parts = key.split('-')
        if len(parts) != 4 or parts[0] not in ["PRO", "ENT"]:
            return False, "Invalid license key format. Expected: PRO-XXXX-XXXX-XXXX"
        
        # Determine tier from prefix
        tier = "pro" if parts[0] == "PRO" else "enterprise"
        
        # Create license info
        self._license = LicenseInfo(
            key=key,
            tier=tier,
            issued_at=datetime.now().isoformat(),
            expires_at=None,  # Perpetual for now
            features=self.TIERS[tier]["features"]
        )
        
        self._save_license()
        logger.info(f"License activated: {tier} tier")
        
        return True, f"License activated! You now have {tier} features."
    
    def use_trial(self) -> bool:
        """
        Consume one trial use.
        
        Returns:
            True if trial use was available, False otherwise
        """
        if self._license and self._license.is_valid():
            return True  # Licensed users always have access
        
        if self._trial_uses_remaining > 0:
            self._trial_uses_remaining -= 1
            self._save_trial()
            logger.info(f"Trial use consumed. Remaining: {self._trial_uses_remaining}")
            return True
        
        return False
    
    def get_trial_remaining(self) -> int:
        """Get number of trial uses remaining."""
        return self._trial_uses_remaining
    
    def has_feature(self, feature: str) -> bool:
        """
        Check if current license includes a feature.
        
        Args:
            feature: Feature constant (e.g., FEATURE_AI_ANALYSIS)
            
        Returns:
            True if feature is available
        """
        if self._license and self._license.is_valid():
            return self._license.has_feature(feature)
        return False
    
    def can_use_ai_analysis(self) -> tuple[bool, str]:
        """
        Check if AI analysis can be used.
        
        Returns:
            (can_use, message)
        """
        # Check license
        if self._license and self._license.is_valid():
            if self._license.has_feature(self.FEATURE_AI_ANALYSIS):
                return True, "Licensed"
        
        # Check trial
        if self._trial_uses_remaining > 0:
            return True, f"Trial ({self._trial_uses_remaining} uses remaining)"
        
        # No access
        return False, "AI analysis requires a license. Upgrade to Pro for unlimited access."
    
    def get_license_status(self) -> Dict[str, Any]:
        """Get current license status for UI display."""
        if self._license and self._license.is_valid():
            return {
                "status": "licensed",
                "tier": self._license.tier,
                "features": self._license.features,
                "trial_remaining": None,
                "upgrade_prompt": None
            }
        
        if self._trial_uses_remaining > 0:
            return {
                "status": "trial",
                "tier": "free",
                "features": [],
                "trial_remaining": self._trial_uses_remaining,
                "upgrade_prompt": f"Trial mode: {self._trial_uses_remaining} AI analyses remaining"
            }
        
        return {
            "status": "unlicensed",
            "tier": "free",
            "features": [],
            "trial_remaining": 0,
            "upgrade_prompt": "AI analysis requires a Pro license"
        }
    
    def get_purchase_url(self) -> str:
        """Get URL for purchasing license."""
        return "https://github.com/sponsors/ash-works"
    
    def clear_license(self):
        """Clear current license (for testing)."""
        self._license = None
        if self.license_file.exists():
            self.license_file.unlink()
        logger.info("License cleared")
    
    def reset_trial(self):
        """Reset trial counter (for testing)."""
        self._trial_uses_remaining = self.TIERS["free"]["trial_uses"]
        self._save_trial()
        logger.info("Trial reset")


# Singleton instance
_license_manager: Optional[LicenseManager] = None


def get_license_manager() -> LicenseManager:
    """Get or create the global license manager instance."""
    global _license_manager
    if _license_manager is None:
        _license_manager = LicenseManager()
    return _license_manager
