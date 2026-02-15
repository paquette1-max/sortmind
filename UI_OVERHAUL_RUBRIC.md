# File Organizer World-Class UI Overhaul - Internal Rubric

## Quality Categories (1-5 Scale)

### 1. Code Correctness (Weight: 25%)
- **5**: All functionality works, no bugs, handles edge cases gracefully
- **4**: Minor edge cases not covered but core functionality solid
- **3**: Some functionality issues but mostly works
- **2**: Significant bugs affecting usability
- **1**: Broken or non-functional

**Specific Requirements:**
- [ ] File count shows only selected directory (not recursive)
- [ ] Table selection properly connects to preview panel
- [ ] All buttons work as expected
- [ ] Error handling prevents crashes
- [ ] Keyboard navigation works throughout

### 2. World-Class UI Implementation (Weight: 25%)
- **5**: All 7 pillars implemented flawlessly, feels professional
- **4**: Most pillars implemented well, minor polish needed
- **3**: Basic implementation of key pillars
- **2**: Some UI improvements but not world-class
- **1**: Poor UI quality

**7 Pillars Checklist:**
- [ ] Cognitive Load Reduction (progressive disclosure, smart defaults)
- [ ] Micro-interactions & Feedback Loops (hover states, loading feedback)
- [ ] Visual Hierarchy & Information Architecture (8-point grid, typography)
- [ ] Accessibility (WCAG 2.1 AA, keyboard nav, screen reader support)
- [ ] Consistency & Platform Conventions (macOS/Windows)
- [ ] Error Prevention & Recovery (helpful messages, inline validation)
- [ ] Performance Perception (skeleton screens, perceived speed)

### 3. Specific UI Fixes (Weight: 20%)
- **5**: All 8 specific fixes implemented perfectly
- **4**: 6-7 fixes implemented well
- **3**: 4-5 fixes implemented
- **2**: 2-3 fixes implemented
- **1**: 0-1 fixes implemented

**Required Fixes:**
- [ ] 1. File count shows only selected directory
- [ ] 2. Column headers clear with tooltips
- [ ] 3. Results table → preview panel connection
- [ ] 4. Helpful empty states
- [ ] 5. Button tooltips explaining actions
- [ ] 6. Informative status messages
- [ ] 7. Consistent spacing and visual hierarchy
- [ ] 8. Helpful error messages (not cryptic)

### 4. Code Quality (Weight: 15%)
- **5**: Clean, maintainable, well-documented, no hardcoded values
- **4**: Good quality, minor issues
- [ ] Meaningful variable names
- [ ] Proper separation of concerns
- [ ] No magic numbers/strings
- [ ] Consistent style
- [ ] Security: proper path validation

### 5. Testing & Verification (Weight: 15%)
- **5**: All flows tested, edge cases covered, accessibility verified
- **4**: Most flows tested, minor gaps
- [ ] UI flows tested manually
- [ ] Edge cases handled (empty folder, many files, errors)
- [ ] Accessibility verified (keyboard nav, contrast)
- [ ] Performance check (no hanging)

## Scoring
- Total possible: 100 points
- 90-100: World-class delivery
- 80-89: Excellent
- 70-79: Good
- 60-69: Acceptable
- <60: Needs revision

## Target Score: 90+ (World-Class)

## Implementation Phases

### Phase 1: Architect Review ✓ (COMPLETE)
- Reviewed current UI architecture
- Identified structural issues
- Key findings:
  - MainWindow has good structure but needs empty states
  - ResultsTable has selection → preview signal already
  - ScanWorker already uses glob() (not rglob) - bug is fixed
  - QSS styling is comprehensive but needs refinement
  - Missing: skeleton screens, empty states, keyboard shortcuts

### Phase 2: Vesper UI Redesign
- Design empty state components
- Plan keyboard navigation improvements
- Design skeleton screen for loading
- Plan accessibility enhancements

### Phase 3: Coder Implementation
- Implement empty states
- Add skeleton loading widget
- Enhance keyboard navigation
- Add comprehensive tooltips
- Improve error messages

### Phase 4: Tester Verification
- Test all UI flows
- Verify keyboard navigation
- Check accessibility
- Performance testing

### Phase 5: Guardian Review
- Code quality check
- Security review
- Final polish

## Deliverables Checklist
- [ ] Updated MainWindow with empty states
- [ ] Updated ResultsTable with better selection handling
- [ ] Skeleton loading widget
- [ ] Enhanced tooltips throughout
- [ ] Improved error messages
- [ ] Keyboard navigation support
- [ ] Accessibility improvements
- [ ] Updated QSS styles
- [ ] Documentation updates
