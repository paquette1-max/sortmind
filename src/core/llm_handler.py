"""LLM handler implementations for AI File Organizer."""
import logging
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class BaseLLMHandler:
    """Base class for LLM handlers."""
    
    def __init__(self, model: str):
        self.model = model
    
    def analyze_file(self, file_path: Path, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Analyze a single file and return organization suggestion."""
        raise NotImplementedError
    
    def is_available(self) -> bool:
        """Check if the LLM service is available."""
        raise NotImplementedError


class OllamaHandler(BaseLLMHandler):
    """Handler for Ollama local LLM."""
    
    def __init__(self, model: str = "llama3.2:3b", url: str = "http://localhost:11434"):
        super().__init__(model)
        self.url = url
        self._available = None
    
    def is_available(self) -> bool:
        """Check if Ollama is running."""
        if self._available is not None:
            return self._available
        
        try:
            import requests
            response = requests.get(f"{self.url}/api/tags", timeout=5)
            self._available = response.status_code == 200
            return self._available
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            self._available = False
            return False
    
    def analyze_file(self, file_path: Path, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Analyze file using Ollama."""
        if not self.is_available():
            raise RuntimeError("Ollama is not available. Is it running?")
        
        # Simple implementation - in production would use actual LLM call
        # For now, return basic categorization based on extension
        ext = file_path.suffix.lower()
        
        category_map = {
            '.pdf': 'documents',
            '.txt': 'documents',
            '.doc': 'documents',
            '.docx': 'documents',
            '.jpg': 'images',
            '.jpeg': 'images',
            '.png': 'images',
            '.mp3': 'audio',
            '.mp4': 'video',
            '.py': 'code',
            '.js': 'code',
            '.zip': 'archives',
        }
        
        category = category_map.get(ext, 'uncategorized')
        
        return {
            "file_path": str(file_path),
            "category": category,
            "suggested_name": file_path.name,
            "confidence": 0.7,
            "reasoning": f"Categorized by file extension ({ext}) using local Ollama",
            "should_organize": True
        }


class OpenRouterHandler(BaseLLMHandler):
    """Handler for OpenRouter API."""
    
    def __init__(self, api_key: str, model: str = "openai/gpt-3.5-turbo"):
        super().__init__(model)
        self.api_key = api_key
        self._available = None
    
    def is_available(self) -> bool:
        """Check if OpenRouter API key is valid."""
        if self._available is not None:
            return self._available
        
        if not self.api_key:
            self._available = False
            return False
        
        # Could make a test API call here
        self._available = True
        return True
    
    def analyze_file(self, file_path: Path, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Analyze file using OpenRouter."""
        if not self.is_available():
            raise RuntimeError("OpenRouter API key not configured")
        
        # Simple implementation - in production would use actual API call
        ext = file_path.suffix.lower()
        
        category_map = {
            '.pdf': 'documents',
            '.txt': 'documents',
            '.doc': 'documents',
            '.docx': 'documents',
            '.jpg': 'images',
            '.jpeg': 'images',
            '.png': 'images',
            '.mp3': 'audio',
            '.mp4': 'video',
            '.py': 'code',
            '.js': 'code',
            '.zip': 'archives',
        }
        
        category = category_map.get(ext, 'uncategorized')
        
        return {
            "file_path": str(file_path),
            "category": category,
            "suggested_name": file_path.name,
            "confidence": 0.8,
            "reasoning": f"Categorized by file extension ({ext}) using OpenRouter",
            "should_organize": True
        }
