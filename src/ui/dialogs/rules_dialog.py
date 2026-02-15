"""
Rules Manager Dialog for managing custom organization rules.
"""
import uuid
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QLineEdit, QComboBox, QPushButton, QGroupBox,
    QFormLayout, QMessageBox, QTextEdit, QSpinBox, QCheckBox,
    QDoubleSpinBox, QDialogButtonBox, QWidget, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

import logging

try:
    from ...core.rules_engine import (
        RulesEngine, OrganizationRule, RuleType, RuleOperator
    )
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from core.rules_engine import (
        RulesEngine, OrganizationRule, RuleType, RuleOperator
    )

logger = logging.getLogger(__name__)


class RulesManagerDialog(QDialog):
    """Dialog for managing organization rules."""
    
    rules_changed = pyqtSignal()  # Emitted when rules are modified
    
    def __init__(self, rules_engine: Optional[RulesEngine] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Organization Rules Manager")
        self.setModal(False)
        self.resize(900, 700)
        
        self.rules_engine = rules_engine or RulesEngine()
        self.current_rule: Optional[OrganizationRule] = None
        
        self._setup_ui()
        self._load_rules()
        
        logger.info("Rules Manager dialog initialized")
    
    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel(
            "Create rules to automatically organize files based on patterns, extensions, "
            "content, size, or date. Rules are evaluated in priority order (lower number = higher priority)."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #666; padding: 5px;")
        layout.addWidget(instructions)
        
        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side: Rules list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        left_layout.addWidget(QLabel("Rules (lower priority = evaluated first):"))
        
        self.rules_list = QListWidget()
        self.rules_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
            }
            QListWidget::item:disabled {
                color: #999;
            }
        """)
        self.rules_list.currentItemChanged.connect(self._on_rule_selected)
        left_layout.addWidget(self.rules_list)
        
        # List buttons
        list_buttons = QHBoxLayout()
        
        self.add_btn = QPushButton("➕ Add Rule")
        self.add_btn.clicked.connect(self._add_new_rule)
        list_buttons.addWidget(self.add_btn)
        
        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.clicked.connect(self._delete_current_rule)
        list_buttons.addWidget(self.delete_btn)
        
        self.duplicate_btn = QPushButton("📋 Duplicate")
        self.duplicate_btn.clicked.connect(self._duplicate_current_rule)
        list_buttons.addWidget(self.duplicate_btn)
        
        left_layout.addLayout(list_buttons)
        
        # Move buttons
        move_buttons = QHBoxLayout()
        
        self.move_up_btn = QPushButton("⬆️ Move Up")
        self.move_up_btn.clicked.connect(self._move_rule_up)
        move_buttons.addWidget(self.move_up_btn)
        
        self.move_down_btn = QPushButton("⬇️ Move Down")
        self.move_down_btn.clicked.connect(self._move_rule_down)
        move_buttons.addWidget(self.move_down_btn)
        
        left_layout.addLayout(move_buttons)
        
        splitter.addWidget(left_widget)
        
        # Right side: Rule editor
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 0, 0, 0)
        
        # Rule editor form
        editor_group = QGroupBox("Rule Editor")
        editor_layout = QFormLayout(editor_group)
        
        # Rule name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter rule name...")
        editor_layout.addRow("Rule Name:*", self.name_input)
        
        # Description
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Optional description...")
        self.desc_input.setMaximumHeight(60)
        editor_layout.addRow("Description:", self.desc_input)
        
        # Enabled checkbox
        self.enabled_check = QCheckBox("Rule Enabled")
        self.enabled_check.setChecked(True)
        editor_layout.addRow(self.enabled_check)
        
        # Rule type
        self.type_combo = QComboBox()
        self.type_combo.addItem("Filename Pattern", RuleType.FILENAME_PATTERN)
        self.type_combo.addItem("File Extension", RuleType.EXTENSION)
        self.type_combo.addItem("Content Keyword", RuleType.CONTENT_KEYWORD)
        self.type_combo.addItem("File Size", RuleType.FILE_SIZE)
        self.type_combo.addItem("Date Modified", RuleType.DATE_MODIFIED)
        self.type_combo.addItem("Date Created", RuleType.DATE_CREATED)
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        editor_layout.addRow("Rule Type:*", self.type_combo)
        
        # Operator
        self.operator_combo = QComboBox()
        self._update_operators()
        editor_layout.addRow("Operator:*", self.operator_combo)
        
        # Value input
        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("Enter value to match...")
        editor_layout.addRow("Value:*", self.value_input)
        
        # Value2 input (for BETWEEN operator)
        self.value2_label = QLabel("Value 2:*")
        self.value2_input = QLineEdit()
        self.value2_input.setPlaceholderText("Enter second value (for 'between')...")
        editor_layout.addRow(self.value2_label, self.value2_input)
        self.value2_label.setVisible(False)
        self.value2_input.setVisible(False)
        
        # Case sensitive
        self.case_sensitive_check = QCheckBox("Case Sensitive")
        editor_layout.addRow(self.case_sensitive_check)
        
        # Separator
        separator = QWidget()
        separator.setMinimumHeight(10)
        editor_layout.addRow(separator)
        
        # Target category
        self.category_input = QLineEdit()
        self.category_input.setPlaceholderText("e.g., Documents, Images, Archive...")
        editor_layout.addRow("Target Category:*", self.category_input)
        
        # Rename pattern
        self.rename_input = QLineEdit()
        self.rename_input.setPlaceholderText("Optional: {original_name}_{date}{original_ext}")
        editor_layout.addRow("Rename Pattern:", self.rename_input)
        
        # Priority
        self.priority_spin = QSpinBox()
        self.priority_spin.setMinimum(1)
        self.priority_spin.setMaximum(999)
        self.priority_spin.setValue(100)
        editor_layout.addRow("Priority:", self.priority_spin)
        
        # Variables help
        vars_label = QLabel(
            "Variables for rename pattern: {original_name}, {original_ext}, {category}, "
            "{date}, {datetime}"
        )
        vars_label.setStyleSheet("color: #666; font-size: 10px;")
        vars_label.setWordWrap(True)
        editor_layout.addRow(vars_label)
        
        right_layout.addWidget(editor_group)
        
        # Test section
        test_group = QGroupBox("Test Rule")
        test_layout = QVBoxLayout(test_group)
        
        test_input_layout = QHBoxLayout()
        self.test_path_input = QLineEdit()
        self.test_path_input.setPlaceholderText("Enter file path to test...")
        test_input_layout.addWidget(self.test_path_input)
        
        self.test_btn = QPushButton("Test")
        self.test_btn.clicked.connect(self._test_rule)
        test_input_layout.addWidget(self.test_btn)
        
        test_layout.addLayout(test_input_layout)
        
        self.test_result = QLabel("Test result will appear here")
        self.test_result.setStyleSheet("""
            padding: 10px;
            background-color: #f5f5f5;
            border-radius: 4px;
        """)
        self.test_result.setWordWrap(True)
        test_layout.addWidget(self.test_result)
        
        right_layout.addWidget(test_group)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply
        )
        button_box.accepted.connect(self._save_all_rules)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self._apply_current_rule)
        right_layout.addWidget(button_box)
        
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter, 1)
        
        # Import/Export buttons
        import_export_layout = QHBoxLayout()
        
        self.import_btn = QPushButton("📥 Import Rules")
        self.import_btn.clicked.connect(self._import_rules)
        import_export_layout.addWidget(self.import_btn)
        
        self.export_btn = QPushButton("📤 Export Rules")
        self.export_btn.clicked.connect(self._export_rules)
        import_export_layout.addWidget(self.export_btn)
        
        import_export_layout.addStretch()
        
        self.clear_btn = QPushButton("🗑️ Clear All")
        self.clear_btn.clicked.connect(self._clear_all_rules)
        import_export_layout.addWidget(self.clear_btn)
        
        layout.addLayout(import_export_layout)
        
        self.setLayout(layout)
        
        # Connect value changes to auto-apply
        self.name_input.textChanged.connect(self._auto_apply)
        self.desc_input.textChanged.connect(self._auto_apply)
        self.enabled_check.stateChanged.connect(self._auto_apply)
        self.type_combo.currentIndexChanged.connect(self._auto_apply)
        self.operator_combo.currentIndexChanged.connect(self._auto_apply)
        self.value_input.textChanged.connect(self._auto_apply)
        self.value2_input.textChanged.connect(self._auto_apply)
        self.case_sensitive_check.stateChanged.connect(self._auto_apply)
        self.category_input.textChanged.connect(self._auto_apply)
        self.rename_input.textChanged.connect(self._auto_apply)
        self.priority_spin.valueChanged.connect(self._auto_apply)
    
    def _update_operators(self):
        """Update available operators based on rule type."""
        current_type = self.type_combo.currentData()
        
        self.operator_combo.clear()
        
        if current_type in (RuleType.FILENAME_PATTERN, RuleType.CONTENT_KEYWORD):
            self.operator_combo.addItem("Contains", RuleOperator.CONTAINS)
            self.operator_combo.addItem("Equals", RuleOperator.EQUALS)
            self.operator_combo.addItem("Starts With", RuleOperator.STARTS_WITH)
            self.operator_combo.addItem("Ends With", RuleOperator.ENDS_WITH)
            self.operator_combo.addItem("Matches Regex", RuleOperator.MATCHES_REGEX)
        
        elif current_type == RuleType.EXTENSION:
            self.operator_combo.addItem("Is", RuleOperator.EQUALS)
            self.operator_combo.addItem("Contains", RuleOperator.CONTAINS)
        
        elif current_type in (RuleType.FILE_SIZE, RuleType.DATE_MODIFIED, RuleType.DATE_CREATED):
            self.operator_combo.addItem("Greater Than", RuleOperator.GREATER_THAN)
            self.operator_combo.addItem("Less Than", RuleOperator.LESS_THAN)
            self.operator_combo.addItem("Equals", RuleOperator.EQUALS)
            self.operator_combo.addItem("Between", RuleOperator.BETWEEN)
    
    def _on_type_changed(self):
        """Handle rule type change."""
        self._update_operators()
        
        # Show/hide value2 for BETWEEN operator
        self._update_value2_visibility()
        
        # Update placeholder text
        current_type = self.type_combo.currentData()
        
        if current_type == RuleType.FILENAME_PATTERN:
            self.value_input.setPlaceholderText("e.g., report, IMG_, .*\\.backup")
        elif current_type == RuleType.EXTENSION:
            self.value_input.setPlaceholderText("e.g., pdf, jpg, png or pdf,jpg,png")
        elif current_type == RuleType.CONTENT_KEYWORD:
            self.value_input.setPlaceholderText("e.g., CONFIDENTIAL, TODO")
        elif current_type == RuleType.FILE_SIZE:
            self.value_input.setPlaceholderText("e.g., 10MB, 1GB, 1024")
        elif current_type in (RuleType.DATE_MODIFIED, RuleType.DATE_CREATED):
            self.value_input.setPlaceholderText("e.g., 7_days_ago, 1_month_ago, today")
    
    def _update_value2_visibility(self):
        """Show/hide value2 input based on operator."""
        current_op = self.operator_combo.currentData()
        show_value2 = current_op == RuleOperator.BETWEEN
        self.value2_label.setVisible(show_value2)
        self.value2_input.setVisible(show_value2)
    
    def _load_rules(self):
        """Load rules into the list."""
        self.rules_list.clear()
        
        rules = self.rules_engine.get_rules()
        for rule in sorted(rules, key=lambda r: r.priority):
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, rule.id)
            
            # Format display text
            status = "✓" if rule.enabled else "✗"
            display_text = f"[{status}] [{rule.priority}] {rule.name}"
            if rule.target_category:
                display_text += f" → {rule.target_category}"
            
            item.setText(display_text)
            
            # Gray out disabled rules
            if not rule.enabled:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            
            self.rules_list.addItem(item)
        
        self._clear_editor()
    
    def _on_rule_selected(self, current: QListWidgetItem, previous: QListWidgetItem):
        """Handle rule selection."""
        if current is None:
            self._clear_editor()
            return
        
        rule_id = current.data(Qt.ItemDataRole.UserRole)
        rule = self.rules_engine.get_rule(rule_id)
        
        if rule:
            self.current_rule = rule
            self._populate_editor(rule)
    
    def _populate_editor(self, rule: OrganizationRule):
        """Populate editor fields with rule data."""
        self.name_input.setText(rule.name)
        self.desc_input.setText(rule.description)
        self.enabled_check.setChecked(rule.enabled)
        
        # Set type
        type_index = self.type_combo.findData(rule.rule_type)
        if type_index >= 0:
            self.type_combo.setCurrentIndex(type_index)
        
        # Set operator
        op_index = self.operator_combo.findData(rule.operator)
        if op_index >= 0:
            self.operator_combo.setCurrentIndex(op_index)
        
        self.value_input.setText(str(rule.value))
        if rule.value2 is not None:
            self.value2_input.setText(str(rule.value2))
        
        self.case_sensitive_check.setChecked(rule.case_sensitive)
        self.category_input.setText(rule.target_category)
        self.rename_input.setText(rule.target_name_pattern or "")
        self.priority_spin.setValue(rule.priority)
    
    def _clear_editor(self):
        """Clear editor fields."""
        self.current_rule = None
        self.name_input.clear()
        self.desc_input.clear()
        self.enabled_check.setChecked(True)
        self.type_combo.setCurrentIndex(0)
        self.value_input.clear()
        self.value2_input.clear()
        self.case_sensitive_check.setChecked(False)
        self.category_input.clear()
        self.rename_input.clear()
        self.priority_spin.setValue(100)
    
    def _add_new_rule(self):
        """Add a new rule."""
        new_rule = OrganizationRule(
            id=str(uuid.uuid4()),
            name="New Rule",
            rule_type=RuleType.FILENAME_PATTERN,
            operator=RuleOperator.CONTAINS,
            value="",
            target_category="uncategorized",
            priority=100
        )
        
        self.rules_engine.add_rule(new_rule)
        self._load_rules()
        
        # Select the new rule
        for i in range(self.rules_list.count()):
            item = self.rules_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == new_rule.id:
                self.rules_list.setCurrentItem(item)
                break
        
        self.rules_changed.emit()
    
    def _delete_current_rule(self):
        """Delete the currently selected rule."""
        if not self.current_rule:
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete rule '{self.current_rule.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.rules_engine.remove_rule(self.current_rule.id)
            self._load_rules()
            self.rules_changed.emit()
    
    def _duplicate_current_rule(self):
        """Duplicate the currently selected rule."""
        if not self.current_rule:
            return
        
        new_rule = OrganizationRule(
            id=str(uuid.uuid4()),
            name=f"{self.current_rule.name} (Copy)",
            rule_type=self.current_rule.rule_type,
            operator=self.current_rule.operator,
            value=self.current_rule.value,
            value2=self.current_rule.value2,
            target_category=self.current_rule.target_category,
            target_name_pattern=self.current_rule.target_name_pattern,
            priority=self.current_rule.priority + 1,
            enabled=self.current_rule.enabled,
            case_sensitive=self.current_rule.case_sensitive,
            description=self.current_rule.description
        )
        
        self.rules_engine.add_rule(new_rule)
        self._load_rules()
        self.rules_changed.emit()
    
    def _move_rule_up(self):
        """Move current rule up in priority."""
        if not self.current_rule:
            return
        
        # Decrease priority number (higher priority)
        new_priority = max(1, self.current_rule.priority - 1)
        self.rules_engine.update_rule(self.current_rule.id, {'priority': new_priority})
        self._load_rules()
        self.rules_changed.emit()
    
    def _move_rule_down(self):
        """Move current rule down in priority."""
        if not self.current_rule:
            return
        
        # Increase priority number (lower priority)
        new_priority = self.current_rule.priority + 1
        self.rules_engine.update_rule(self.current_rule.id, {'priority': new_priority})
        self._load_rules()
        self.rules_changed.emit()
    
    def _apply_current_rule(self):
        """Apply current editor values to the selected rule."""
        if not self.current_rule:
            return
        
        updates = {
            'name': self.name_input.text(),
            'description': self.desc_input.toPlainText(),
            'enabled': self.enabled_check.isChecked(),
            'rule_type': self.type_combo.currentData(),
            'operator': self.operator_combo.currentData(),
            'value': self.value_input.text(),
            'value2': self.value2_input.text() if self.value2_input.text() else None,
            'case_sensitive': self.case_sensitive_check.isChecked(),
            'target_category': self.category_input.text(),
            'target_name_pattern': self.rename_input.text() or None,
            'priority': self.priority_spin.value()
        }
        
        self.rules_engine.update_rule(self.current_rule.id, updates)
        self._load_rules()
        self.rules_changed.emit()
    
    def _auto_apply(self):
        """Automatically apply changes (for live editing)."""
        if self.current_rule:
            self._apply_current_rule()
    
    def _test_rule(self):
        """Test the current rule against a file path."""
        test_path = self.test_path_input.text().strip()
        
        if not test_path:
            self.test_result.setText("Please enter a file path to test")
            return
        
        # Create temporary rule from current editor values
        test_rule = OrganizationRule(
            id="test",
            name="Test Rule",
            rule_type=self.type_combo.currentData(),
            operator=self.operator_combo.currentData(),
            value=self.value_input.text(),
            value2=self.value2_input.text() if self.value2_input.text() else None,
            case_sensitive=self.case_sensitive_check.isChecked(),
            target_category=self.category_input.text(),
            enabled=True
        )
        
        try:
            from ...core.rules_engine import RulesEngine
            temp_engine = RulesEngine([test_rule])
            match = temp_engine.evaluate_file(test_path)
            
            if match.matched:
                self.test_result.setStyleSheet("""
                    padding: 10px;
                    background-color: #e8f5e9;
                    border-radius: 4px;
                    color: #2e7d32;
                """)
                result_text = f"✅ MATCHED!\n\n"
                result_text += f"File: {test_path}\n"
                result_text += f"Category: {match.target_category}\n"
                if match.target_name:
                    result_text += f"New name: {match.target_name}\n"
            else:
                self.test_result.setStyleSheet("""
                    padding: 10px;
                    background-color: #ffebee;
                    border-radius: 4px;
                    color: #c62828;
                """)
                result_text = f"❌ NOT MATCHED\n\n"
                result_text += f"File: {test_path}\n"
                result_text += f"Reason: {match.reasoning}"
            
            self.test_result.setText(result_text)
            
        except Exception as e:
            self.test_result.setStyleSheet("""
                padding: 10px;
                background-color: #fff3e0;
                border-radius: 4px;
                color: #ef6c00;
            """)
            self.test_result.setText(f"⚠️ Error testing rule: {e}")
    
    def _save_all_rules(self):
        """Save all rules and close dialog."""
        self._apply_current_rule()
        self.accept()
    
    def _import_rules(self):
        """Import rules from a JSON file."""
        from PyQt6.QtWidgets import QFileDialog
        
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Import Rules",
            "",
            "JSON Files (*.json)"
        )
        
        if filepath:
            try:
                self.rules_engine.load_from_file(filepath)
                self._load_rules()
                self.rules_changed.emit()
                QMessageBox.information(self, "Success", "Rules imported successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import rules: {e}")
    
    def _export_rules(self):
        """Export rules to a JSON file."""
        from PyQt6.QtWidgets import QFileDialog
        
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Rules",
            "rules.json",
            "JSON Files (*.json)"
        )
        
        if filepath:
            try:
                self.rules_engine.save_to_file(filepath)
                QMessageBox.information(self, "Success", "Rules exported successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export rules: {e}")
    
    def _clear_all_rules(self):
        """Clear all rules."""
        reply = QMessageBox.question(
            self,
            "Confirm Clear",
            "Remove all rules? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.rules_engine.clear_rules()
            self._load_rules()
            self.rules_changed.emit()
    
    def get_rules_engine(self) -> RulesEngine:
        """Get the rules engine with current rules."""
        return self.rules_engine
