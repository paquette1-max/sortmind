"""
License dialog for File Organizer Pro features.
"""
import logging
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QMessageBox, QFrame, QSpacerItem, QSizePolicy,
    QGroupBox, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QDesktopServices
from PyQt6.QtCore import QUrl

try:
    from ...core.license_manager import get_license_manager, LicenseManager
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from core.license_manager import get_license_manager, LicenseManager

logger = logging.getLogger(__name__)


class LicenseDialog(QDialog):
    """
    Dialog for entering and managing license keys.
    
    Features:
    - Display current license status
    - Enter license key
    - Show trial remaining
    - Link to purchase
    """
    
    license_activated = pyqtSignal()  # Emitted when license is successfully activated
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.license_mgr = get_license_manager()
        self._setup_ui()
        self._update_status()
        
        self.setWindowTitle("License - File Organizer")
        self.resize(500, 400)
        
        logger.info("LicenseDialog opened")
    
    def _setup_ui(self):
        """Setup the license dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Header
        header = QLabel("🧠 SortMind Pro")
        header_font = QFont("", 18, QFont.Weight.Bold)
        header.setFont(header_font)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        subtitle = QLabel("Unlock AI-powered document analysis")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #737373;")
        layout.addWidget(subtitle)
        
        # Status section
        status_group = QGroupBox("Current Status")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel("Loading...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_font = QFont("", 12)
        self.status_label.setFont(status_font)
        status_layout.addWidget(self.status_label)
        
        self.features_label = QLabel("")
        self.features_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.features_label.setStyleSheet("color: #22C55E;")
        status_layout.addWidget(self.features_label)
        
        self.trial_label = QLabel("")
        self.trial_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.trial_label.setStyleSheet("color: #F59E0B;")
        status_layout.addWidget(self.trial_label)
        
        layout.addWidget(status_group)
        
        # License key entry
        key_group = QGroupBox("Enter License Key")
        key_layout = QVBoxLayout(key_group)
        
        key_hint = QLabel("Format: PRO-XXXX-XXXX-XXXX or ENT-XXXX-XXXX-XXXX")
        key_hint.setStyleSheet("color: #737373; font-size: 11px;")
        key_layout.addWidget(key_hint)
        
        key_input_layout = QHBoxLayout()
        
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("Enter your license key...")
        self.key_input.setMaxLength(23)  # PRO-XXXX-XXXX-XXXX
        self.key_input.textChanged.connect(self._format_key_input)
        key_input_layout.addWidget(self.key_input)
        
        self.activate_btn = QPushButton("Activate")
        self.activate_btn.setStyleSheet("""
            QPushButton {
                background-color: #22C55E;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #16A34A;
            }
            QPushButton:disabled {
                background-color: #4B5563;
            }
        """)
        self.activate_btn.clicked.connect(self._activate_license)
        key_input_layout.addWidget(self.activate_btn)
        
        key_layout.addLayout(key_input_layout)
        
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #EF4444;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        key_layout.addWidget(self.error_label)
        
        layout.addWidget(key_group)
        
        # Pricing section
        pricing_group = QGroupBox("Upgrade to Pro")
        pricing_layout = QGridLayout(pricing_group)
        
        # Pro tier
        pro_label = QLabel("<b>Pro License</b><br>$49 one-time")
        pro_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pricing_layout.addWidget(pro_label, 0, 0)
        
        pro_features = QLabel("✓ AI Document Analysis<br>✓ Batch Processing<br>✓ Custom Patterns")
        pro_features.setStyleSheet("color: #737373;")
        pro_features.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pricing_layout.addWidget(pro_features, 1, 0)
        
        self.buy_pro_btn = QPushButton("Buy Pro")
        self.buy_pro_btn.clicked.connect(lambda: self._open_purchase_url("pro"))
        pricing_layout.addWidget(self.buy_pro_btn, 2, 0)
        
        # Enterprise tier
        ent_label = QLabel("<b>Enterprise</b><br>$199 one-time")
        ent_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pricing_layout.addWidget(ent_label, 0, 1)
        
        ent_features = QLabel("✓ Everything in Pro<br>✓ Cloud Sync<br>✓ Priority Support")
        ent_features.setStyleSheet("color: #737373;")
        ent_features.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pricing_layout.addWidget(ent_features, 1, 1)
        
        self.buy_ent_btn = QPushButton("Buy Enterprise")
        self.buy_ent_btn.clicked.connect(lambda: self._open_purchase_url("enterprise"))
        pricing_layout.addWidget(self.buy_ent_btn, 2, 1)
        
        layout.addWidget(pricing_group)
        
        # Info text
        info = QLabel("💡 Purchase via GitHub Sponsors. License key will be emailed within 24 hours.")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("color: #737373; font-size: 11px;")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        button_layout.addItem(spacer)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _update_status(self):
        """Update the status display based on current license."""
        status = self.license_mgr.get_license_status()
        
        tier = status["tier"]
        
        if status["status"] == "licensed":
            self.status_label.setText(f"✅ {tier.title()} License Active")
            self.status_label.setStyleSheet("color: #22C55E;")
            
            features = status.get("features", [])
            if features:
                feature_text = " | ".join([f.replace("_", " ").title() for f in features[:3]])
                self.features_label.setText(feature_text)
            
            self.trial_label.hide()
            self.key_input.setPlaceholderText("License active - enter new key to upgrade")
            self.activate_btn.setText("Update")
            
        elif status["status"] == "trial":
            remaining = status.get("trial_remaining", 0)
            self.status_label.setText("🧪 Trial Mode")
            self.status_label.setStyleSheet("color: #F59E0B;")
            self.trial_label.setText(f"{remaining} AI analyses remaining")
            self.features_label.hide()
            
        else:  # unlicensed
            self.status_label.setText("🔒 Free Version")
            self.status_label.setStyleSheet("color: #737373;")
            self.trial_label.setText("Trial expired - Upgrade to Pro")
            self.features_label.hide()
    
    def _format_key_input(self, text: str):
        """Auto-format license key as user types."""
        # Remove non-alphanumeric except dashes
        cleaned = "".join(c for c in text.upper() if c.isalnum() or c == "-")
        
        # Auto-insert dashes
        parts = cleaned.replace("-", "")
        formatted = ""
        for i, char in enumerate(parts):
            if i > 0 and i % 4 == 0 and i < 16:
                formatted += "-"
            formatted += char
        
        # Limit to format XXX-XXXX-XXXX-XXXX (19 chars)
        formatted = formatted[:19]
        
        if formatted != text.upper():
            self.key_input.setText(formatted)
            self.key_input.setCursorPosition(len(formatted))
    
    def _activate_license(self):
        """Attempt to activate license with entered key."""
        key = self.key_input.text().strip()
        
        if not key:
            self.error_label.setText("Please enter a license key")
            return
        
        success, message = self.license_mgr.validate_license_key(key)
        
        if success:
            self.error_label.setText("")
            self._update_status()
            self.license_activated.emit()
            
            QMessageBox.information(
                self,
                "License Activated",
                f"✅ {message}\n\nThank you for supporting SortMind!"
            )
        else:
            self.error_label.setText(f"❌ {message}")
    
    def _open_purchase_url(self, tier: str):
        """Open purchase URL in browser."""
        url = self.license_mgr.get_purchase_url()
        QDesktopServices.openUrl(QUrl(url))
        
        QMessageBox.information(
            self,
            "Purchase",
            f"Opening GitHub Sponsors...\n\n"
            f"Select the '{tier.title()}' tier and complete the sponsorship. "
            f"Your license key will be emailed within 24 hours."
        )


class UpgradePromptWidget(QFrame):
    """
    Small widget to show upgrade prompts in the main window.
    """
    
    upgrade_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.license_mgr = get_license_manager()
        self._setup_ui()
        self._update_prompt()
        
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
    
    def _setup_ui(self):
        """Setup the upgrade prompt widget."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)
        
        # Icon
        icon_label = QLabel("🧠")
        icon_font = QFont("", 20)
        icon_label.setFont(icon_font)
        layout.addWidget(icon_label)
        
        # Text
        text_layout = QVBoxLayout()
        
        self.title_label = QLabel("Unlock AI Analysis")
        title_font = QFont("", 11, QFont.Weight.Bold)
        self.title_label.setFont(title_font)
        text_layout.addWidget(self.title_label)
        
        self.desc_label = QLabel("Automatically name documents using AI")
        self.desc_label.setStyleSheet("color: #737373;")
        text_layout.addWidget(self.desc_label)
        
        layout.addLayout(text_layout, 1)
        
        # Button
        self.upgrade_btn = QPushButton("Upgrade")
        self.upgrade_btn.setStyleSheet("""
            QPushButton {
                background-color: #8B5CF6;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #7C3AED;
            }
        """)
        self.upgrade_btn.clicked.connect(self.upgrade_clicked.emit)
        layout.addWidget(self.upgrade_btn)
        
        # Close button (X)
        self.close_btn = QPushButton("×")
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #737373;
                font-size: 16px;
                border: none;
            }
            QPushButton:hover {
                color: #EF4444;
            }
        """)
        self.close_btn.clicked.connect(self.hide)
        layout.addWidget(self.close_btn)
    
    def _update_prompt(self):
        """Update prompt based on license status."""
        status = self.license_mgr.get_license_status()
        
        if status["status"] == "licensed":
            self.hide()  # Don't show for licensed users
            return
        
        elif status["status"] == "trial":
            remaining = status.get("trial_remaining", 0)
            self.title_label.setText(f"🧪 Trial Mode")
            self.desc_label.setText(f"{remaining} AI analyses remaining - Upgrade for unlimited")
            
        else:  # unlicensed
            self.title_label.setText("🔒 AI Features Locked")
            self.desc_label.setText("Upgrade to Pro for intelligent document analysis")
    
    def refresh(self):
        """Refresh the prompt display."""
        self._update_prompt()
