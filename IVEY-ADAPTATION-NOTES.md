# Ivey Business School Adaptation Notes
**Adaptive Case Study Learning Platform**

## Executive Summary

This document captures design patterns from the Adaptive Latin Learning proof-of-concept that are directly transferable to an Ivey Business School case study platform. The current architecture already supports the core pedagogical requirements identified for business case instruction.

**Status**: Proof-of-concept demonstrates technical feasibility
**Target**: Ivey Business School case-based learning
**Key Insight**: Learner profiling, adaptive feedback, and prior knowledge connections are domain-agnostic

---

## Priority 1: Enhanced Feedback System

### Current Implementation (Latin)
**File**: `backend/app/agent.py` (lines 699-767)

The system now enforces structured, specific feedback:

```python
# From _build_remediate_request()
return f"""Generate a detailed 'lesson' with the following MANDATORY structure:

Section 1 - 'Your Answer' heading:
- Start with EXACTLY this format: 'You chose "[their actual answer text]" (option [number]).
  This suggests you may have thought [specific misconception]. However, the correct answer is
  "[correct answer text]" because [2-3 sentences explaining the specific grammatical concept].'
- Be SPECIFIC about what their choice reveals about their thinking

Section 2 - 'The Key Concept' heading:
- Explain the grammatical concept they misunderstood in 3-4 sentences
- Use technical terms but explain them clearly
- If learner has Romance language background, EXPLICITLY connect to those languages

[...continues with specific requirements...]

Do NOT give vague feedback like 'Not quite - let's clarify this concept'.
Be SPECIFIC about what they got wrong and why.
"""
```

### Ivey Adaptation

**What stays the same**:
- Structured feedback requirement (sections, mandatory fields)
- Explicit misconception identification
- Connection to prior knowledge (see Priority 2)
- Quality enforcement via prompt engineering

**What changes**:

```python
# backend/app/ivey_agent.py (future)
def _build_case_feedback_request(
    student_answer: str,
    correct_analysis: dict,
    case_context: dict,
    learner_model: dict
) -> str:
    """Generate feedback for business case analysis."""

    profile = learner_model.get('profile', {})
    prior_cases = profile.get('completed_cases', [])
    background = profile.get('professional_background', '')

    # Build connection reminder for prior cases
    case_connections = ""
    if prior_cases:
        case_connections = f"\n\n**CRITICAL PERSONALIZATION**: This learner has completed cases: {', '.join(prior_cases)}. You MUST make EXPLICIT connections to those cases when relevant. For example: 'This pricing decision is similar to the Netflix case you studied last week...'"

    # Build background connection
    background_connection = ""
    if background:
        background_connection = f"\n\n**BACKGROUND CONTEXT**: Learner has {background} background. Connect to their professional experience when applicable."

    return f"""Generate detailed case analysis feedback with MANDATORY structure:

Section 1 - 'Your Analysis' heading:
- Start with EXACTLY: "Your analysis identified [✓ correct elements] but missed [✗ missing elements]."
- Be SPECIFIC about which parts of their reasoning were sound
- Identify the exact gap in their analysis

Section 2 - 'Framework Application' heading:
- Identify which framework(s) should have been applied (VRIO, Porter's Five Forces, 3Cs, etc.)
- Explain how to apply the framework to THIS specific case
- Provide 2-3 sentences on why this framework matters here

Section 3 - 'Similar Cases' heading:
- Reference prior cases this learner has studied{case_connections}
- Show how expert analysis from Case Study X applies here
- Build pattern recognition across cases

Section 4 - 'Cultural/Contextual Factors' callout:
- Highlight non-obvious factors they missed (cultural, regulatory, timing, etc.)
- Explain WHY these matter to the business outcome

QUALITY STANDARD: Feedback must help student see the gap between their mental model and expert analysis. No generic praise like "Good try!" - identify SPECIFIC strengths and gaps.
"""
```

**Implementation Path**:
1. ✅ Structured prompt enforcement (already built)
2. ✅ Learner profile injection (already built at agent.py:212-283)
3. 🔲 Create Ivey-specific feedback templates
4. 🔲 Add framework library (VRIO, Porter's, etc.) to resource bank
5. 🔲 Build case completion tracking in learner model

---

## Priority 2: Implement True "Connections" Learning

### Current Implementation (Latin)

**File**: `backend/app/agent.py` (lines 709-718, 751-760)

```python
# Check for Romance language background to add explicit connection reminders
profile = learner_model.get('profile', {})
prior_knowledge = profile.get('priorKnowledge', {})
has_romance = prior_knowledge.get('hasRomanceLanguage', False)
language_details = prior_knowledge.get('languageDetails', '')

# Build connection reminder if applicable
connection_reminder = ""
if has_romance and language_details:
    connection_reminder = f"\n\n**CRITICAL PERSONALIZATION**: This learner has studied {language_details}. You MUST make EXPLICIT connections to these languages in your explanation. For example: 'Just like Spanish uses ____, Latin ____' or 'Similar to French ____, this Latin form ____'. Do NOT skip these connections - they are essential for this learner's understanding."
```

**This pattern is domain-agnostic!**

### Ivey Adaptation

**Learner Profile Schema** (`backend/data/learner-models/{learner_id}.json`):

```json
{
  "learner_id": "learner-ivey-12345",
  "learner_name": "Student Name",
  "profile": {
    "professional_background": "Management consulting at McKinsey, 3 years",
    "industry_experience": ["Healthcare", "Technology"],
    "prior_education": "Economics major, Statistics minor",
    "completed_cases": [
      {
        "case_id": "netflix-pricing-2023",
        "case_title": "Netflix: Pricing in Competitive Markets",
        "completion_date": "2024-01-15",
        "frameworks_used": ["Porter's Five Forces", "Price Elasticity"],
        "score": 0.85
      },
      {
        "case_id": "tesla-manufacturing",
        "case_title": "Tesla: Manufacturing Innovation",
        "completion_date": "2024-01-22",
        "frameworks_used": ["VRIO", "Operational Excellence"],
        "score": 0.78
      }
    ],
    "learning_style": "connections",  // Same as Latin version!
    "interests": "Sustainable business models, emerging markets"
  },
  "current_case": "amazon-acquisition-strategy",
  "concepts": {
    "mergers-acquisitions": {
      "status": "in_progress",
      "mastery_score": 0.62,
      "assessments": [...]
    }
  }
}
```

**Connection Injection** (works exactly like Romance language connections):

```python
# backend/app/ivey_agent.py
def inject_case_connections(learner_model: dict) -> str:
    """Build connection reminders for case analysis."""
    profile = learner_model.get('profile', {})
    completed_cases = profile.get('completed_cases', [])
    background = profile.get('professional_background', '')

    connection_text = ""

    if completed_cases:
        recent_cases = [c['case_title'] for c in completed_cases[-3:]]  # Last 3 cases
        connection_text += f"\n\n**CRITICAL PERSONALIZATION**: This learner has studied: {', '.join(recent_cases)}. You MUST make EXPLICIT connections when relevant. Examples:\n"
        connection_text += "- 'Remember how Netflix approached pricing? This situation differs because...'\n"
        connection_text += "- 'You applied VRIO to Tesla's manufacturing - the same framework reveals...'\n"
        connection_text += "Do NOT skip these connections - they build pattern recognition across cases."

    if background:
        connection_text += f"\n\n**BACKGROUND CONNECTION**: Learner has {background}. Connect to their professional experience: 'Your consulting background would suggest applying the 3C framework here...'"

    return connection_text
```

**Example AI-Generated Feedback** (after implementing connections):

> **Your Analysis**
>
> You correctly identified the cash flow challenge (✓) and recommended debt financing (✓). However, you missed the cultural integration risks that derailed the AOL-Time Warner merger - a critical oversight in cross-border M&A (✗).
>
> **Framework Application**
>
> Remember the **VRIO framework** you applied to Tesla's manufacturing advantages last week? Here, use it to assess whether this acquisition creates defensible competitive advantage:
> - **Valuable**: Does combining these firms create new value?
> - **Rare**: Are the synergies truly unique to this pairing?
> - **Imitable**: Can competitors replicate these gains through organic growth?
> - **Organized**: Do both organizations have the structure to capture synergies?
>
> Your consulting background would recognize this as due diligence failure - the numbers looked good, but cultural fit assessment was superficial.

**Implementation Path**:
1. ✅ Profile injection architecture (already exists)
2. ✅ Connection reminder patterns (proven with Romance languages)
3. 🔲 Extend learner model schema for case completion tracking
4. 🔲 Build case metadata library (frameworks used, key concepts, etc.)
5. 🔲 Add professional background field to onboarding

---

## Priority 3: Case-Specific Features

### Progressive Case Reveal

**New Content Type Needed**: `"type": "case-exhibit"`

The current content generation system (`backend/app/agent.py:782-1000`) already supports multiple content types:
- `lesson` - Structured explanations
- `paradigm-table` - Visual patterns (→ **financial statements, frameworks**)
- `example-set` - Contextualized examples (→ **industry benchmarks**)
- `multiple-choice` - Diagnostic questions (→ **strategic decisions**)
- `fill-blank` - Targeted practice (→ **calculate metrics**)
- `dialogue` - Open response (→ **justify recommendation**)

**Add new type**:

```json
{
  "type": "case-exhibit",
  "exhibit_id": "financial-statements-q1-q4",
  "title": "Exhibit 3: Quarterly Financial Performance",
  "unlock_trigger": "completed_question_2",
  "content": {
    "tables": [...],
    "charts": [...],
    "notes": "Fiscal year ends December 31. All figures in millions USD."
  },
  "hints": [
    "Look for trends in gross margin - what does this suggest about pricing power?",
    "Compare Q3 to Q4 - what external event might explain the revenue spike?"
  ]
}
```

**Backend Logic** (`backend/app/ivey_agent.py`):

```python
def generate_case_content(
    learner_id: str,
    case_id: str,
    stage: str,
    exhibits_unlocked: List[str]
) -> dict:
    """Generate case content with progressive exhibit reveals."""

    learner_model = load_learner_model(learner_id)
    case_metadata = load_case_metadata(case_id)

    # Determine what exhibits to show
    next_exhibit = None
    for exhibit in case_metadata['exhibits']:
        if exhibit['exhibit_id'] not in exhibits_unlocked:
            # Check unlock condition
            if meets_unlock_criteria(learner_model, exhibit['unlock_trigger']):
                next_exhibit = exhibit
                break

    # Generate question or reveal exhibit
    if stage == "reveal_exhibit" and next_exhibit:
        return {
            "success": True,
            "content": {
                "type": "case-exhibit",
                **next_exhibit
            }
        }
    elif stage == "assess":
        # Generate question based on currently available exhibits
        available_data = [e for e in case_metadata['exhibits'] if e['exhibit_id'] in exhibits_unlocked]
        return generate_strategic_question(case_metadata, available_data, learner_model)
```

**Frontend Component** (`frontend/src/components/CaseExhibitRenderer.jsx`):

```jsx
function CaseExhibitRenderer({ exhibit, onAcknowledge }) {
  return (
    <div className="case-exhibit">
      <div className="exhibit-header">
        <span className="exhibit-badge">🔓 New Exhibit Unlocked</span>
        <h2>{exhibit.title}</h2>
      </div>

      <div className="exhibit-content">
        {exhibit.content.tables && (
          <FinancialTable data={exhibit.content.tables} />
        )}
        {exhibit.content.charts && (
          <Chart data={exhibit.content.charts} />
        )}
      </div>

      {exhibit.hints && (
        <div className="exhibit-hints">
          <h3>Consider:</h3>
          <ul>
            {exhibit.hints.map((hint, i) => (
              <li key={i}>{hint}</li>
            ))}
          </ul>
        </div>
      )}

      <button onClick={onAcknowledge} className="continue-button">
        I've reviewed this exhibit →
      </button>
    </div>
  )
}
```

**Unlock Trigger Examples**:
- `"completed_question_1"` - After answering first diagnostic
- `"score_below_0.6"` - Adaptive reveal if struggling
- `"time_elapsed_5min"` - Simulates receiving new information
- `"requested_exhibit_3"` - Student asks for more data

**Implementation Path**:
1. ✅ Content type system (extensible by design)
2. 🔲 Add `case-exhibit` content type to schema
3. 🔲 Build unlock logic in content generator
4. 🔲 Create frontend component for exhibit rendering
5. 🔲 Add exhibit tracking to learner model (`exhibits_unlocked: []`)

---

## Architecture Compatibility Analysis

### What Works Out-of-the-Box

| Component | Latin Version | Ivey Version | Status |
|-----------|---------------|--------------|--------|
| Learner profiling | Grammar background, languages studied | Professional background, cases completed | ✅ Same pattern |
| Adaptive feedback | Confidence × correctness matrix | Same matrix | ✅ No changes needed |
| Content generation | AI generates questions/lessons | AI generates case questions/analysis | ✅ Prompt changes only |
| Connection reminders | Romance language → Latin | Prior cases → Current case | ✅ Same injection pattern |
| Progress tracking | Mastery per concept | Mastery per framework/skill | ✅ Same data model |
| Tutor chat | Grammar questions | Case analysis questions | ✅ Different knowledge base |

### What Needs Modification

| Component | Change Required | Complexity |
|-----------|----------------|------------|
| Onboarding questions | Professional background, industry experience | Low - update OnboardingFlow.jsx |
| Resource bank structure | `concept-001/` → `case-netflix-pricing/` | Low - folder reorganization |
| Content types | Add `case-exhibit`, `financial-table` | Medium - new renderers |
| Feedback prompts | Grammar → Business frameworks | Low - prompt engineering |
| External resources | Latin grammar sites → HBR articles, framework guides | Low - metadata changes |
| Question types | Latin grammar → Strategic decisions, calculations | Medium - new validators |

### What Needs Major Development

1. **Case Library Management**
   - Upload case PDFs, extract exhibits
   - Tag with frameworks, industries, difficulty
   - Version control for case updates

2. **Collaborative Features** (if multi-student)
   - Team-based case analysis
   - Peer review of recommendations
   - Class discussion integration

3. **Professor Dashboard**
   - Monitor student progress across cohort
   - Identify common misconceptions
   - Adjust case difficulty in real-time

4. **Integration with Ivey Systems**
   - SSO with Ivey credentials
   - Grade export to LMS
   - AODA compliance audit (already mostly compliant)

---

## Technical Debt & Known Issues

### From Latin Proof-of-Concept

**Fixed in development**:
- ✅ Fill-blank field naming (correctAnswer vs correctAnswers)
- ✅ Confidence scale consistency (1-4 everywhere)
- ✅ slowapi parameter naming conventions
- ✅ Generic feedback problem (addressed with structured prompts)
- ✅ Missing Romance language connections (implemented)

**Not yet addressed** (lower priority for proof-of-concept):
- 🔲 No automated testing (integration tests in INTEGRATION-TEST-PLAN.md but not implemented)
- 🔲 No CI/CD pipeline
- 🔲 Single-concept limitation (only concept-001 implemented)
- 🔲 No cumulative review questions yet (code exists but needs testing)
- 🔲 Rate limiting not tested under load
- 🔲 Error recovery could be more graceful

**Ivey-specific considerations**:
- 🔲 Need exhibit file storage (S3 or similar)
- 🔲 Need instructor override capabilities
- 🔲 Need audit logs for academic integrity
- 🔲 Need accessibility testing with screen readers (WCAG 2.1 AA target)

---

## Resource Bank Structure Comparison

### Current (Latin)
```
resource-bank/
└── latin-grammar/
    └── concept-001/
        ├── metadata.json
        ├── lessons/
        │   └── first-declension-intro.md
        ├── tables/
        │   └── puella-paradigm.json
        ├── examples/
        │   └── contextual-examples.json
        └── external-resources/
            └── resources.json
```

### Proposed (Ivey)
```
resource-bank/
└── business-cases/
    ├── case-netflix-pricing-2023/
    │   ├── metadata.json
    │   │   {
    │   │     "case_id": "netflix-pricing-2023",
    │   │     "title": "Netflix: Pricing in Competitive Markets",
    │   │     "industry": "Entertainment/Streaming",
    │   │     "frameworks": ["Porter's Five Forces", "Price Elasticity", "Competitive Response"],
    │   │     "difficulty": "intermediate",
    │   │     "prerequisites": ["case-intro-pricing"],
    │   │     "learning_objectives": [
    │   │       "Apply Porter's Five Forces to assess competitive intensity",
    │   │       "Analyze price elasticity in subscription markets",
    │   │       "Evaluate strategic responses to competitive threats"
    │   │     ]
    │   │   }
    │   ├── exhibits/
    │   │   ├── 01-company-background.md
    │   │   ├── 02-market-landscape.json
    │   │   ├── 03-financial-statements.json
    │   │   ├── 04-customer-survey-data.json
    │   │   └── 05-competitor-pricing.json
    │   ├── frameworks/
    │   │   ├── porters-five-forces-guide.md
    │   │   └── price-elasticity-calculator.json
    │   ├── expert-analysis/
    │   │   └── professor-commentary.md
    │   └── external-resources/
    │       └── resources.json  // HBR articles, industry reports
    │
    └── frameworks/  // Shared across cases
        ├── porters-five-forces/
        ├── vrio/
        ├── swot/
        └── bcg-matrix/
```

---

## Migration Checklist

### Phase 1: Core Adaptation (2-4 weeks)
- [ ] Update learner profile schema for business context
- [ ] Create Ivey-specific onboarding flow
- [ ] Build 1-2 pilot cases with exhibits
- [ ] Adapt feedback prompts for business frameworks
- [ ] Test with small cohort (10-20 students)

### Phase 2: Feature Enhancement (4-6 weeks)
- [ ] Implement progressive exhibit reveals
- [ ] Add framework library to resource bank
- [ ] Build professor dashboard (view-only)
- [ ] Create case upload/management tool
- [ ] Conduct accessibility audit

### Phase 3: Production Readiness (6-8 weeks)
- [ ] SSO integration with Ivey systems
- [ ] LMS grade export
- [ ] Performance testing (100+ concurrent users)
- [ ] Security audit
- [ ] Student user testing (50+ students)
- [ ] Faculty training materials

### Phase 4: Scale & Iterate (Ongoing)
- [ ] Expand case library (target: 20+ cases)
- [ ] Add collaborative features (optional)
- [ ] Build analytics for learning insights
- [ ] Integrate with Ivey course syllabi
- [ ] Publish research on learning outcomes

---

## Cost Considerations

### Current Latin Proof-of-Concept

**Anthropic API Usage** (estimated):
- Content generation: ~2,000 tokens/question (input) + ~1,500 tokens/response (output)
- Cost per question cycle: ~$0.02 USD
- Student answering 20 questions: ~$0.40 USD
- Cohort of 100 students: ~$40 USD per assignment

**Infrastructure**:
- Backend: Can run on Ivey servers (FastAPI + Python)
- Frontend: Static hosting (GitHub Pages, Netlify, or Ivey web server)
- Database: Local JSON files (OK for proof-of-concept, upgrade to PostgreSQL for production)

### Ivey Production Version

**Additional costs**:
- Case exhibit storage: S3 or similar (~$20-50/month for 50 cases)
- Database: PostgreSQL managed service (~$50-100/month)
- Monitoring/logging: DataDog or similar (~$100/month)
- Accessibility testing tools: ~$500/year

**Scaling**:
- Per-student cost remains ~$0.40-0.80 per assignment (depending on case complexity)
- 500 students × 10 assignments/semester = ~$4,000 in API costs
- Compare to: TA grading time saved (500 students × 2 hours/student × $25/hour = $25,000)

**ROI is strongly positive if system reduces grading burden.**

---

## Academic Integrity Considerations

### Preventing Misuse

**Current design** (already resistant to gaming):
1. ✅ Confidence calibration penalizes overconfidence from guessing
2. ✅ Scenario-based questions harder to search online
3. ✅ AI generates unique questions (not from static bank)
4. ✅ Question history prevents simple repetition

**Ivey-specific additions needed**:
- 🔲 Audit log: Track all student-AI interactions
- 🔲 Plagiarism detection: Flag if student answers match AI tutor responses verbatim
- 🔲 Time tracking: Alert if student completes complex case too quickly
- 🔲 Proctoring integration: Optional for high-stakes assessments

### Ivey Academic Integrity Policy Alignment

The system should support, not replace, Ivey's Honor Code:
- **Formative use**: System ideal for practice/learning (NOT summative exams)
- **Transparency**: Students know they're interacting with AI tutor
- **Skill building**: Focus on teaching frameworks, not providing answers
- **Professor oversight**: Dashboard shows student progress and AI interactions

---

## Research Opportunities

### Publishable Questions

1. **Learning Efficacy**
   - Does adaptive feedback improve case analysis skills vs. static rubrics?
   - How does confidence calibration affect decision-making quality?
   - Measure: Pre/post framework application accuracy

2. **Personalization Impact**
   - Do "connections" students outperform others when prior case connections are explicit?
   - Professional background × case industry match → performance correlation?
   - Measure: Time to mastery, retention in follow-up assessments

3. **AI-Assisted Learning**
   - Can LLM-generated feedback match expert TA feedback quality?
   - Blind comparison: Students rate AI vs. human feedback
   - Measure: Student satisfaction, learning outcomes, cost per student

4. **Framework Transfer**
   - Does practice in adaptive system improve performance on final exams?
   - Do students develop better pattern recognition across cases?
   - Measure: Framework application accuracy in novel cases

### Potential Publications

- *Journal of Management Education* - Adaptive learning in case-based instruction
- *Decision Sciences Journal of Innovative Education* - AI tutoring for business analytics
- *Academy of Management Learning & Education* - Confidence calibration in strategic thinking

---

## Next Steps for Proof-of-Concept → Ivey Pilot

1. **Immediate** (this week)
   - ✅ Document architecture compatibility (this file)
   - 🔲 Create 1 pilot business case (simple pricing decision)
   - 🔲 Adapt onboarding for business student profile

2. **Short-term** (next 2 weeks)
   - 🔲 Test with 5-10 Ivey students (alpha testing)
   - 🔲 Collect qualitative feedback on feedback quality
   - 🔲 Compare AI feedback to professor's expert commentary

3. **Medium-term** (next 4 weeks)
   - 🔲 Build 3-5 cases across different industries/frameworks
   - 🔲 Implement basic professor dashboard
   - 🔲 Conduct accessibility review

4. **Pitch to Ivey** (6-8 weeks)
   - 🔲 Prepare demo with real cases
   - 🔲 Cost-benefit analysis vs. TA grading
   - 🔲 Research proposal for learning outcomes study
   - 🔲 Security & privacy review completion

---

## Contact & Resources

**Current proof-of-concept**: https://github.com/jameskruck/adaptive-latin
**Documentation**: See INTEGRATION-TEST-PLAN.md, README.md
**Developer**: James Kruck (Ivey EdTech Lab)

**Key stakeholders for Ivey pilot**:
- EdTech Lab Director
- Case method faculty champion
- IT Security (for Ivey system integration)
- AODA compliance officer

---

*Last updated: 2024-10-24*
*Version: 1.0 (Latin proof-of-concept complete)*
