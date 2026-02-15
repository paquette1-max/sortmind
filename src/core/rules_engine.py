"""
Custom Rules Engine for user-defined file organization rules.
Supports pattern-based, extension-based, content-based, size/date-based rules.
"""
import re
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any, Callable, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class RuleType(Enum):
    """Types of organization rules."""
    FILENAME_PATTERN = "filename_pattern"  # Regex pattern on filename
    EXTENSION = "extension"  # File extension matching
    CONTENT_KEYWORD = "content_keyword"  # Keyword search in content
    FILE_SIZE = "file_size"  # Size-based rules
    DATE_MODIFIED = "date_modified"  # Date-based rules
    DATE_CREATED = "date_created"  # Creation date rules


class RuleOperator(Enum):
    """Comparison operators for rules."""
    EQUALS = "equals"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    MATCHES_REGEX = "matches_regex"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    BETWEEN = "between"


@dataclass
class OrganizationRule:
    """A single organization rule."""
    id: str
    name: str
    rule_type: RuleType
    operator: RuleOperator
    value: Any  # The value to compare against
    value2: Optional[Any] = None  # For BETWEEN operator
    target_category: str = "uncategorized"  # Where to organize matching files
    target_name_pattern: Optional[str] = None  # Optional rename pattern
    priority: int = 100  # Lower = higher priority
    enabled: bool = True
    case_sensitive: bool = False
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert rule to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'rule_type': self.rule_type.value,
            'operator': self.operator.value,
            'value': self.value,
            'value2': self.value2,
            'target_category': self.target_category,
            'target_name_pattern': self.target_name_pattern,
            'priority': self.priority,
            'enabled': self.enabled,
            'case_sensitive': self.case_sensitive,
            'description': self.description,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OrganizationRule':
        """Create rule from dictionary."""
        return cls(
            id=data['id'],
            name=data['name'],
            rule_type=RuleType(data['rule_type']),
            operator=RuleOperator(data['operator']),
            value=data['value'],
            value2=data.get('value2'),
            target_category=data.get('target_category', 'uncategorized'),
            target_name_pattern=data.get('target_name_pattern'),
            priority=data.get('priority', 100),
            enabled=data.get('enabled', True),
            case_sensitive=data.get('case_sensitive', False),
            description=data.get('description', ''),
            created_at=data.get('created_at', datetime.now().isoformat())
        )


@dataclass
class RuleMatch:
    """Result of a rule match."""
    matched: bool
    rule: Optional[OrganizationRule] = None
    target_category: Optional[str] = None
    target_name: Optional[str] = None
    confidence: float = 1.0
    reasoning: str = ""


class RulesEngine:
    """Engine for evaluating organization rules against files."""
    
    def __init__(self, rules: Optional[List[OrganizationRule]] = None):
        """
        Initialize rules engine.
        
        Args:
            rules: Initial list of rules
        """
        self.rules = rules or []
        self.logger = logger
        self._content_cache: Dict[Path, str] = {}  # Cache for file content
    
    def add_rule(self, rule: OrganizationRule) -> None:
        """Add a new rule."""
        self.rules.append(rule)
        # Sort by priority
        self.rules.sort(key=lambda r: r.priority)
        self.logger.info(f"Added rule: {rule.name} (priority: {rule.priority})")
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove a rule by ID."""
        for i, rule in enumerate(self.rules):
            if rule.id == rule_id:
                del self.rules[i]
                self.logger.info(f"Removed rule: {rule_id}")
                return True
        return False
    
    def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """Update a rule's properties."""
        for rule in self.rules:
            if rule.id == rule_id:
                for key, value in updates.items():
                    if hasattr(rule, key):
                        if key == 'rule_type':
                            value = RuleType(value)
                        elif key == 'operator':
                            value = RuleOperator(value)
                        setattr(rule, key, value)
                
                # Re-sort if priority changed
                if 'priority' in updates:
                    self.rules.sort(key=lambda r: r.priority)
                
                self.logger.info(f"Updated rule: {rule_id}")
                return True
        return False
    
    def get_rule(self, rule_id: str) -> Optional[OrganizationRule]:
        """Get a rule by ID."""
        for rule in self.rules:
            if rule.id == rule_id:
                return rule
        return None
    
    def enable_rule(self, rule_id: str) -> bool:
        """Enable a rule."""
        return self.update_rule(rule_id, {'enabled': True})
    
    def disable_rule(self, rule_id: str) -> bool:
        """Disable a rule."""
        return self.update_rule(rule_id, {'enabled': False})
    
    def evaluate_file(self, file_path: Union[str, Path], 
                      file_metadata: Optional[Dict] = None) -> RuleMatch:
        """
        Evaluate all rules against a file.
        
        Args:
            file_path: Path to the file
            file_metadata: Optional pre-computed metadata
            
        Returns:
            RuleMatch with the highest priority matching rule
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return RuleMatch(matched=False, reasoning="File not found")
        
        # Sort rules by priority (lowest number = highest priority)
        sorted_rules = sorted(self.rules, key=lambda r: r.priority)
        
        for rule in sorted_rules:
            if not rule.enabled:
                continue
            
            try:
                if self._evaluate_rule(rule, file_path, file_metadata):
                    # Generate target name if pattern provided
                    target_name = None
                    if rule.target_name_pattern:
                        target_name = self._apply_name_pattern(
                            rule.target_name_pattern, file_path, rule
                        )
                    
                    return RuleMatch(
                        matched=True,
                        rule=rule,
                        target_category=rule.target_category,
                        target_name=target_name,
                        confidence=1.0,
                        reasoning=f"Matched rule: {rule.name}"
                    )
            except Exception as e:
                self.logger.warning(f"Error evaluating rule {rule.name}: {e}")
                continue
        
        return RuleMatch(matched=False, reasoning="No matching rules found")
    
    def evaluate_files(self, file_paths: List[Union[str, Path]]) -> Dict[Path, RuleMatch]:
        """
        Evaluate rules against multiple files.
        
        Args:
            file_paths: List of file paths
            
        Returns:
            Dictionary mapping file paths to their rule matches
        """
        results = {}
        for file_path in file_paths:
            results[Path(file_path)] = self.evaluate_file(file_path)
        return results
    
    def _evaluate_rule(self, rule: OrganizationRule, file_path: Path,
                       file_metadata: Optional[Dict] = None) -> bool:
        """Evaluate a single rule against a file."""
        
        if rule.rule_type == RuleType.FILENAME_PATTERN:
            return self._evaluate_filename_rule(rule, file_path)
        
        elif rule.rule_type == RuleType.EXTENSION:
            return self._evaluate_extension_rule(rule, file_path)
        
        elif rule.rule_type == RuleType.CONTENT_KEYWORD:
            return self._evaluate_content_rule(rule, file_path)
        
        elif rule.rule_type == RuleType.FILE_SIZE:
            return self._evaluate_size_rule(rule, file_path)
        
        elif rule.rule_type == RuleType.DATE_MODIFIED:
            return self._evaluate_date_rule(rule, file_path, 'modified')
        
        elif rule.rule_type == RuleType.DATE_CREATED:
            return self._evaluate_date_rule(rule, file_path, 'created')
        
        return False
    
    def _evaluate_filename_rule(self, rule: OrganizationRule, file_path: Path) -> bool:
        """Evaluate filename pattern rule."""
        filename = file_path.name
        pattern = rule.value
        
        if not rule.case_sensitive:
            filename = filename.lower()
            pattern = pattern.lower()
        
        if rule.operator == RuleOperator.CONTAINS:
            return pattern in filename
        elif rule.operator == RuleOperator.STARTS_WITH:
            return filename.startswith(pattern)
        elif rule.operator == RuleOperator.ENDS_WITH:
            return filename.endswith(pattern)
        elif rule.operator == RuleOperator.EQUALS:
            return filename == pattern
        elif rule.operator == RuleOperator.MATCHES_REGEX:
            flags = 0 if rule.case_sensitive else re.IGNORECASE
            return bool(re.search(pattern, file_path.name, flags))
        
        return False
    
    def _evaluate_extension_rule(self, rule: OrganizationRule, file_path: Path) -> bool:
        """Evaluate file extension rule."""
        ext = file_path.suffix.lower()
        value = rule.value.lower() if isinstance(rule.value, str) else rule.value
        
        # Handle list of extensions
        if isinstance(value, list):
            extensions = [e.lower() if isinstance(e, str) else e for e in value]
        else:
            extensions = [value]
        
        # Ensure extensions start with dot
        extensions = [e if e.startswith('.') else f'.{e}' for e in extensions]
        
        if rule.operator == RuleOperator.EQUALS:
            return ext in extensions
        elif rule.operator == RuleOperator.CONTAINS:
            return any(e in ext for e in extensions)
        
        return ext in extensions
    
    def _evaluate_content_rule(self, rule: OrganizationRule, file_path: Path) -> bool:
        """Evaluate content keyword rule."""
        # Only check text files
        text_extensions = {'.txt', '.md', '.py', '.js', '.html', '.css', '.json',
                          '.xml', '.csv', '.log', '.ini', '.yaml', '.yml', '.rst'}
        
        if file_path.suffix.lower() not in text_extensions:
            return False
        
        # Check cache
        if file_path in self._content_cache:
            content = self._content_cache[file_path]
        else:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(10000)  # Read first 10KB
                self._content_cache[file_path] = content
            except:
                return False
        
        keyword = rule.value
        if not rule.case_sensitive:
            content = content.lower()
            keyword = keyword.lower()
        
        if rule.operator == RuleOperator.CONTAINS:
            return keyword in content
        elif rule.operator == RuleOperator.EQUALS:
            return content == keyword
        elif rule.operator == RuleOperator.MATCHES_REGEX:
            flags = 0 if rule.case_sensitive else re.IGNORECASE
            return bool(re.search(keyword, content, flags))
        
        return False
    
    def _evaluate_size_rule(self, rule: OrganizationRule, file_path: Path) -> bool:
        """Evaluate file size rule."""
        try:
            size = file_path.stat().st_size
            value = self._parse_size(rule.value)
            
            if rule.operator == RuleOperator.GREATER_THAN:
                return size > value
            elif rule.operator == RuleOperator.LESS_THAN:
                return size < value
            elif rule.operator == RuleOperator.EQUALS:
                return size == value
            elif rule.operator == RuleOperator.BETWEEN:
                value2 = self._parse_size(rule.value2) if rule.value2 else 0
                return value <= size <= value2
        except:
            return False
        
        return False
    
    def _evaluate_date_rule(self, rule: OrganizationRule, file_path: Path,
                           date_type: str) -> bool:
        """Evaluate date-based rule."""
        try:
            stat = file_path.stat()
            
            if date_type == 'modified':
                file_date = datetime.fromtimestamp(stat.st_mtime)
            elif date_type == 'created':
                # Use st_birthtime on macOS, fallback to st_ctime
                timestamp = getattr(stat, 'st_birthtime', stat.st_ctime)
                file_date = datetime.fromtimestamp(timestamp)
            else:
                return False
            
            # Parse rule value
            if isinstance(rule.value, str):
                # Relative date like "7_days_ago", "1_month_ago"
                compare_date = self._parse_relative_date(rule.value)
            else:
                compare_date = rule.value
            
            if rule.operator == RuleOperator.GREATER_THAN:
                return file_date > compare_date
            elif rule.operator == RuleOperator.LESS_THAN:
                return file_date < compare_date
            elif rule.operator == RuleOperator.EQUALS:
                return file_date.date() == compare_date.date()
            elif rule.operator == RuleOperator.BETWEEN:
                if isinstance(rule.value2, str):
                    compare_date2 = self._parse_relative_date(rule.value2)
                else:
                    compare_date2 = rule.value2
                return compare_date <= file_date <= compare_date2
                
        except Exception as e:
            self.logger.warning(f"Error evaluating date rule: {e}")
            return False
        
        return False
    
    def _parse_size(self, size_str: Union[str, int]) -> int:
        """Parse size string to bytes."""
        if isinstance(size_str, (int, float)):
            return int(size_str)
        
        size_str = str(size_str).strip().upper()
        
        # Check for multi-character suffixes first (order matters!)
        multipliers = [
            ('TB', 1024 ** 4),
            ('GB', 1024 ** 3),
            ('MB', 1024 ** 2),
            ('KB', 1024),
            ('B', 1),
        ]
        
        for suffix, multiplier in multipliers:
            if size_str.endswith(suffix):
                number = size_str[:-len(suffix)].strip()
                try:
                    return int(float(number) * multiplier)
                except ValueError:
                    continue
        
        # Assume bytes if no suffix
        return int(float(size_str))
    
    def _parse_relative_date(self, date_str: str) -> datetime:
        """Parse relative date string."""
        date_str = date_str.lower().replace('_', ' ')
        
        # Patterns like "7 days ago", "1 month ago", "today", "yesterday"
        now = datetime.now()
        
        if date_str == 'today':
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_str == 'yesterday':
            return now - timedelta(days=1)
        
        # Try to parse "X days/months/years ago"
        parts = date_str.split()
        if len(parts) >= 3 and parts[2] == 'ago':
            try:
                amount = int(parts[0])
                unit = parts[1].rstrip('s')  # Remove plural 's'
                
                if unit == 'day':
                    return now - timedelta(days=amount)
                elif unit == 'week':
                    return now - timedelta(weeks=amount)
                elif unit == 'month':
                    return now - timedelta(days=amount * 30)
                elif unit == 'year':
                    return now - timedelta(days=amount * 365)
            except:
                pass
        
        # Default to now
        return now
    
    def _apply_name_pattern(self, pattern: str, file_path: Path, 
                           rule: OrganizationRule) -> str:
        """Apply a rename pattern to generate new filename."""
        # Available variables:
        # {original_name} - Original filename without extension
        # {original_ext} - Original file extension
        # {category} - Target category
        # {date} - Current date (YYYYMMDD)
        # {datetime} - Current datetime (YYYYMMDD_HHMMSS)
        # {counter} - Auto-incrementing counter
        
        variables = {
            'original_name': file_path.stem,
            'original_ext': file_path.suffix,
            'category': rule.target_category,
            'date': datetime.now().strftime('%Y%m%d'),
            'datetime': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'counter': '001'  # Would need state to track actual counter
        }
        
        result = pattern
        for var, value in variables.items():
            result = result.replace(f'{{{var}}}', str(value))
        
        # Ensure extension
        if not result.endswith(file_path.suffix):
            result += file_path.suffix
        
        return result
    
    def save_to_file(self, filepath: Union[str, Path]) -> None:
        """Save rules to JSON file."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'version': '1.0',
            'rules': [rule.to_dict() for rule in self.rules]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.logger.info(f"Saved {len(self.rules)} rules to {filepath}")
    
    def load_from_file(self, filepath: Union[str, Path]) -> None:
        """Load rules from JSON file."""
        filepath = Path(filepath)
        
        if not filepath.exists():
            self.logger.warning(f"Rules file not found: {filepath}")
            return
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.rules = [OrganizationRule.from_dict(r) for r in data.get('rules', [])]
        self.logger.info(f"Loaded {len(self.rules)} rules from {filepath}")
    
    def get_rules(self, enabled_only: bool = False) -> List[OrganizationRule]:
        """Get all rules, optionally filtering by enabled status."""
        if enabled_only:
            return [r for r in self.rules if r.enabled]
        return self.rules.copy()
    
    def clear_rules(self) -> None:
        """Remove all rules."""
        self.rules = []
        self.logger.info("All rules cleared")
