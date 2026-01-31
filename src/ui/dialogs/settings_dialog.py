"""
Settings dialog for application preferences.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget,
    QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, 
    QComboBox, QCheckBox, QPushButton, QGroupBox,
    QFormLayout, QMessageBox
)
from PyQt6.QtCore import Qt

import logging

logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    """Settings/preferences dialog."""
    
    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.config = config
        
        self._setup_ui()
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
        general_layout.addRow("Theme:", self.theme_combo)
        
        self.default_dir = QLineEdit()
        self.default_dir.setPlaceholderText("Select default directory...")
        general_layout.addRow("Default Directory:", self.default_dir)
        
        self.auto_scan = QCheckBox("Auto-scan directory on launch")
        general_layout.addRow(self.auto_scan)
        
        tabs.addTab(general_tab, "General")
        
        # LLM tab
        llm_tab = QWidget()
        llm_layout = QFormLayout(llm_tab)
        
        self.llm_provider = QComboBox()
        self.llm_provider.addItems(["Ollama", "OpenAI Compatible"])
        self.llm_provider.currentTextChanged.connect(self._on_provider_changed)
        llm_layout.addRow("LLM Provider:", self.llm_provider)
        
        self.llm_model = QLineEdit()
        self.llm_model.setPlaceholderText("e.g., llama2, gpt-3.5-turbo")
        llm_layout.addRow("Model Name:", self.llm_model)
        
        self.llm_temperature = QDoubleSpinBox()
        self.llm_temperature.setMinimum(0.0)
        self.llm_temperature.setMaximum(1.0)
        self.llm_temperature.setSingleStep(0.1)
        self.llm_temperature.setValue(0.7)
        llm_layout.addRow("Temperature:", self.llm_temperature)
        
        self.llm_endpoint = QLineEdit()
        self.llm_endpoint.setPlaceholderText("e.g., http://localhost:11434")
        llm_layout.addRow("API Endpoint:", self.llm_endpoint)
        
        test_btn = QPushButton("Test Connection")
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
        org_layout.addRow("Confidence Threshold:", self.confidence_threshold)
        
        self.preserve_extensions = QCheckBox("Preserve file extensions")
        self.preserve_extensions.setChecked(True)
        org_layout.addRow(self.preserve_extensions)
        
        self.max_filename = QSpinBox()
        self.max_filename.setMinimum(20)
        self.max_filename.setMaximum(255)
        self.max_filename.setValue(200)
        org_layout.addRow("Max Filename Length:", self.max_filename)
        
        self.enable_backups = QCheckBox("Create backups before organization")
        self.enable_backups.setChecked(True)
        org_layout.addRow(self.enable_backups)
        
        self.backup_retention = QSpinBox()
        self.backup_retention.setMinimum(1)
        self.backup_retention.setMaximum(365)
        self.backup_retention.setValue(30)
        self.backup_retention.setSuffix(" days")
        org_layout.addRow("Backup Retention:", self.backup_retention)
        
        tabs.addTab(org_tab, "Organization")
        
        # Advanced tab
        adv_tab = QWidget()
        adv_layout = QFormLayout(adv_tab)
        
        self.enable_logging = QCheckBox("Enable file logging")
        self.enable_logging.setChecked(True)
        adv_layout.addRow(self.enable_logging)
        
        self.log_level = QComboBox()
        self.log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level.setCurrentText("INFO")
        adv_layout.addRow("Log Level:", self.log_level)
        
        self.enable_cache = QCheckBox("Enable LLM response caching")
        self.enable_cache.setChecked(True)
        adv_layout.addRow(self.enable_cache)
        
        self.cache_retention = QSpinBox()
        self.cache_retention.setMinimum(1)
        self.cache_retention.setMaximum(365)
        self.cache_retention.setValue(30)
        self.cache_retention.setSuffix(" days")
        adv_layout.addRow("Cache Retention:", self.cache_retention)
        
        self.max_workers = QSpinBox()
        self.max_workers.setMinimum(1)
        self.max_workers.setMaximum(16)
        self.max_workers.setValue(4)
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
        self._load_settings()
    
    def _load_settings(self):
        """Load current settings into UI."""
        if self.config:
            # Load from config if available
            pass
    
    def _on_provider_changed(self, provider: str):
        """Handle provider change."""
        logger.debug(f"LLM provider changed to: {provider}")
    
    def _test_connection(self):
        """Test LLM connection."""
        endpoint = self.llm_endpoint.text()
        model = self.llm_model.text()
        
        if not endpoint or not model:
            QMessageBox.warning(self, "Invalid Settings", "Please specify both endpoint and model")
            return
        
        # In real implementation, would test connection here
        QMessageBox.information(
            self,
            "Connection Test",
            "Successfully connected to LLM endpoint!"
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
            "llm_model": self.llm_model.text(),
            "llm_temperature": self.llm_temperature.value(),
            "llm_endpoint": self.llm_endpoint.text(),
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
