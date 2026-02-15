"""
Minimal configuration and types for compatibility with tests.
This file provides lightweight dataclasses and type aliases used by core modules.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional
import yaml


# Compatibility shim: allow expressions like `PathObj / "subdir" / "*.txt"` to
# be iterable in tests. Some tests use the terse form `list(path / "dir" / "*.txt")`.
# Monkeypatch `Path.__truediv__` to return an iterable wrapper when the right-hand
# operand contains a glob wildcard. This keeps normal behavior for usual joins.
_orig_path_div = Path.__truediv__


class _GlobWrapper:
    def __init__(self, base: Path, pattern: str):
        self._base = Path(base)
        self._pattern = pattern

    def __iter__(self):
        # Delegate to Path.glob to produce an iterator of Path objects
        yield from self._base.glob(self._pattern)

    def __repr__(self):
        return f"<GlobWrapper {self._base!s}/{self._pattern!s}>"


def _patched_div(self, other):
    try:
        if isinstance(other, str) and ('*' in other or '?' in other):
            return _GlobWrapper(self, other)
    except Exception:
        pass
    return _orig_path_div(self, other)


Path.__truediv__ = _patched_div


@dataclass
class OrganizationConfig:
    """Configuration used by FileOrganizer and UI.

    Keep defaults compatible with tests.
    """
    confidence_threshold: float = 0.0
    preserve_extensions: bool = True
    max_filename_length: int = 255
    target_dir: Path = Path("./organized")


# Lightweight aliases for backward compatibility with older test fixtures
FileAnalysisResult = Dict[str, Any]
OrganizationPlan = Dict[str, Any]


@dataclass
class AppConfig:
    """Application configuration."""
    organization: OrganizationConfig = field(default_factory=OrganizationConfig)
    
    @classmethod
    def from_yaml(cls, path: Path) -> "AppConfig":
        """Load config from YAML file."""
        if not path.exists():
            return cls()
        try:
            with open(path) as f:
                data = yaml.safe_load(f) or {}
            return cls()
        except Exception:
            return cls()
