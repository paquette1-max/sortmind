"""
Core module - Core application components.
"""

from .preview import PreviewManager, FilePreview, PreviewType
from .rules_engine import RulesEngine, OrganizationRule, RuleType, RuleOperator, RuleMatch
from .duplicate_detector import DuplicateDetector, DuplicateGroup, DuplicateType, DuplicateDetectionResult
from .config import OrganizationConfig, AppConfig
from .logging_config import setup_logging
from .llm_handler import BaseLLMHandler, OllamaHandler, OpenRouterHandler

# Stripe integration (optional - only if configured)
try:
    from .stripe_integration import (
        StripeLicenseManager, LicenseInfo,
        create_checkout_url, validate_license,
        get_stripe_manager
    )
    from .email_sender import send_license_email
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False

__all__ = [
    "PreviewManager", "FilePreview", "PreviewType",
    "RulesEngine", "OrganizationRule", "RuleType", "RuleOperator", "RuleMatch",
    "DuplicateDetector", "DuplicateGroup", "DuplicateType", "DuplicateDetectionResult",
    "OrganizationConfig", "AppConfig", "setup_logging",
    "BaseLLMHandler", "OllamaHandler", "OpenRouterHandler"
]

# Add Stripe exports if available
if STRIPE_AVAILABLE:
    __all__.extend([
        "StripeLicenseManager", "LicenseInfo",
        "create_checkout_url", "validate_license",
        "get_stripe_manager", "send_license_email"
    ])
