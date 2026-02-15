"""LLM Configuration dialog for first-run setup."""
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QLineEdit, QMessageBox, QGroupBox, QRadioButton
)
from PyQt6.QtCore import Qt

import logging

logger = logging.getLogger(__name__)


class LLMConfigDialog(QDialog):
    """Dialog for configuring LLM backend on first run."""
    
    def __init__(self, parent=None, first_run=True):
        super().__init__(parent)
        self.first_run = first_run
        self.selected_backend = None
        self.config_data = {}
        
        self.setWindowTitle("SortMind - LLM Setup")
        self.setMinimumWidth(500)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Header
        if self.first_run:
            header = QLabel("Welcome to SortMind!")
            header.setStyleSheet("font-size: 18px; font-weight: bold;")
            layout.addWidget(header)
            
            info = QLabel("To use AI-powered file organization, you need to configure a language model.\n"
                         "Choose one of the options below:")
            info.setWordWrap(True)
            layout.addWidget(info)
        else:
            header = QLabel("LLM Configuration")
            header.setStyleSheet("font-size: 18px; font-weight: bold;")
            layout.addWidget(header)
        
        # Option 1: Ollama (Local)
        ollama_group = QGroupBox("Option 1: Ollama (Recommended - Local)")
        ollama_layout = QVBoxLayout(ollama_group)
        
        ollama_info = QLabel("Run AI locally with Ollama. Free and private.")
        ollama_info.setWordWrap(True)
        ollama_layout.addWidget(ollama_info)
        
        self.ollama_btn = QPushButton("Use Ollama (Local)")
        self.ollama_btn.clicked.connect(self._select_ollama)
        ollama_layout.addWidget(self.ollama_btn)
        
        layout.addWidget(ollama_group)
        
        # Option 2: OpenRouter (API)
        openrouter_group = QGroupBox("Option 2: OpenRouter (API Key)")
        openrouter_layout = QVBoxLayout(openrouter_group)
        
        openrouter_info = QLabel("Use cloud LLMs via OpenRouter. Requires API key.")
        openrouter_info.setWordWrap(True)
        openrouter_layout.addWidget(openrouter_info)
        
        api_layout = QHBoxLayout()
        api_layout.addWidget(QLabel("API Key:"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter your OpenRouter API key")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        api_layout.addWidget(self.api_key_input)
        
        self.openrouter_btn = QPushButton("Use OpenRouter")
        self.openrouter_btn.clicked.connect(self._select_openrouter)
        
        openrouter_layout.addLayout(api_layout)
        openrouter_layout.addWidget(self.openrouter_btn)
        
        layout.addWidget(openrouter_group)
        
        # Option 3: Demo Mode (No LLM)
        demo_group = QGroupBox("Option 3: Demo Mode (No AI)")
        demo_layout = QVBoxLayout(demo_group)
        
        demo_info = QLabel("Use rule-based organization only. No AI features.")
        demo_info.setWordWrap(True)
        demo_layout.addWidget(demo_info)
        
        self.demo_btn = QPushButton("Use Demo Mode")
        self.demo_btn.clicked.connect(self._select_demo)
        demo_layout.addWidget(self.demo_btn)
        
        layout.addWidget(demo_group)
        
        # Help text
        help_text = QLabel("<a href='https://github.com/ollama/ollama'>Download Ollama</a> | "
                         "<a href='https://openrouter.ai/keys'>Get OpenRouter Key</a>")
        help_text.setOpenExternalLinks(True)
        help_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(help_text)
        
        # Cancel button (only if not first run)
        if not self.first_run:
            cancel_btn = QPushButton("Cancel")
            cancel_btn.clicked.connect(self.reject)
            layout.addWidget(cancel_btn)
        
        layout.addStretch()
    
    def _select_ollama(self):
        """Select Ollama backend."""
        self.selected_backend = "ollama"
        self.config_data = {
            "backend": "ollama",
            "model": "llama3.2:3b",
            "url": "http://localhost:11434"
        }
        self.accept()
    
    def _select_openrouter(self):
        """Select OpenRouter backend."""
        api_key = self.api_key_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "API Key Required", 
                              "Please enter your OpenRouter API key.")
            return
        
        self.selected_backend = "openrouter"
        self.config_data = {
            "backend": "openrouter",
            "api_key": api_key,
            "model": "openai/gpt-3.5-turbo"
        }
        self.accept()
    
    def _select_demo(self):
        """Select demo mode (no LLM)."""
        self.selected_backend = "demo"
        self.config_data = {
            "backend": "demo",
            "enabled": False
        }
        self.accept()
    
    @staticmethod
    def check_llm_config(config_path: Path) -> bool:
        """Check if LLM is configured."""
        # Check for config file or environment variables
        import os
        if os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY"):
            return True
        if config_path.exists():
            try:
                import yaml
                with open(config_path) as f:
                    cfg = yaml.safe_load(f)
                return cfg.get("llm", {}).get("backend") is not None
            except Exception:
                pass
        return False
    
    @staticmethod
    def prompt_for_config(parent=None, config_path: Path = None) -> dict:
        """Show config dialog and return selected config."""
        first_run = config_path is None or not LLMConfigDialog.check_llm_config(config_path)
        dialog = LLMConfigDialog(parent, first_run=first_run)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.config_data
        return None
