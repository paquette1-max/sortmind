from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict


@dataclass
class ScannedFile:
    """Lightweight representation of a scanned file used by tests.

    This minimal implementation satisfies imports in tests and other
    modules during development. The full `FileScanner` from Phase 1
    can replace this later.
    """
    path: Path
    name: str
    size: int = 0
    mtime: float = 0.0
    metadata: Optional[Dict] = None


class FileScanner:
    """Minimal placeholder scanner with a simple API for tests.

    The real scanner in Phase 1 provides robust traversal and parsing.
    """

    def __init__(self, config=None):
        self.config = config

    def scan(self, directory: Path):
        results = []
        for p in Path(directory).rglob('*'):
            if p.is_file():
                results.append(ScannedFile(path=p, name=p.name, size=p.stat().st_size))
        return results
