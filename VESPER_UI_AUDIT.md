# 🎨 Vesper UI Audit Report
## AI File Organizer - Design System Review

**Auditor:** Vesper (UI Specialist Agent)  
**Date:** 2026-02-14  
**Status:** ⚠️ Issues Found - Fixes Required  
**Overall Grade:** B+ (Good foundation, needs polish)

---

## Executive Summary

The AI File Organizer has a solid foundation with the dark theme QSS in place. However, several components have **hardcoded light-theme colors** that override the dark theme, creating visual inconsistency. The QSS is comprehensive but not fully utilized due to missing object names and inline styles.

**Critical Finding:** The PreviewPanel has light-theme hardcoded colors that clash with the dark theme.

---

## 🚨 P0 - Critical Issues (Must Fix)

### 1. PreviewPanel Hardcoded Light Theme Colors
**File:** `src/ui/widgets/preview_panel.py`

**Issues Found:**
```python
# Line 44-50 - Header label has light theme colors
self.header_label.setStyleSheet("""
    font-weight: bold;
    font-size: 12px;
    color: #333;                    # ❌ Dark text on dark bg!
    padding: 5px;
    background-color: #f0f0f0;      # ❌ Light background!
    border-radius: 4px;
""")

# Line 57-62 - Metadata label
self.metadata_label.setStyleSheet("""
    font-size: 10px;
    color: #666;                    # ❌ Gray text
    padding: 5px;
""")

# Line 66 - Separator
separator.setStyleSheet("background-color: #ddd;")  # ❌ Light border

# Line 73-78 - Scroll area
self.scroll_area.setStyleSheet("""
    QScrollArea {
        border: 1px solid #ddd;     # ❌ Light border
        border-radius: 4px;
        background-color: white;    # ❌ White background!
    }
""")

# Line 85-90 - Text preview
self.text_preview.setStyleSheet("""
    QTextEdit {
        border: none;
        background-color: #fafafa;  # ❌ Off-white
    }
""")

# Line 95-100 - Image label
self.image_label.setStyleSheet("""
    QLabel {
        border: none;
        background-color: #f5f5f5;  # ❌ Light gray
    }
""")

# Line 104-110 - Error label (OK - semantic color)
# Line 138-143 - Type label
self.type_label.setStyleSheet("""
    font-size: 9px;
    color: #999;                    # ❌ Light gray text
    padding: 2px;
""")
```

**Fix Required:**
Remove ALL hardcoded styles from PreviewPanel. The dark_theme.qss already handles these. If specific styling is needed, use design system colors:

```python
# CORRECT: Remove inline styles, let QSS handle it
# OR use design system colors:
"""
color: #FAFAFA;                    # ✅ Primary text
background-color: #262626;         # ✅ Tertiary background
border: 1px solid #404040;         # ✅ Border color
"""
```

---

### 2. ResultsTable Hardcoded Confidence Colors
**File:** `src/ui/widgets/results_table.py`

**Lines 77-85:**
```python
# Color code confidence
if confidence >= 0.85:
    confidence_item.setBackground(QColor("#90EE90"))  # ❌ Light green
    confidence_item.setForeground(QColor("#006400"))  # ❌ Dark green
elif confidence >= 0.70:
    confidence_item.setBackground(QColor("#FFD700"))  # ❌ Gold
    confidence_item.setForeground(QColor("#8B6914"))  # ❌ Dark goldenrod
else:
    confidence_item.setBackground(QColor("#FFB6C6"))  # ❌ Light red
    confidence_item.setForeground(QColor("#8B0000"))  # ❌ Dark red
```

**Fix Required:**
Use design system semantic colors:
```python
if confidence >= 0.85:
    confidence_item.setBackground(QColor("#22C55E"))  # ✅ Success green
    confidence_item.setForeground(QColor("#0F0F0F"))  # ✅ Dark text
elif confidence >= 0.70:
    confidence_item.setBackground(QColor("#F59E0B"))  # ✅ Warning amber
    confidence_item.setForeground(QColor("#0F0F0F"))  # ✅ Dark text
else:
    confidence_item.setBackground(QColor("#EF4444"))  # ✅ Error red
    confidence_item.setForeground(QColor("#FAFAFA"))  # ✅ Light text
```

---

## ⚠️ P1 - High Priority Issues

### 3. ProgressDialog Hardcoded Styles
**File:** `src/ui/widgets/progress_dialog.py`

**Lines 30, 40, 44:**
```python
self.title_label.setStyleSheet("font-weight: bold; font-size: 12px;")  # OK
self.status_label.setStyleSheet("color: #666; font-size: 10px;")       # ❌ Gray
self.file_label.setStyleSheet("color: #666; font-size: 10px;")         # ❌ Gray
```

**Fix:** Use `--color-text-secondary: #A3A3A3`

---

### 4. MainWindow Minor Hardcoded Padding
**File:** `src/ui/main_window.py`

**Line 56:**
```python
self.dir_label.setStyleSheet("padding: 8px; border-radius: 4px;")  # ⚠️ OK but consider removing
```

**Recommendation:** Remove inline style and use QSS:
```css
/* Add to dark_theme.qss */
QLabel#directoryLabel {
    padding: 8px;
    border-radius: 4px;
    background-color: #1A1A1A;
}
```

Then set object name:
```python
self.dir_label.setObjectName("directoryLabel")
```

---

### 5. Missing Button Object Names
**File:** `src/ui/main_window.py`

**Lines 75, 79:**
```python
self.analyze_btn.setObjectName("primaryButton")   # ✅ Good
self.organize_btn.setObjectName("primaryButton")  # ✅ Good
```

**But:** The QSS defines these IDs:
```css
QPushButton#secondaryButton { }
QPushButton#dangerButton { }
QPushButton#ghostButton { }
```

**Issue:** The "Browse..." button and toolbar buttons don't have object names.

**Fix:** Add appropriate object names:
```python
browse_btn.setObjectName("secondaryButton")
```

---

## 💡 P2 - Polish & Improvements

### 6. SettingsDialog Tab Styling
**File:** `src/ui/dialogs/settings_dialog.py`

The settings dialog uses default Qt tab styling. Consider adding tab-specific styles to QSS:
```css
QTabWidget::pane {
    border: 1px solid #262626;
    border-radius: 6px;
    background-color: #1A1A1A;
}

QTabBar::tab {
    background-color: #262626;
    color: #A3A3A3;
    padding: 10px 20px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}

QTabBar::tab:selected {
    background-color: #1A1A1A;
    color: #FAFAFA;
}
```

---

### 7. Add Application Font
**File:** `src/main.py`

Add Inter font to the application:
```python
from PyQt6.QtGui import QFont, QFontDatabase

# Load Inter font
font_db = QFontDatabase()
font_id = font_db.addApplicationFont(":/fonts/Inter-Regular.ttf")
if font_id != -1:
    font_family = font_db.applicationFontFamilies(font_id)[0]
    app.setFont(QFont(font_family, 10))
```

Or use system fonts:
```python
app.setFont(QFont("Inter, -apple-system, system-ui, sans-serif", 10))
```

---

### 8. Empty State Styling
The results table shows empty when no files are analyzed. Consider adding an empty state widget:

```python
# Add to MainWindow
self.empty_state = QLabel("Select a directory to begin analyzing files")
self.empty_state.setObjectName("emptyState")
self.empty_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
```

With QSS:
```css
QLabel#emptyState {
    color: #737373;
    font-size: 14px;
    padding: 40px;
}
```

---

### 9. Confidence Column Visual Polish
Instead of background colors for confidence, consider:
- Progress bar style indicator
- Colored text with icons (✓, ~, ✗)
- Color-coded badges

Example:
```python
# Use text with emoji indicators
if confidence >= 0.85:
    confidence_item.setText(f"✓ {confidence:.0%}")
    confidence_item.setForeground(QColor("#22C55E"))
elif confidence >= 0.70:
    confidence_item.setText(f"~ {confidence:.0%}")
    confidence_item.setForeground(QColor("#F59E0B"))
else:
    confidence_item.setText(f"✗ {confidence:.0%}")
    confidence_item.setForeground(QColor("#EF4444"))
```

---

## ✅ What's Working Well

1. **Dark Theme QSS** - Comprehensive and well-structured
2. **Button Object Names** - Primary buttons correctly tagged
3. **Main Window Layout** - Clean splitter-based layout
4. **Menu Bar** - Properly using QMenuBar QSS
5. **Status Bar** - Using correct dark theme colors
6. **Results Table Structure** - Good column configuration
7. **Progress Dialog** - Clean modal implementation

---

## 🛠️ Fix Implementation Priority

### Phase 1: Critical (Do First)
1. Fix PreviewPanel hardcoded colors
2. Update ResultsTable confidence colors

### Phase 2: High Priority
3. Fix ProgressDialog label colors
4. Add Browse button object name
5. Set directory label object name

### Phase 3: Polish
6. Add Inter font
7. Add empty state styling
8. Improve confidence indicators

---

## 📝 Code Fix Files

### File 1: preview_panel.py
**Action:** Remove all hardcoded setStyleSheet calls
**Lines to modify:** 44-50, 57-62, 66, 73-78, 85-90, 95-100, 138-143
**Approach:** Either remove entirely (let QSS handle) or use design system colors

### File 2: results_table.py  
**Action:** Update confidence color coding
**Lines to modify:** 77-85
**Approach:** Use semantic colors from design system

### File 3: progress_dialog.py
**Action:** Update label colors
**Lines to modify:** 40, 44
**Approach:** Use #A3A3A3 for secondary text

### File 4: main_window.py
**Action:** Add object names
**Lines to modify:** 55, 57
**Approach:** Set objectName for QSS targeting

---

## 🎯 Design System Compliance

| Component | Status | Notes |
|-----------|--------|-------|
| Color Palette | ⚠️ | Hardcoded light colors in PreviewPanel |
| Typography | ⚠️ | Using system fonts, not Inter |
| Buttons | ✅ | Primary/Secondary variants exist |
| Inputs | ✅ | Styled via QSS |
| Tables | ✅ | Good structure, needs color fix |
| Spacing | ✅ | 4px grid followed |
| Icons | N/A | Text-based currently |

---

## ✍️ Sign-off

**Status:** ⚠️ **CONDITIONAL APPROVAL**

The UI foundation is solid, but **P0 issues must be fixed** before final approval:

1. ✅ Dark theme QSS is comprehensive
2. ✅ Component structure is good
3. ❌ PreviewPanel has light-theme hardcoded colors
4. ❌ ResultsTable uses non-design-system colors

**Required for Full Approval:**
- [ ] Fix PreviewPanel hardcoded styles
- [ ] Update ResultsTable confidence colors
- [ ] Verify all components in dark mode

**Approved for:** Development / Testing  
**Not Approved for:** Production release (until P0 fixes)

---

*Report generated by Vesper 🎨 - UI Specialist Agent*
