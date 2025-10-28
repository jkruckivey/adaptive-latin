# Course Creation Requirements & Design

## Executive Summary

This document analyzes the current Latin grammar course structure to identify what information and content is needed to enable users to create their own adaptive learning courses.

---

## Current Course Anatomy

### Structure Overview
```
resource-bank/
└── latin-grammar/                    # Domain
    ├── concept-001/                  # Individual concept
    │   ├── metadata.json             # Concept metadata
    │   ├── resources/
    │   │   ├── text-explainer.md     # Teaching content (244 lines)
    │   │   └── examples.json         # Structured examples
    │   └── assessments/
    │       ├── dialogue-prompts.json # Conversational questions
    │       ├── written-prompts.json  # Essay/explanation prompts
    │       └── applied-tasks.json    # Application exercises
    └── concept-002/
        └── [same structure]
```

### 1. Concept Metadata (`metadata.json`)

**Required Fields:**
- `id` - Unique identifier (e.g., "concept-001")
- `title` - Human-readable concept name
- `domain` - Subject area (e.g., "latin-grammar")
- `difficulty` - Numeric difficulty (1-10)
- `prerequisites` - Array of concept IDs that must be completed first
- `learning_objectives` - Array of specific, measurable objectives
- `estimated_mastery_time` - Time estimate for completion
- `available_resource_types` - Types of teaching resources provided
- `assessment_types` - Types of assessments available
- `tags` - Searchable/filterable tags
- `vocabulary` - Key terms/concepts for this concept

**Example:**
```json
{
  "id": "concept-001",
  "title": "First Declension Nouns + Sum, esse (present)",
  "domain": "latin-grammar",
  "difficulty": 1,
  "prerequisites": [],
  "learning_objectives": [
    "Identify first declension nouns by their nominative singular ending (-a)",
    "Decline first declension nouns in all cases (singular and plural)",
    "Explain the function of each case (nominative, genitive, dative, accusative, ablative)"
  ],
  "estimated_mastery_time": "60-90 minutes",
  "available_resource_types": ["text", "examples"],
  "assessment_types": ["dialogue", "written", "applied"],
  "tags": ["foundational", "declension", "noun-system"],
  "vocabulary": [
    {"latin": "puella, puellae", "english": "girl", "gender": "f"},
    {"latin": "via, viae", "english": "road, way", "gender": "f"}
  ]
}
```

### 2. Teaching Content (`resources/text-explainer.md`)

**Purpose:** Comprehensive teaching material the AI references when generating content.

**Characteristics:**
- Written in Markdown
- 200-500+ lines typical
- Structured with clear sections
- Includes explanations, examples, memory aids
- Acts as the "textbook" for this concept

**Minimum Requirements:**
- Clear introduction to the concept
- Step-by-step explanations
- At least 3-5 examples
- Practice guidance
- Common mistakes/gotchas

### 3. Structured Examples (`resources/examples.json`)

**Purpose:** Provides structured, domain-specific examples for the AI to reference.

**Structure:**
```json
{
  "examples": [
    {
      "title": "Example 1: Complete Paradigm",
      "description": "Explanation of what this example demonstrates",
      "paradigm": {
        "forms": [
          {
            "form": "puella",
            "function": "Subject",
            "example_sentence": "Puella est.",
            "translation": "The girl is."
          }
        ]
      }
    }
  ]
}
```

**Minimum Requirements:**
- 3-5 complete examples per concept
- Examples should cover main use cases
- Include both simple and complex cases
- Domain-specific structure (flexible JSON)

### 4. Assessment Prompts

**Three Types:**

#### A. Dialogue Prompts (`assessments/dialogue-prompts.json`)
- Conversational questions to check understanding
- Include rubrics for evaluating responses
- AI grades free-text responses

**Structure:**
```json
{
  "prompts": [
    {
      "id": "dialogue-001-1",
      "difficulty": "basic",
      "prompt": "How can you tell if a noun is first declension?",
      "rubric": {
        "excellent": {
          "criteria": ["Mentions -a ending", "Clear explanation"],
          "score_range": "0.90-1.00"
        },
        "good": { /* ... */ },
        "developing": { /* ... */ },
        "insufficient": { /* ... */ }
      }
    }
  ]
}
```

#### B. Written Prompts (`assessments/written-prompts.json`)
- Extended response questions
- Multi-dimensional rubrics (e.g., accuracy, clarity, examples)
- Weighted scoring

#### C. Applied Tasks (`assessments/applied-tasks.json`)
- Specific exercises (translations, problem-solving)
- Clear correct/incorrect answers
- Step-by-step solutions

**Minimum Requirements per Concept:**
- 10-15 dialogue prompts (varying difficulty)
- 5-10 written prompts
- 10-15 applied tasks

---

## Course Creation Requirements

### Level 1: Minimum Viable Course (MVP)

**Course-Level Information:**
1. Course title
2. Domain/subject area
3. Description (what will students learn?)
4. Target audience
5. Number of concepts (minimum 2)

**Per Concept:**
1. Concept title
2. Learning objectives (3-5)
3. Teaching content (markdown text, min 500 words)
4. Key vocabulary/terms (5-10 items)
5. 10 multiple-choice questions with correct answers
6. Prerequisites (if any)

**This enables:**
- Linear progression through concepts
- Basic AI-generated questions
- Mastery tracking
- Adaptive feedback

### Level 2: Enhanced Course

**Adds to MVP:**
- Structured examples (JSON format, 3-5 per concept)
- Dialogue assessment prompts with rubrics
- Written assessment prompts
- Difficulty levels
- Estimated completion times
- Tags for searchability

**This enables:**
- Richer AI-generated content
- Free-text response evaluation
- More varied assessment types
- Better recommendations

### Level 3: Professional Course (Full Feature Set)

**Adds to Enhanced:**
- Multiple resource types (videos, external links)
- Complex prerequisite trees
- Spaced repetition scheduling
- Custom widget types
- Multi-path progression
- Collaborative editing

---

## Proposed Course Creation User Flow

### Phase 1: Course Setup (5-10 minutes)

**Step 1: Basic Information**
```
┌─────────────────────────────────────────┐
│ Create Your Course                      │
├─────────────────────────────────────────┤
│                                         │
│ Course Title: [___________________]    │
│                                         │
│ Subject Area: [Dropdown: Math,         │
│               Science, Language, ...]   │
│                                         │
│ Description:                            │
│ [_________________________________]     │
│ [_________________________________]     │
│                                         │
│ Target Audience:                        │
│ ( ) High School                         │
│ ( ) College                             │
│ ( ) Adult Learners                      │
│ ( ) Self-Learners                       │
│                                         │
│     [Cancel]        [Next: Concepts]    │
└─────────────────────────────────────────┘
```

### Phase 2: Concept Planning (10-15 minutes)

**Step 2: Concept Outline**
```
┌─────────────────────────────────────────┐
│ Plan Your Concepts                      │
├─────────────────────────────────────────┤
│                                         │
│ How many concepts? [_3_]                │
│                                         │
│ Concept 1: [Introduction to Algebra_]  │
│   Prerequisites: None                   │
│                                         │
│ Concept 2: [Linear Equations______]    │
│   Prerequisites: Concept 1              │
│                                         │
│ Concept 3: [Systems of Equations__]    │
│   Prerequisites: Concept 2              │
│                                         │
│ [+ Add Concept]                         │
│                                         │
│     [Back]        [Next: Build Content] │
└─────────────────────────────────────────┘
```

### Phase 3: Content Creation (30-60 min per concept)

**Step 3: For Each Concept**

**Tab 1: Teaching Content**
```
┌─────────────────────────────────────────┐
│ Concept 1: Introduction to Algebra     │
├─────────────────────────────────────────┤
│ [Teaching] [Vocabulary] [Assessments]  │
│                                         │
│ Learning Objectives:                    │
│ 1. [Understand variables____________]  │
│ 2. [Simplify expressions____________]  │
│ 3. [Solve basic equations___________]  │
│ [+ Add Objective]                       │
│                                         │
│ Teaching Content:                       │
│ ┌─────────────────────────────────┐   │
│ │ # Introduction to Algebra        │   │
│ │                                  │   │
│ │ Algebra is the branch of math... │   │
│ │                                  │   │
│ │ [Rich text editor with markdown] │   │
│ │                                  │   │
│ └─────────────────────────────────┘   │
│                                         │
│ 💡 Tip: Include examples, diagrams,   │
│    and practice problems               │
│                                         │
│     [Save Draft]            [Next Tab] │
└─────────────────────────────────────────┘
```

**Tab 2: Vocabulary**
```
┌─────────────────────────────────────────┐
│ Key Terms & Vocabulary                  │
├─────────────────────────────────────────┤
│                                         │
│ Term 1:                                 │
│   Term: [variable_______________]      │
│   Definition: [A letter that represents│
│                a number______________]  │
│                                         │
│ Term 2:                                 │
│   Term: [equation_______________]      │
│   Definition: [A statement that two    │
│                expressions are equal_]  │
│                                         │
│ [+ Add Term]                            │
│                                         │
│     [Back]                  [Next Tab] │
└─────────────────────────────────────────┘
```

**Tab 3: Assessments**
```
┌─────────────────────────────────────────┐
│ Create Assessments                      │
├─────────────────────────────────────────┤
│                                         │
│ Assessment Type: [Multiple Choice ▼]    │
│                                         │
│ Question 1:                             │
│ ┌─────────────────────────────────┐   │
│ │ What is 2x + 3 when x = 4?       │   │
│ └─────────────────────────────────┘   │
│                                         │
│ Options:                                │
│ ( ) 10                                  │
│ (•) 11  ← Correct answer               │
│ ( ) 12                                  │
│ ( ) 13                                  │
│                                         │
│ Explanation (shown if wrong):           │
│ [Substitute x=4: 2(4)+3 = 8+3 = 11_]   │
│                                         │
│ [+ Add Question]                        │
│                                         │
│ Progress: 10/10 questions minimum      │
│                                         │
│     [Save Concept]     [Next Concept] │
└─────────────────────────────────────────┘
```

### Phase 4: Review & Publish (5-10 minutes)

**Step 4: Course Review**
```
┌─────────────────────────────────────────┐
│ Review Your Course                      │
├─────────────────────────────────────────┤
│                                         │
│ ✅ Course Information Complete          │
│ ✅ 3 Concepts Created                   │
│    ├─ Concept 1: Complete (15 Qs)     │
│    ├─ Concept 2: Complete (12 Qs)     │
│    └─ Concept 3: Complete (14 Qs)     │
│                                         │
│ Course Preview:                         │
│ [Launch Preview Mode]                   │
│                                         │
│ Publishing Options:                     │
│ ( ) Private (only you)                  │
│ (•) Unlisted (anyone with link)        │
│ ( ) Public (searchable)                 │
│                                         │
│     [Save as Draft]      [Publish]     │
└─────────────────────────────────────────┘
```

---

## Technical Implementation Considerations

### 1. Storage Architecture

**Option A: File System (Current)**
- Pros: Simple, version control friendly, familiar structure
- Cons: Doesn't scale for many users, no multi-tenancy

**Option B: Database**
- Pros: Better for multi-user, queryable, scalable
- Cons: More complex, requires migration

**Recommendation:** Start with file system for MVP, plan database migration.

**Proposed Structure:**
```
resource-bank/
├── latin-grammar/          # Official course (immutable)
└── user-courses/
    ├── user-123/
    │   └── intro-algebra/
    │       ├── course.json
    │       └── concept-001/
    │           ├── metadata.json
    │           ├── resources/
    │           └── assessments/
    └── user-456/
        └── python-basics/
```

### 2. Validation Requirements

**Course Validation:**
- Minimum 2 concepts
- Each concept has required metadata
- Teaching content meets minimum word count (500 words)
- Minimum 10 assessments per concept
- All learning objectives defined
- Valid JSON structure

**Runtime Validation:**
- `validate_concept_completeness()` already exists
- Extend to validate user-created courses
- Check for minimum viable content before allowing publication

### 3. Backend API Endpoints Needed

```python
# Course Management
POST   /api/courses                      # Create new course
GET    /api/courses/{course_id}          # Get course details
PUT    /api/courses/{course_id}          # Update course
DELETE /api/courses/{course_id}          # Delete course
GET    /api/courses/user/{user_id}       # List user's courses

# Concept Management
POST   /api/courses/{course_id}/concepts           # Add concept
PUT    /api/courses/{course_id}/concepts/{c_id}    # Update concept
DELETE /api/courses/{course_id}/concepts/{c_id}    # Delete concept

# Content Upload
POST   /api/courses/{course_id}/concepts/{c_id}/teaching-content
POST   /api/courses/{course_id}/concepts/{c_id}/vocabulary
POST   /api/courses/{course_id}/concepts/{c_id}/assessments

# Publishing
POST   /api/courses/{course_id}/publish            # Publish course
POST   /api/courses/{course_id}/unpublish          # Unpublish
```

### 4. Frontend Components Needed

```
components/
├── course-creation/
│   ├── CourseSetup.jsx              # Step 1: Basic info
│   ├── ConceptPlanner.jsx           # Step 2: Outline concepts
│   ├── ConceptEditor.jsx            # Step 3: Edit concept
│   │   ├── TeachingContentTab.jsx
│   │   ├── VocabularyTab.jsx
│   │   └── AssessmentsTab.jsx
│   ├── CourseReview.jsx             # Step 4: Review & publish
│   └── ProgressTracker.jsx          # Shows completion status
├── course-library/
│   ├── CourseCard.jsx
│   ├── CourseList.jsx
│   └── CourseSearch.jsx
└── shared/
    ├── MarkdownEditor.jsx
    ├── AssessmentBuilder.jsx
    └── ValidationFeedback.jsx
```

### 5. AI Prompt Adjustments

**Current System:**
- Loads concept resources from `resource-bank/latin-grammar/`
- Injects learning objectives and vocabulary into prompts

**For User Courses:**
- Same structure, different path
- Need to handle potentially lower-quality content
- May need stricter validation or AI "enhancement" step
- Consider AI-assisted content generation tools

---

## MVP Feature Scope (Phase 1)

**In Scope:**
1. ✅ Course creation wizard (4 steps)
2. ✅ Basic concept editor (title, objectives, teaching content)
3. ✅ Vocabulary management
4. ✅ Multiple-choice question builder
5. ✅ Course validation
6. ✅ Save drafts
7. ✅ Publish courses (unlisted only)
8. ✅ Backend API for CRUD operations
9. ✅ File-based storage in `user-courses/`

**Out of Scope (Future):**
- Public course marketplace
- Collaborative editing
- Rich media uploads (videos, images)
- Advanced assessment types
- Analytics/usage stats
- Course versioning
- Import/export

---

## Success Metrics

**Course Creator Perspective:**
- Time to create first concept: < 45 minutes
- Completion rate of course wizard: > 70%
- Published courses per active creator: 2+

**Learner Perspective:**
- User-created courses achieve similar mastery rates as Latin course
- AI-generated content quality acceptable (manual review initially)
- Drop-off rate comparable to official courses

---

## Questions for Discussion

1. **Pricing Model:** Should course creation be:
   - Free for all users?
   - Paid feature?
   - Free with limits (e.g., 1 course, then pay)?

2. **Quality Control:** How to ensure user-created courses are high quality?
   - Manual review before public publishing?
   - Community ratings?
   - AI-assisted validation?
   - Start with "unlisted only"?

3. **AI Enhancement:** Should we offer AI tools to help create content?
   - "Generate teaching content from objectives"
   - "Create assessment questions from text"
   - "Suggest vocabulary terms"

4. **Content Rights:** Who owns user-created courses?
   - Creator retains full rights?
   - Platform gets license to display?
   - Open-source/Creative Commons default?

5. **Progression:** Should MVP include:
   - Just linear progression (concept 1 → 2 → 3)?
   - Or complex prerequisite trees from the start?

---

## Next Steps

1. **Review this document** - Discuss scope, flow, and technical approach
2. **Define MVP boundaries** - What's absolutely necessary vs. nice-to-have?
3. **Create wireframes** - Visual mockups of the course creation UI
4. **API design** - Detailed endpoint specifications
5. **Database schema** - If we go the DB route (recommended for scalability)
6. **Begin implementation** - Start with backend API, then frontend wizard

---

## Timeline Estimate (MVP)

**Backend:** 2-3 weeks
- API endpoints: 1 week
- File storage & validation: 1 week
- Testing: 3-5 days

**Frontend:** 3-4 weeks
- Course wizard UI: 1.5 weeks
- Concept editor: 1.5 weeks
- Integration & testing: 1 week

**Total:** 5-7 weeks for functional MVP

This could be accelerated with focused effort or extended if scope expands.
