# System Prompts Documentation

This directory contains all AI system prompts used in the Adaptive Latin Learning system. Separating prompts from code allows for easier iteration, A/B testing, and non-technical editing.

## Directory Structure

```
prompts/
├── README.md                                      # This file
├── tutor-agent-system-prompt-active.md            # ✅ ACTIVE: General adaptive learning system prompt
├── tutor-agent-system-prompt-latin-specific.md    # Latin-focused version (reference)
├── confidence-response-addendum.md                # ✅ ACTIVE: Confidence calibration guidelines
├── confidence-tracking-prompt-latin-specific.md   # Latin-focused version (reference)
├── content-generation-addendum.md                 # ✅ ACTIVE: Content generation instructions
└── conversational-agents/                         # Future: separate prompts for chat agents
    ├── latin-tutor-chat.md
    └── roman-character-chat.md
```

## Prompt Files

### 1. `tutor-agent-system-prompt-active.md` ✅ ACTIVE
**Purpose**: Core system prompt for the adaptive learning tutor agent (general-purpose, works for any subject)

**Used by**: `backend/app/agent.py` - `load_system_prompt()` function → used in `chat()` for conversational tutoring

**Origin**: Migrated from `examples/prompts/` - this is the comprehensive, production-tested prompt

**Key Responsibilities**:
- Generate lessons, paradigm tables, examples, practice exercises
- Adapt content format to learner's learning style
- Create assessments (multiple-choice, fill-blank, dialogue)
- Follow diagnostic-first pedagogy
- Personalize examples to learner interests

**When to Edit**:
- Changing teaching philosophy (e.g., more/less Socratic)
- Adjusting content format requirements
- Adding new content types
- Modifying JSON schemas
- Updating pedagogical principles

**Testing After Changes**:
1. Generate content for all stages (start, practice, assess, remediate, reinforce)
2. Verify JSON validation passes
3. Check personalization works (uses learner profile)
4. Confirm content quality meets standards

---

### 2. `confidence-response-addendum.md` ✅ ACTIVE
**Purpose**: Detailed guidelines for confidence-aware assessment and feedback (addendum to main system prompt)

**Used by**: `backend/app/agent.py` - `load_system_prompt()` combines this with the main prompt

**Origin**: Migrated from `examples/prompts/` - comprehensive calibration feedback templates

**Calibration Categories**:
- **Overconfident**: Wrong answer + high confidence → Detailed teaching + metacognitive tip
- **Underconfident**: Correct answer + low confidence → Confidence-building affirmation
- **Calibrated**: Confidence matches performance → Brief positive feedback
- **Calibrated Low**: Wrong answer + low confidence (good awareness) → Supportive teaching

**When to Edit**:
- Adjusting feedback tone (more/less formal)
- Changing metacognitive strategies taught
- Modifying feedback length
- A/B testing different framing approaches

**Testing After Changes**:
1. Test all 4 calibration categories
2. Verify tone is supportive, not judgmental
3. Confirm feedback includes actionable tips
4. Check personalization (references specific answer/concept)

---

### 3. `content-generation-addendum.md` ✅ ACTIVE
**Purpose**: Instructions for generating structured JSON learning content (lessons, questions, tables, exercises)

**Used by**: `backend/app/agent.py` - `load_content_generation_prompt()` function → used in `generate_content()`

**Origin**: Migrated from `examples/prompts/` - includes diagnostic-first pedagogy, personalization rules, JSON schemas

**Key Responsibilities**:
- Generate JSON content types: lesson, paradigm-table, example-set, multiple-choice, fill-blank, dialogue
- Implement diagnostic-first pedagogy (assess before teaching)
- Personalize content based on learner profile (learning style, interests, language background)
- Create scenario-based questions with authentic contexts

**When to Edit**:
- Adding new content types or JSON schemas
- Changing pedagogical approach (e.g., more/less scaffolding)
- Adjusting personalization logic
- Updating content quality standards

---

### 4. `tutor-agent-system-prompt-latin-specific.md` (Reference)
**Purpose**: Latin-specific version of the tutor prompt created during prompt infrastructure setup

**Status**: Reference only - not currently active

**Differences from active prompt**: More concise, Latin-focused examples, specific to noun declensions

---

### 5. `confidence-tracking-prompt-latin-specific.md` (Reference)
**Purpose**: Latin-specific confidence calibration prompt created during prompt infrastructure setup

**Status**: Reference only - not currently active

**Differences from active prompt**: Shorter, Latin-specific examples, focused on grammatical concepts

---

## Prompt Design Principles

### 1. Clarity Over Brevity
Prompts should be **detailed and explicit**. AI models benefit from:
- Clear role definition
- Specific output format requirements
- Examples of good vs. bad outputs
- Edge case handling

**Bad**: "Generate a Latin lesson"
**Good**: "Generate a lesson following the JSON schema below. Include 2-3 sections with clear headings. Personalize examples to learner interests..."

### 2. Separation of Concerns
Each prompt file should have ONE primary responsibility:
- Content generation ≠ Confidence feedback
- Tutor agent ≠ Conversational chat agent
- Assessment creation ≠ Assessment evaluation

This modularity allows independent iteration.

### 3. Versioning and A/B Testing
When making significant prompt changes:
1. Save current version with date: `tutor-agent-system-prompt-2025-10-23.md`
2. Create new version
3. A/B test with real learners
4. Keep winning version, archive the other

### 4. Documentation of Intent
Each prompt should include comments explaining **WHY** certain instructions exist:
- "Use diagnostic-first approach (assess before teach)" → Explains pedagogical reasoning
- "ALWAYS return valid JSON only" → Explains technical requirement

## Common Prompt Engineering Patterns

### Pattern 1: Role + Responsibilities + Constraints
```markdown
You are {role} responsible for {responsibilities}.

You must {constraints/requirements}.
```

### Pattern 2: Output Format Specification
```markdown
Output Format: {format description}

Example:
{concrete example}

Validation:
- [ ] Checklist item 1
- [ ] Checklist item 2
```

### Pattern 3: Conditional Logic
```markdown
If {condition}:
  Then {action}

Examples:
- If learningStyle === "visual": Generate paradigm-table
- If stage === "remediate": Include detailed explanation
```

### Pattern 4: Examples (Few-Shot Learning)
```markdown
Good Example:
{example of desired output}

Bad Example (avoid):
{example of undesired output}

Why the difference matters: {explanation}
```

## Editing Workflow

### Making Changes

1. **Identify the prompt file** to modify (see "Used by" in each section above)
2. **Create backup**: Copy current version to `archive/prompt-name-YYYY-MM-DD.md`
3. **Edit the prompt**: Make changes in the main file
4. **Test locally**: Run content generation with new prompt
5. **Validate output**: Ensure JSON parsing works, content quality maintained
6. **Deploy**: If tests pass, deploy to production
7. **Monitor**: Check logs for errors, gather user feedback

### Testing Checklist

After editing any prompt:
- [ ] AI generates valid output (no parsing errors)
- [ ] Output matches required schema
- [ ] Content quality is accurate and pedagogically sound
- [ ] Personalization still works (uses learner profile)
- [ ] Edge cases handled gracefully
- [ ] No unintended regressions in other features

## Integration with Code

### How Prompts are Loaded

**✅ IMPLEMENTED** - Config-based loading with file reading

**Config (backend/app/config.py)**:
```python
# System Prompts (now located in backend/prompts/ for better organization)
PROMPTS_DIR: Path = BASE_DIR / "prompts"
SYSTEM_PROMPT_FILE: Path = PROMPTS_DIR / "tutor-agent-system-prompt-active.md"
CONFIDENCE_PROMPT_FILE: Path = PROMPTS_DIR / "confidence-response-addendum.md"
CONTENT_GENERATION_PROMPT_FILE: Path = PROMPTS_DIR / "content-generation-addendum.md"
```

**Loading Functions (backend/app/agent.py)**:
```python
def load_system_prompt() -> str:
    """Load the tutor agent system prompt and confidence addendum."""
    # Load main system prompt
    with open(config.SYSTEM_PROMPT_FILE, "r", encoding="utf-8") as f:
        main_prompt = f.read()

    # Load confidence tracking addendum
    with open(config.CONFIDENCE_PROMPT_FILE, "r", encoding="utf-8") as f:
        confidence_addendum = f.read()

    # Combine prompts
    return f"{main_prompt}\n\n{confidence_addendum}"

def load_content_generation_prompt() -> str:
    """Load the content generation instructions."""
    with open(config.CONTENT_GENERATION_PROMPT_FILE, "r", encoding="utf-8") as f:
        return f.read()
```

**Usage**:
- `chat()` function: Calls `load_system_prompt()` → combines tutor + confidence prompts
- `generate_content()` function: Calls `load_content_generation_prompt()` → uses content generation instructions

### Current Implementation Status

**As of 2025-10-23**:
- ✅ Prompts externalized and comprehensive (282 + 444 + 513 = 1,239 lines)
- ✅ Integration complete - agent.py loads from files
- ✅ Config.py updated to point to backend/prompts/
- ✅ Load functions implemented and working
- ✅ Directory structure consolidated

**Migration Completed**:
1. ✅ Copied existing prompts from `examples/prompts/` to `backend/prompts/`
2. ✅ Updated config.py to reference new location
3. ✅ Created comprehensive documentation (this README)
4. ✅ System tested and working (backend auto-reloaded successfully)

## Prompt Quality Guidelines

### Content Generation Prompts

**Must include**:
- Clear output format (JSON schema)
- Personalization instructions
- Quality criteria
- Examples of good output

**Should avoid**:
- Ambiguous instructions ("be creative")
- Conflicting requirements
- Assuming model knowledge (spell out everything)

### Feedback Prompts

**Must include**:
- Tone guidelines (supportive, growth-oriented)
- Specific language to use/avoid
- Actionable advice for learners
- Personalization hooks

**Should avoid**:
- Judgmental language
- Generic feedback templates
- Overly long responses

## Version History

| Date | File | Change | Reason |
|------|------|--------|--------|
| 2025-10-23 | All | Initial creation | Peer review identified missing prompt infrastructure |
| | | | |

---

## Related Documentation

- [ARCHITECTURE.md](../../ARCHITECTURE.md) - Overall system architecture
- [CONFIDENCE-TRACKING.md](../../CONFIDENCE-TRACKING.md) - Confidence calibration system
- [docs/PROMPTS-GUIDE.md](../../docs/PROMPTS-GUIDE.md) - Extended prompt engineering guide (future)

## Questions or Issues?

If you're unsure which prompt to edit or how to structure a new prompt:
1. Review existing prompts as templates
2. Check prompt engineering patterns above
3. Test changes locally before deploying
4. Document your reasoning in version history

**Remember**: Prompts are the "curriculum" of the AI tutor. Changes here directly affect learner experience. Edit thoughtfully and test thoroughly!
