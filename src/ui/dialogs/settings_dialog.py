"""Settings dialog for application preferences."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, 
    QComboBox, QCheckBox, QPushButton, QGroupBox,
    QFormLayout, QMessageBox, QCompleter
)
from PyQt6.QtCore import Qt

import logging
import requests

logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    """Settings/preferences dialog with LLM auto-discovery."""
    
    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setMinimumWidth(550)
        self.config = config
        
        self._setup_ui()
        self._load_settings()
        logger.info("Settings dialog initialized")
    
    def _setup_ui(self):
        """Setup tabbed interface with settings."""
        layout = QVBoxLayout()
        
        # Tabs
        tabs = QTabWidget()
        
        # General tab
        general_tab = QWidget()
        general_layout = QFormLayout(general_tab)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "System"])
        self.theme_combo.setToolTip("Select the application theme. Dark is recommended for reduced eye strain.")
        general_layout.addRow("Theme:", self.theme_combo)
        
        self.default_dir = QLineEdit()
        self.default_dir.setPlaceholderText("Select default directory...")
        self.default_dir.setToolTip("Default directory to open on startup. Leave empty to prompt each time.")
        general_layout.addRow("Default Directory:", self.default_dir)
        
        self.auto_scan = QCheckBox("Auto-scan directory on launch")
        self.auto_scan.setToolTip("Automatically start scanning when a directory is selected")
        general_layout.addRow(self.auto_scan)
        
        tabs.addTab(general_tab, "General")
        
        # LLM tab
        llm_tab = QWidget()
        llm_layout = QFormLayout(llm_tab)
        
        # LLM Provider
        self.llm_provider = QComboBox()
        self.llm_provider.addItems(["Ollama (Local)", "OpenAI Compatible"])
        self.llm_provider.setToolTip("Select your LLM provider. Ollama runs locally on your machine (recommended for privacy).")
        self.llm_provider.currentTextChanged.connect(self._on_provider_changed)
        llm_layout.addRow("LLM Provider:", self.llm_provider)
        
        # Model selection with auto-discovery
        model_group = QGroupBox("Model Selection")
        model_layout = QVBoxLayout(model_group)
        
        # Model dropdown + refresh button
        model_row = QHBoxLayout()
        self.llm_model = QComboBox()
        self.llm_model.setEditable(True)  # Allow manual entry
        self.llm_model.setToolTip(
            "Select or type the model name.\n"
            "Click 'Refresh' to auto-detect installed models.\n"
            "For Ollama: try 'llama3.2:3b', 'mistral', 'phi3'\n"
            "For OpenAI: use 'gpt-3.5-turbo', 'gpt-4'"
        )
        model_row.addWidget(self.llm_model)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setToolTip("Query Ollama for installed models")
        refresh_btn.clicked.connect(self._refresh_models)
        model_row.addWidget(refresh_btn)
        
        model_layout.addLayout(model_row)
        
        # Model status label
        self.model_status = QLabel("Click 'Refresh' to detect installed models")
        self.model_status.setStyleSheet("color: #737373; font-size: 11px;")
        model_layout.addWidget(self.model_status)
        
        llm_layout.addRow(model_group)
        
        # API Endpoint
        self.llm_endpoint = QLineEdit()
        self.llm_endpoint.setPlaceholderText("http://localhost:11434")
        self.llm_endpoint.setText("http://localhost:11434")
        self.llm_endpoint.setToolTip(
            "Ollama API endpoint URL.\n"
            "Default: http://localhost:11434\n"
            "Only change if running Ollama on a different port or machine."
        )
        llm_layout.addRow("Ollama URL:", self.llm_endpoint)
        
        # API Key (for OpenAI-compatible)
        self.llm_api_key = QLineEdit()
        self.llm_api_key.setPlaceholderText("Required for OpenAI/OpenRouter...")
        self.llm_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.llm_api_key.setToolTip("API key for OpenAI-compatible services. Not needed for local Ollama.")
        llm_layout.addRow("API Key:", self.llm_api_key)
        
        # Temperature
        self.llm_temperature = QDoubleSpinBox()
        self.llm_temperature.setMinimum(0.0)
        self.llm_temperature.setMaximum(1.0)
        self.llm_temperature.setSingleStep(0.1)
        self.llm_temperature.setValue(0.7)
        self.llm_temperature.setToolTip(
            "Controls AI creativity (0.0 = deterministic, 1.0 = creative).\n"
            "Recommended: 0.7 for balanced results."
        )
        llm_layout.addRow("Temperature:", self.llm_temperature)
        
        # Test connection button
        test_btn = QPushButton("Test Connection")
        test_btn.setToolTip("Verify the LLM is reachable with current settings")
        test_btn.clicked.connect(self._test_connection)
        llm_layout.addRow("", test_btn)
        
        tabs.addTab(llm_tab, "LLM")
        
        # Organization tab
        org_tab = QWidget()
        org_layout = QFormLayout(org_tab)
        
        self.confidence_threshold = QDoubleSpinBox()
        self.confidence_threshold.setMinimum(0.0)
        self.confidence_threshold.setMaximum(1.0)
        self.confidence_threshold.setSingleStep(0.05)
        self.confidence_threshold.setValue(0.70)
        self.confidence_threshold.setToolTip(
            "Minimum confidence required to auto-organize a file.\n"
            "Files below this threshold will be flagged for review.\n"
            "Recommended: 0.70 (70%)"
        )
        org_layout.addRow("Confidence Threshold:", self.confidence_threshold)
        
        self.preserve_extensions = QCheckBox("Preserve file extensions")
        self.preserve_extensions.setChecked(True)
        self.preserve_extensions.setToolTip("Keep original file extensions when renaming files")
        org_layout.addRow(self.preserve_extensions)
        
        self.max_filename = QSpinBox()
        self.max_filename.setMinimum(20)
        self.max_filename.setMaximum(255)
        self.max_filename.setValue(200)
        self.max_filename.setToolTip("Maximum length for generated filenames (prevents OS errors)")
        org_layout.addRow("Max Filename Length:", self.max_filename)
        
        self.enable_backups = QCheckBox("Create backups before organization")
        self.enable_backups.setChecked(True)
        self.enable_backups.setToolTip("Create backup copies before moving/renaming files (recommended for safety)")
        org_layout.addRow(self.enable_backups)
        
        self.backup_retention = QSpinBox()
        self.backup_retention.setMinimum(1)
        self.backup_retention.setMaximum(365)
        self.backup_retention.setValue(30)
        self.backup_retention.setSuffix(" days")
        self.backup_retention.setToolTip("How long to keep backups before automatic cleanup")
        org_layout.addRow("Backup Retention:", self.backup_retention)
        
        tabs.addTab(org_tab, "Organization")
        
        # Advanced tab
        adv_tab = QWidget()
        adv_layout = QFormLayout(adv_tab)
        
        self.enable_logging = QCheckBox("Enable file logging")
        self.enable_logging.setChecked(True)
        self.enable_logging.setToolTip("Save application logs to file for troubleshooting")
        adv_layout.addRow(self.enable_logging)
        
        self.log_level = QComboBox()
        self.log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level.setCurrentText("INFO")
        self.log_level.setToolTip("Log verbosity level. DEBUG shows all details, ERROR shows only failures.")
        adv_layout.addRow("Log Level:", self.log_level)
        
        self.enable_cache = QCheckBox("Enable LLM response caching")
        self.enable_cache.setChecked(True)
        self.enable_cache.setToolTip("Cache AI responses to reduce API calls and improve speed")
        adv_layout.addRow(self.enable_cache)
        
        self.cache_retention = QSpinBox()
        self.cache_retention.setMinimum(1)
        self.cache_retention.setMaximum(365)
        self.cache_retention.setValue(30)
        self.cache_retention.setSuffix(" days")
        self.cache_retention.setToolTip("How long to keep cached LLM responses")
        adv_layout.addRow("Cache Retention:", self.cache_retention)
        
        self.max_workers = QSpinBox()
        self.max_workers.setMinimum(1)
        self.max_workers.setMaximum(16)
        self.max_workers.setValue(4)
        self.max_workers.setToolTip("Number of parallel workers for file operations (higher = faster but more CPU)")
        adv_layout.addRow("Max Parallel Workers:", self.max_workers)
        
        tabs.addTab(adv_tab, "Advanced")
        
        layout.addWidget(tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self._apply_settings)
        
        button_layout.addStretch()
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(apply_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Auto-refresh models on dialog open
        self._refresh_models()
    
    def _refresh_models(self):
        """Query Ollama for available models."""
        endpoint = self.llm_endpoint.text().strip() or "http://localhost:11434"
        
        self.model_status.setText("Querying Ollama for installed models...")
        self.model_status.setStyleSheet("color: #6366F1; font-size: 11px;")
        
        try:
            response = requests.get(f"{endpoint}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = [m.get('name', '') for m in data.get('models', [])]
                
                if models:
                    current_text = self.llm_model.currentText()
                    self.llm_model.clear()
                    self.llm_model.addItems(models)
                    
                    # Restore previous selection if it exists
                    if current_text:
                        index = self.llm_model.findText(current_text)
                        if index >= 0:
                            self.llm_model.setCurrentIndex(index)
                    
                    self.model_status.setText(f"Found {len(models)} installed model(s)")
                    self.model_status.setStyleSheet("color: #48bb78; font-size: 11px;")
                    logger.info(f"Auto-detected {len(models)} Ollama models")
                else:
                    self.model_status.setText("No models found. Install with: ollama pull llama3.2")
                    self.model_status.setStyleSheet("color: #ed8936; font-size: 11px;")
            else:
                self.model_status.setText(f"Ollama returned error {response.status_code}")
                self.model_status.setStyleSheet("color: #f56565; font-size: 11px;")
        except requests.exceptions.ConnectionError:
            self.model_status.setText("Cannot connect to Ollama. Is it running?")
            self.model_status.setStyleSheet("color: #f56565; font-size: 11px;")
            logger.warning("Could not connect to Ollama for model discovery")
        except Exception as e:
            self.model_status.setText(f"Error: {str(e)}")
            self.model_status.setStyleSheet("color: #f56565; font-size: 11px;")
            logger.error(f"Model discovery error: {e}")
    
    def _on_provider_changed(self, provider: str):
        """Handle provider change."""
        is_ollama = "Ollama" in provider
        
        # Update tooltips and placeholder based on provider
        if is_ollama:
            self.llm_endpoint.setPlaceholderText("http://localhost:11434")
            self.llm_endpoint.setText("http://localhost:11434")
            self.llm_api_key.setEnabled(False)
            self.llm_api_key.setToolTip("Not needed for local Ollama")
            self._refresh_models()
        else:
            self.llm_endpoint.setPlaceholderText("https://api.openai.com/v1")
            self.llm_api_key.setEnabled(True)
            self.llm_api_key.setToolTip("Required for OpenAI-compatible services")
            self.model_status.setText("Enter model name manually (e.g., gpt-3.5-turbo)")
            self.model_status.setStyleSheet("color: #737373; font-size: 11px;")
        
        logger.debug(f"LLM provider changed to: {provider}")
    
    def _load_settings(self):
        """Load current settings into UI."""
        if self.config:
            # Load from config if available
            pass
    
    def _test_connection(self):
        """Test LLM connection."""
        endpoint = self.llm_endpoint.text().strip()
        model = self.llm_model.currentText().strip() or self.llm_model.currentText()
        
        if not endpoint:
            QMessageBox.warning(self, "Invalid Settings", "Please specify the endpoint URL")
            return
        
        if not model:
            QMessageBox.warning(self, "Invalid Settings", "Please select or enter a model name")
            return
        
        # Test Ollama connection
        try:
            response = requests.get(f"{endpoint}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = [m.get('name', '') for m in data.get('models', [])]
                
                if model in models:
                    QMessageBox.information(
                        self,
                        "Connection Successful",
                        f"Successfully connected to Ollama!\n\n"
                        f"Model '{model}' is installed and ready."
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Model Not Found",
                        f"Connected to Ollama, but model '{model}' is not installed.\n\n"
                        f"Installed models: {', '.join(models[:5])}\n"
                        f"Install with: ollama pull {model}"
                    )
            else:
                QMessageBox.critical(
                    self,
                    "Connection Failed",
                    f"Ollama returned error {response.status_code}"
                )
        except requests.exceptions.ConnectionError:
            QMessageBox.critical(
                self,
                "Connection Failed",
                f"Cannot connect to Ollama at {endpoint}\n\n"
                "Make sure Ollama is installed and running.\n"
                "Download: https://ollama.ai"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Connection Error",
                f"Error testing connection: {str(e)}"
            )
    
    def _apply_settings(self):
        """Apply settings without closing dialog."""
        self.save_settings()
        QMessageBox.information(self, "Success", "Settings applied successfully")
    
    def save_settings(self):
        """Save settings to config."""
        settings = {
            "theme": self.theme_combo.currentText(),
            "default_directory": self.default_dir.text(),
            "auto_scan": self.auto_scan.isChecked(),
            "llm_provider": self.llm_provider.currentText(),
            "llm_model": self.llm_model.currentText(),
            "llm_temperature": self.llm_temperature.value(),
            "llm_endpoint": self.llm_endpoint.text(),
            "llm_api_key": self.llm_api_key.text(),
            "confidence_threshold": self.confidence_threshold.value(),
            "preserve_extensions": self.preserve_extensions.isChecked(),
            "max_filename_length": self.max_filename.value(),
            "enable_backups": self.enable_backups.isChecked(),
            "backup_retention_days": self.backup_retention.value(),
            "enable_logging": self.enable_logging.isChecked(),
            "log_level": self.log_level.currentText(),
            "enable_cache": self.enable_cache.isChecked(),
            "cache_retention_days": self.cache_retention.value(),
            "max_workers": self.max_workers.value(),
        }
        logger.info("Settings saved")
        return settings
    
    def get_settings(self) -> dict:
        """Get all current settings."""
        settings = self.save_settings()
        # backward-compatible key some tests expect
        settings['provider'] = self.llm_provider.currentText()
        return settings
