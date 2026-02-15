"""
Core module - Core application components.
"""

from .preview import PreviewManager, FilePreview, PreviewType
from .rules_engine import RulesEngine, OrganizationRule, RuleType, RuleOperator, RuleMatch
from .duplicate_detector import DuplicateDetector, DuplicateGroup, DuplicateType, DuplicateDetectionResult
from .config import OrganizationConfig, AppConfig
from .logging_config import setup_logging
from .llm_handler import BaseLLMHandler, OllamaHandler, OpenRouterHandler

__all__ = [
    "PreviewManager", "FilePreview", "PreviewType",
    "RulesEngine", "OrganizationRule", "RuleType", "RuleOperator", "RuleMatch",
    "DuplicateDetector", "DuplicateGroup", "DuplicateType", "DuplicateDetectionResult",
    "OrganizationConfig", "AppConfig", "setup_logging",
    "BaseLLMHandler", "OllamaHandler", "OpenRouterHandler"
]
