# Course Creator Roadmap

## Overview
This document tracks the development roadmap for the adaptive-latin course creation platform, including completed features, work in progress, and planned additions.

---

## ✅ Completed Features

### Core Course Creation Wizard
- **5-Step Wizard Flow**
  - Step 1: Course Setup (title, domain, description, target audience, taxonomy selection)
  - Step 2: Module Planner (create modules with learning outcomes and concepts)
  - Step 3: Resource Library (attach external sources with verification requirements)
  - Step 4: Content Editor (build teaching content for each concept)
  - Step 5: Review & Publish (preview and finalize course)

### Import/Export System
- **JSON Import/Export** ✅
  - Export complete course structure to JSON file
  - Import previously exported courses
  - Preserves all metadata, modules, concepts, and learning outcomes
  - Client-side download with timestamped filenames

- **AI Syllabus Parser** ✅
  - Upload `.txt` or `.pdf` syllabus files
  - Claude AI extracts course structure automatically
  - Generates modules, concepts, and learning outcomes
  - Supports Bloom's and Fink's taxonomy frameworks
  - Error handling with helpful user feedback

### UX Enhancements
- **Progress Indicators** ✅
  - Visual step progress with numbered circles
  - Completed steps show green checkmarks
  - Active step highlighted

- **Auto-save System** ✅
  - Automatic draft saving every 3 seconds after changes
  - Debounced to prevent excessive saves
  - Persistent storage using localStorage
  - Subtle timestamp indicator (top-left)

- **Toast Notifications** ✅
  - Success messages for manual saves
  - Auto-hide after 3 seconds
  - Dismissible with close button

- **Validation** ✅
  - Required field validation
  - Error messages for incomplete data
  - Comprehension quiz validation for required materials

### External Resource Management
- **Multi-level Resource Attachment** ✅
  - Attach resources to entire course or specific concepts
  - Support for videos, PDFs, websites, images
  - Auto-detection of resource types

- **Requirement Levels** ✅
  - Optional (supplementary)
  - Recommended (strongly suggested)
  - Required (must complete before proceeding)

- **Verification Methods** ✅ (for required materials)
  - No verification (honor system)
  - Self-attestation (checkbox confirmation)
  - Comprehension quiz (multi-question assessment)
  - Discussion prompt (reflective response)

---

## 🚧 In Progress

### Draft Management
- Load previously saved drafts from localStorage
- Draft recovery UI with timestamp display
- "Resume from draft" option on initial choice screen

---

## 📋 Planned Features

### Content Import Options

#### 1. Markdown Content Import
**Priority**: High
**Description**: Bulk import teaching content from markdown files
- Upload markdown files for multiple concepts
- Auto-detect concept titles from headers
- Preserve formatting and embedded media
- Map files to existing concept structure

#### 2. CSV Bulk Import
**Priority**: Medium
**Description**: Import course structure from spreadsheet
- Define columns: Module, Concept, Learning Objectives, Prerequisites
- Validate data before import
- Preview mapped structure
- Support for both module-based and flat structures

#### 3. Clone Existing Course
**Priority**: High
**Description**: Duplicate course as template for modifications
- Select existing course to clone
- Option to include/exclude content vs. just structure
- Rename and modify metadata
- Useful for creating course variants

#### 4. Google Docs Integration
**Priority**: Low
**Description**: Import content directly from Google Drive
- OAuth integration with Google Drive
- Select Google Docs for course content
- Extract formatted text and images
- Real-time sync option

#### 5. Video Transcript Parser
**Priority**: Medium
**Description**: Extract learning objectives from video transcripts
- Upload video transcript files
- AI extraction of key concepts and objectives
- Suggested module structure based on topics
- Integration with YouTube API for auto-transcript fetch

### Export Enhancements

#### 6. SCORM Package Export
**Priority**: High
**Description**: Package course for LMS compatibility
- Generate SCORM 1.2 or 2004 packages
- Include all content and assessments
- Tracking and completion data structure
- Compatible with Canvas, Moodle, Blackboard

#### 7. PDF Export
**Priority**: Medium
**Description**: Generate printable course outline/syllabus
- Professional formatting
- Include CLOs, MLOs, learning objectives
- Module structure and concept progression
- Resource list with URLs
- Customizable template

#### 8. Markdown Export
**Priority**: Medium
**Description**: Export all teaching content as markdown files
- One file per concept
- Organized folder structure by module
- Include metadata as frontmatter
- Useful for version control and editing

### LMS Integration

#### 9. Canvas LMS Import
**Priority**: High
**Description**: Import from Canvas Common Cartridge
- Parse .imscc files
- Extract modules, assignments, pages
- Map to internal course structure
- Preserve learning outcomes

#### 10. Moodle Backup Import
**Priority**: Medium
**Description**: Import from Moodle backup files
- Parse .mbz backup files
- Extract course structure and content
- Map activities to concepts
- Import quiz questions

### Advanced AI Features

#### 11. Learning Outcome Generator
**Priority**: High
**Description**: AI-assisted generation of learning outcomes
- Suggest CLOs based on course description
- Generate MLOs for each module
- Ensure alignment with chosen taxonomy
- Bloom's/Fink's level verification

#### 12. Concept Dependency Analyzer
**Priority**: Medium
**Description**: AI analysis of concept relationships
- Suggest prerequisite chains
- Identify circular dependencies
- Recommend optimal sequencing
- Visualize concept graph

#### 13. Content Gap Detection
**Priority**: Medium
**Description**: Identify missing content in course structure
- Compare CLOs to module coverage
- Flag concepts without teaching content
- Suggest areas needing expansion
- Assessment coverage analysis

### Collaboration Features

#### 14. Multi-user Course Editing
**Priority**: Low
**Description**: Collaborative course development
- Role-based permissions (owner, editor, reviewer)
- Real-time collaborative editing
- Change tracking and version history
- Comment threads on specific sections

#### 15. Template Library
**Priority**: Medium
**Description**: Shared course templates
- Community-contributed course structures
- Domain-specific templates (business, science, humanities)
- Preview before applying
- Rating and review system

### Quality Assurance

#### 16. Course Quality Checklist
**Priority**: High
**Description**: Automated quality checks before publishing
- Verify all concepts have content
- Check learning outcome alignment
- Ensure prerequisite chains are valid
- Flag potential accessibility issues
- Estimate time-to-completion

#### 17. Accessibility Validator
**Priority**: High
**Description**: WCAG 2.1 AA compliance checking
- Scan all teaching content
- Check external resource URLs
- Alt text verification
- Reading level analysis
- Color contrast checks

### User Experience

#### 18. Guided Tour
**Priority**: Low
**Description**: Interactive onboarding for new users
- Step-by-step walkthrough
- Contextual help tooltips
- Sample course demonstration
- Best practices guide

#### 19. Keyboard Navigation
**Priority**: Medium
**Description**: Full keyboard accessibility
- Tab navigation through wizard
- Keyboard shortcuts for common actions
- Focus indicators
- Screen reader optimization

#### 20. Dark Mode
**Priority**: Low
**Description**: Dark theme option
- Toggle between light/dark themes
- Preserve user preference
- Accessible color contrasts in both modes

---

## 🎯 Next Sprint Priorities

Based on user needs and development effort, the recommended next features to implement are:

1. **Draft Recovery UI** (In Progress) - Complete the auto-save feature with user-facing recovery
2. **Clone Existing Course** - High value, moderate effort
3. **Learning Outcome Generator** - Leverage existing AI integration
4. **Course Quality Checklist** - Critical for ensuring course completeness
5. **SCORM Package Export** - High demand for LMS compatibility

---

## 📊 Feature Categorization

### Quick Wins (High Value, Low Effort)
- Draft Recovery UI
- PDF Export
- Markdown Export
- Course Quality Checklist

### Strategic Investments (High Value, High Effort)
- SCORM Package Export
- Canvas LMS Import
- Learning Outcome Generator
- Concept Dependency Analyzer

### Nice to Have (Medium Value, Low Effort)
- Dark Mode
- Guided Tour
- Keyboard Navigation

### Future Considerations (Lower Priority)
- Multi-user Editing
- Google Docs Integration
- Moodle Backup Import

---

## 🤝 Contributing Ideas

Have ideas for new features? Consider:
- **Impact**: How many users benefit?
- **Alignment**: Does it serve the adaptive learning mission?
- **Feasibility**: Can it be built with existing infrastructure?
- **Maintenance**: What ongoing support is required?

---

**Last Updated**: 2025-11-16
**Version**: 1.0
