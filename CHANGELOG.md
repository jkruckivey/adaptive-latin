# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2025-11-01

### Added
- Professional backend architecture layer with modular routers (concepts, conversations, learners)
- Database abstraction layer (`database.py`) with SQLite support for learners and conversations
- JWT-based authentication infrastructure (`auth.py`) with OAuth2 bearer tokens
- Pydantic schemas (`schemas.py`) for API request/response validation
- Course syllabus and concept map visualization component with 484 lines of polished CSS
- Canvas design skill with 40+ professional fonts for visual content generation
- Stone inscription feature for authentic Latin text rendering
- Test HTML files for interactive widgets (declension-explorer, scenario, word-order)
- Security improvements with `sanitize_user_input()` function to prevent prompt injection attacks
- Enhanced ParadigmTable styling with gradients, hover effects, and color-coded cases (267 lines)
- Module Learning Outcomes (MLOs) metadata for all 7 concepts
- Course-level Learning Outcomes (CLOs) in course metadata
- Integration test plan documentation (`INTEGRATION-TEST-PLAN.md`)
- Ivey adaptation notes documentation (`IVEY-ADAPTATION-NOTES.md`)

### Changed
- Updated all concept metadata files with module learning outcomes
- Applied input sanitization to question_context handling in remediate and reinforce stages
- Enhanced settings with additional auto-approved commands for development workflow

### Fixed
- Resolved 68-commit divergence between local and remote branches
- Maintained API reliability features (retry logic with exponential backoff)
- Preserved video content filtering and dialogue response evaluation

### Security
- Added prompt injection protection via `sanitize_user_input()` function
- Sanitizes scenarios, questions, answers, and options before AI prompt inclusion
- Escapes common injection patterns (code fences, XML tags, instruction delimiters)
- Limits consecutive special characters to prevent pattern-based attacks

## [0.2.0] - 2025-10-30

### Added
- Robust error handling and retry logic for Anthropic API calls with exponential backoff
- Learner-facing verification interfaces for required materials
- Backend integration for course creation with required materials
- Required materials and verification methods to Resource Library
- Quality Matters standards integration with Bloom's and Fink's taxonomies
- Intelligent content caching system to reduce AI generation costs
- PDF text extraction capability with pdfplumber
- External source integration for course creation
- Multi-course backend support
- Curriculum roadmap visualizer for course creation
- Frontend course creation wizard (MVP Level 1)
- Comprehensive course creation requirements documentation

### Changed
- Improved CORS policy to allow PUT requests for learning style updates
- Implemented sliding window scoring for mastery calculation
- Enhanced debug panel with mastery tracking

### Fixed
- Fixed pre-generation script and added cache DB to gitignore
- Resolved CORS issues for learning style preference updates
- Fixed critical peer review issues for crash prevention and UX improvements
- Corrected validation errors when confidence tracking is disabled
- Fixed concept_id attribute error in dialogue questions
- Resolved learning style mapping mismatch between frontend and backend

## [0.1.0] - 2025-10-24

### Added
- Initial adaptive Latin grammar learning platform
- AI-powered personalized tutoring system using Anthropic Claude
- Onboarding flow with learner profiling (learning style, prior knowledge, interests)
- Mastery-based progression through 7 Latin grammar concepts
- Confidence calibration system (1-4 star ratings)
- Interactive content types (paradigm tables, fill-blank exercises, examples)
- Assessment types (multiple-choice, dialogue, written, applied tasks)
- Learner progress tracking and mastery calculation
- Spaced repetition scheduling for review
- Debug panel for development and testing
- Render.yaml configuration for deployment

### Changed
- Disabled dialogue questions by default
- Always show progress bar for better learner feedback
- Minimum 3 assessments required before displaying mastery metrics

### Fixed
- Fixed deployment issues on Render platform
- Added missing slowapi dependency for rate limiting
- Resolved missing react-markdown dependency
- Fixed duplicate slowapi dependency conflict
- Corrected onboarding flow being skipped when profile doesn't exist
- Fixed issue where adaptive next content recommendations were ignored

[Unreleased]: https://github.com/jkruckivey/adaptive-latin/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/jkruckivey/adaptive-latin/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/jkruckivey/adaptive-latin/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/jkruckivey/adaptive-latin/releases/tag/v0.1.0
