"""
Empty state widget for showing helpful empty states.
Displays contextual messages and actions when no data is present.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, 
    QSizePolicy, QHBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

import logging

logger = logging.getLogger(__name__)


class EmptyStateWidget(QWidget):
    """
    A widget that displays helpful empty state messages.
    
    Features:
    - Contextual icon and message based on state
    - Primary action button
    - Secondary help text
    - Accessible labeling
    """
    
    action_triggered = pyqtSignal()  # Emitted when action button clicked
    
    # Predefined states with icons and messages
    STATES = {
        'no_directory': {
            'icon': '📁',
            'title': 'No Directory Selected',
            'message': 'Select a folder to see your files and get AI-powered organization suggestions.',
            'action_text': 'Browse for Folder',
            'help_text': 'Tip: Choose a folder with documents, images, or other files you want to organize.'
        },
        'empty_folder': {
            'icon': '📂',
            'title': 'Folder is Empty',
            'message': 'This folder doesn\'t contain any files. Try selecting a different folder.',
            'action_text': 'Select Different Folder',
            'help_text': None
        },
        'no_results': {
            'icon': '🔍',
            'title': 'No Files to Analyze',
            'message': 'The selected folder appears to be empty or contains no supported file types.',
            'action_text': 'Select Different Folder',
            'help_text': 'Supported files: Documents, Images, Audio, Video, Code files, and more.'
        },
        'no_analysis': {
            'icon': '✨',
            'title': 'Ready to Analyze',
            'message': 'Click "Analyze Files" to get AI-powered organization suggestions for your files.',
            'action_text': 'Analyze Files',
            'help_text': 'This will scan your files and suggest the best way to organize them.'
        },
        'analysis_complete_empty': {
            'icon': '✅',
            'title': 'Analysis Complete',
            'message': 'All files have been analyzed. Select files and click "Organize" to apply changes.',
            'action_text': 'Organize Files',
            'help_text': 'Review the suggestions in the table above before organizing.'
        },
        'loading': {
            'icon': '⏳',
            'title': 'Loading...',
            'message': 'Please wait while we process your request.',
            'action_text': None,
            'help_text': None
        },
        'error': {
            'icon': '⚠️',
            'title': 'Something Went Wrong',
            'message': 'We encountered an error while processing your request.',
            'action_text': 'Try Again',
            'help_text': 'If the problem persists, check your settings or try a different folder.'
        }
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_state = None
        self._setup_ui()
        logger.debug("EmptyStateWidget initialized")
    
    def _setup_ui(self):
        """Setup the empty state UI with proper spacing and hierarchy."""
        # Main layout with generous spacing
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)
        layout.setContentsMargins(48, 48, 48, 48)
        
        # Icon label - large and centered
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(48)
        self.icon_label.setFont(font)
        self.icon_label.setObjectName("emptyStateIcon")
        layout.addWidget(self.icon_label)
        
        # Title - prominent
        self.title_label = QLabel()
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(18)
        font.setWeight(QFont.Weight.DemiBold)
        self.title_label.setFont(font)
        self.title_label.setObjectName("emptyStateTitle")
        layout.addWidget(self.title_label)
        
        # Message - descriptive
        self.message_label = QLabel()
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setWordWrap(True)
        font = QFont()
        font.setPointSize(13)
        self.message_label.setFont(font)
        self.message_label.setObjectName("emptyStateMessage")
        layout.addWidget(self.message_label)
        
        # Spacer before button
        layout.addSpacing(8)
        
        # Action button container (for centering)
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.addStretch()
        
        # Action button
        self.action_button = QPushButton()
        self.action_button.setObjectName("primaryButton")
        self.action_button.setMinimumWidth(180)
        self.action_button.setMinimumHeight(36)
        self.action_button.clicked.connect(self._on_action_clicked)
        self.action_button.setCursor(Qt.CursorShape.PointingHandCursor)
        button_layout.addWidget(self.action_button)
        button_layout.addStretch()
        
        layout.addWidget(button_container)
        
        # Help text - subtle
        self.help_label = QLabel()
        self.help_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.help_label.setWordWrap(True)
        font = QFont()
        font.setPointSize(11)
        self.help_label.setFont(font)
        self.help_label.setObjectName("emptyStateHelp")
        layout.addWidget(self.help_label)
        
        # Add stretch to push everything to center
        layout.addStretch()
        
        self.setLayout(layout)
        
        # Set accessible name for screen readers
        self.setAccessibleName("Empty State Panel")
        
        # Default to no_directory state
        self.set_state('no_directory')
    
    def set_state(self, state_name: str, custom_message: str = None):
        """
        Set the empty state to display.
        
        Args:
            state_name: Key from STATES dict
            custom_message: Optional override for the message text
        """
        if state_name not in self.STATES:
            logger.warning(f"Unknown empty state: {state_name}")
            state_name = 'no_directory'
        
        self.current_state = state_name
        state = self.STATES[state_name]
        
        # Update icon
        self.icon_label.setText(state['icon'])
        self.icon_label.setAccessibleDescription(f"Icon: {state['icon']}")
        
        # Update title
        self.title_label.setText(state['title'])
        self.title_label.setAccessibleName(state['title'])
        
        # Update message (use custom if provided)
        message = custom_message or state['message']
        self.message_label.setText(message)
        
        # Update action button
        action_text = state['action_text']
        if action_text:
            self.action_button.setText(action_text)
            self.action_button.setVisible(True)
            self.action_button.setAccessibleName(action_text)
            self.action_button.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        else:
            self.action_button.setVisible(False)
        
        # Update help text
        help_text = state['help_text']
        if help_text:
            self.help_label.setText(help_text)
            self.help_label.setVisible(True)
        else:
            self.help_label.setVisible(False)
        
        logger.debug(f"Empty state set to: {state_name}")
    
    def set_custom(self, icon: str, title: str, message: str, 
                   action_text: str = None, help_text: str = None):
        """Set a completely custom empty state."""
        self.icon_label.setText(icon)
        self.title_label.setText(title)
        self.message_label.setText(message)
        
        if action_text:
            self.action_button.setText(action_text)
            self.action_button.setVisible(True)
        else:
            self.action_button.setVisible(False)
        
        if help_text:
            self.help_label.setText(help_text)
            self.help_label.setVisible(True)
        else:
            self.help_label.setVisible(False)
        
        self.current_state = 'custom'
    
    def _on_action_clicked(self):
        """Handle action button click."""
        self.action_triggered.emit()
        logger.debug(f"Empty state action triggered: {self.current_state}")
    
    def get_current_state(self) -> str:
        """Get the current state name."""
        return self.current_state
    
    def set_action_enabled(self, enabled: bool):
        """Enable or disable the action button."""
        self.action_button.setEnabled(enabled)
    
    def focus_action_button(self):
        """Set focus to the action button for keyboard navigation."""
        if self.action_button.isVisible() and self.action_button.isEnabled():
            self.action_button.setFocus()
