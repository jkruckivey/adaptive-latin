# Assessment Personalization Guide

**Version:** 1.0.0
**Date:** 2025-11-23
**Feature:** Scenario-Based Assessment Personalization

---

## Overview

The Adaptive Latin Learning System now supports **personalized assessment questions** that adapt to learner interests while maintaining **identical learning objectives and assessment validity**.

### What This Means

- **Questions** adapt to learner context (history, archaeology, mythology, literature)
- **Learning objectives** remain constant
- **Rubrics** are identical across all variations
- **Assessment validity** is preserved

### Example

**Base Question:**
> "How do you identify a first declension noun?"

**History Teacher Sees:**
> "You're examining a Roman inscription and see the word 'MEMORIAE'. How would you identify whether this belongs to the first declension?"

**Mythology Student Sees:**
> "You're reading about Roman gods and encounter 'DEA FORTUNAE' (goddess of fortune). How can you tell if 'FORTUNAE' is first declension?"

**Both are assessing**: Ability to identify first declension nouns by their endings
**Both use**: Same rubric with same criteria
**Difference**: Context matches learner interests

---

## How It Works

### 1. Learner Profile Collection

During onboarding, learners provide:
- **Background**: Their context (teacher, student, hobbyist, etc.)
- **Interests**: Topics they care about (e.g., "Roman history, archaeology, ancient warfare")
- **Learning Style**: Visual, practice-based, or conceptual

### 2. Interest Matching

The system analyzes learner interests and maps them to scenario categories:

| Interest Keywords | Scenario Category |
|------------------|-------------------|
| history, historical, roman history, ancient history, inscriptions | **history** |
| archaeology, archaeological, excavation, artifacts, sites | **archaeology** |
| mythology, mythological, gods, goddesses, myths, legends | **mythology** |
| literature, literary, poetry, poems, reading, books | **literature** |
| *(no match)* | **default** |

### 3. Question Selection

When presenting an assessment:
1. Load learner profile
2. Identify their primary interest category
3. Select matching scenario template
4. Present personalized question
5. Assess using standard rubric

---

## Creating Personalized Assessments

### File Structure

Create both standard and personalized versions:

```
concept-XXX/
├── assessments/
│   ├── dialogue-prompts.json                    # Standard version (backward compatible)
│   └── dialogue-prompts-personalized.json       # Personalized version (NEW)
```

### Personalized Prompt Schema

#### Top-Level Fields

```json
{
  "assessment_type": "dialogue",
  "concept_id": "concept-001",
  "confidence_tracking_enabled": true,
  "personalization_enabled": true,              // NEW: Enable personalization
  "prompts": [...]                               // Array of prompts (see below)
}
```

#### Individual Prompt Structure

```json
{
  "id": "dialogue-001-1",
  "difficulty": "basic",
  "learning_objective": "Identify first declension nouns by their characteristic endings",

  "base_prompt": "How do you identify a first declension noun?",

  "scenario_templates": {
    "history": "You're examining a Roman inscription and see the word 'MEMORIAE'. How would you identify whether this belongs to the first declension?",
    "archaeology": "You've uncovered a stone tablet with 'VICTORIAE AUGUSTAE' carved on it. How do you know if these nouns are first declension?",
    "mythology": "You're reading about Roman gods and encounter 'DEA FORTUNAE' (goddess of fortune). How can you tell if 'FORTUNAE' is first declension?",
    "literature": "You're translating a Latin poem and see 'rosa, rosae'. How do you identify this as first declension?",
    "default": "How do you know if a noun is first declension? What should you look for?"
  },

  "rubric": {
    // Same rubric for ALL scenarios
    "excellent": {
      "criteria": [
        "Mentions nominative singular ending (-a)",
        "Mentions genitive singular ending (-ae)",
        "Notes that most are feminine"
      ],
      "score_range": "0.90-1.00"
    }
  }
}
```

### Required Fields for Personalization

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `learning_objective` | string | **Yes** | Clear statement of what's being assessed |
| `base_prompt` | string | **Yes** | Fallback if no scenarios match |
| `scenario_templates` | object | **Yes** | Interest-specific question variations |
| `scenario_templates.default` | string | Recommended | Generic version |
| `rubric` | object | **Yes** | Same assessment criteria for all scenarios |

---

## Design Principles

### 1. **Preserve Learning Objectives**

✅ **Good**: Different contexts, same skill
```json
{
  "learning_objective": "Identify nominative case function",
  "history": "In 'CAESAR GALLOS VICIT', what role does the nominative play?",
  "mythology": "In 'Iuppiter tonat', what does the nominative tell us?"
}
```

❌ **Bad**: Different skills assessed
```json
{
  "learning_objective": "Identify nominative case function",
  "history": "What case is CAESAR in?",              // Identification only
  "mythology": "Why is Iuppiter nominative here?"    // Explanation required
}
```

### 2. **Maintain Equal Difficulty**

✅ **Good**: Equally challenging
```json
{
  "history": "In 'GALLIAM CAESAR VICIT', why doesn't GALLIAM being first mean it conquered Caesar?",
  "mythology": "In 'Minervam Iuppiter amat', why doesn't Minerva being first make her the subject?"
}
```

❌ **Bad**: Unequal difficulty
```json
{
  "history": "Explain why word order doesn't determine function in Latin.",  // Abstract
  "mythology": "What case is Minervam?"                                      // Concrete
}
```

### 3. **Use Authentic Contexts**

✅ **Good**: Realistic scenarios
```json
{
  "history": "You're examining a Roman inscription...",
  "archaeology": "On a votive offering, you see...",
  "mythology": "In stories about the gods..."
}
```

❌ **Bad**: Forced or contrived
```json
{
  "history": "Imagine you're a time-traveling historian...",
  "archaeology": "Pretend you're Indiana Jones..."
}
```

### 4. **Ensure Rubric Compatibility**

All scenario variations MUST be assessable using the SAME rubric.

```json
{
  "rubric": {
    "excellent": {
      "criteria": [
        "Explains that endings, not position, show function",
        "Identifies accusative by -am ending",
        "Identifies nominative by -a ending"
      ]
    }
  }
}
```

Both questions must allow assessment of these criteria:
- ✅ History version: Checks all criteria
- ✅ Mythology version: Checks all criteria
- ❌ If any version can't be assessed on all criteria: **Invalid design**

---

## Implementation Checklist

When creating personalized assessments:

- [ ] **Learning objective** is clear and identical across scenarios
- [ ] **All scenario variations** test the same underlying skill
- [ ] **Difficulty level** is equal across scenarios
- [ ] **Rubric criteria** can assess all scenarios fairly
- [ ] **base_prompt** exists as fallback
- [ ] **default scenario** provided for unmatched interests
- [ ] **Contexts are authentic** and relevant to the interest category
- [ ] **Tested** with learners from each interest group

---

## Technical Details

### Backend Implementation

**File**: `backend/app/tools.py`

**Key Functions**:

1. `personalize_assessment_prompt(prompt_data, learner_profile)` - Selects appropriate scenario
2. `select_personalized_dialogue_prompt(concept_id, learner_id, difficulty)` - Complete workflow

**Usage**:

```python
from app.tools import select_personalized_dialogue_prompt

# Get personalized question for learner
prompt_data = select_personalized_dialogue_prompt(
    concept_id="concept-001",
    learner_id="test_walkthrough_001",
    difficulty="basic"
)

print(prompt_data['prompt'])        # Personalized question
print(prompt_data['rubric'])        # Assessment rubric
print(prompt_data['learning_objective'])  # What's being assessed
```

### Fallback Behavior

1. **Try**: Load `dialogue-prompts-personalized.json`
2. **If not found**: Load standard `dialogue-prompts.json`
3. **If no scenario templates**: Use `base_prompt`
4. **If no interest match**: Use `default` scenario

This ensures **backward compatibility** with existing assessments.

---

## Examples

### Example 1: Basic Concept Identification

```json
{
  "id": "dialogue-001-1",
  "learning_objective": "Identify first declension nouns by their characteristic endings",
  "base_prompt": "How do you identify a first declension noun?",
  "scenario_templates": {
    "history": "You're examining a Roman inscription and see 'MEMORIAE'. How would you identify whether this belongs to the first declension?",
    "archaeology": "You've uncovered a stone tablet with 'VICTORIAE AUGUSTAE'. How do you know if these nouns are first declension?",
    "mythology": "You're reading about Roman gods and encounter 'DEA FORTUNAE'. How can you tell if 'FORTUNAE' is first declension?",
    "literature": "You're translating a Latin poem and see 'rosa, rosae'. How do you identify this as first declension?",
    "default": "How do you know if a noun is first declension? What should you look for?"
  }
}
```

### Example 2: Case Function Analysis

```json
{
  "id": "dialogue-001-3",
  "learning_objective": "Explain the function and importance of the nominative case",
  "base_prompt": "Explain what the nominative case does in a Latin sentence. Why do we need it?",
  "scenario_templates": {
    "history": "When reading a historical inscription like 'CAESAR GALLOS VICIT' (Caesar conquered the Gauls), what role does the nominative case play and why is it essential?",
    "archaeology": "You find a damaged inscription: '[?]ORIA ROMAN[?] VINCIT'. Why is identifying the nominative case crucial to understanding who/what is conquering?",
    "mythology": "In stories about the gods, like 'Iuppiter tonat' (Jupiter thunders), what does the nominative case tell us and why do we need it?",
    "literature": "In Latin poetry, word order is very flexible for meter. Why is the nominative case essential when words can appear in any order?",
    "default": "Explain what the nominative case does in a Latin sentence. Why do we need it?"
  }
}
```

### Example 3: Syntactic Reasoning

```json
{
  "id": "dialogue-001-6",
  "learning_objective": "Distinguish between multiple -ae forms using syntactic and semantic context",
  "base_prompt": "In the sentence 'Puellae aquam do,' what case is 'puellae' and how do you know?",
  "scenario_templates": {
    "history": "Imagine reading: 'Caesari victoriam do' (I give victory to Caesar). Using similar logic, in 'Puellae aquam do,' what case is 'puellae' and why?",
    "archaeology": "On a votive offering, you see 'DEAE DONUM DO' (I give a gift to the goddess). Similarly, in 'Puellae aquam do,' what case is 'puellae'?",
    "mythology": "Gods often receive offerings: 'Iovae sacrificium do' (I give a sacrifice to Jupiter). In the sentence 'Puellae aquam do,' what case is 'puellae' and how do you know?",
    "literature": "In poetry, gift-giving is common: 'amicae rosam do' (I give a rose to my friend). Using this pattern, what case is 'puellae' in 'Puellae aquam do'?",
    "default": "Here's a tricky one: In the sentence 'Puellae aquam do,' what case is 'puellae' and how do you know?"
  }
}
```

---

## Benefits

### For Learners:
- ✅ **Higher engagement** - questions feel relevant
- ✅ **Better retention** - context aids memory
- ✅ **Increased motivation** - learning feels personalized
- ✅ **Reduced anxiety** - familiar contexts lower cognitive load

### For Educators:
- ✅ **Standardized assessment** - same rubrics for all learners
- ✅ **Fair comparison** - learning objectives are identical
- ✅ **Flexible content** - easy to add new scenarios
- ✅ **Backward compatible** - works with existing assessments

### For the System:
- ✅ **Scalable** - add scenarios without changing code
- ✅ **Maintainable** - centralized personalization logic
- ✅ **Testable** - clear criteria for each scenario
- ✅ **Extensible** - new interest categories easily added

---

## Testing Your Personalized Assessments

Use the provided test script:

```bash
cd backend
python test_personalized_prompts.py
```

**Tests Include**:
1. Prompt personalization for each interest category
2. Real learner personalization (test_walkthrough_001)
3. Multiple question generation
4. Fallback to standard prompts

**Expected Output**:
```
[PASS] - Correctly personalized
[PASS] - Question is personalized to learner's interests
[PASS] - Successfully generated multiple personalized questions
[PASS] - Successfully fell back to standard prompts
```

---

## Future Enhancements

Potential additions to the personalization system:

1. **Dynamic templating**: Fill in learner-specific examples
2. **Difficulty adaptation**: Adjust scenarios based on performance
3. **Multi-interest support**: Blend multiple interest categories
4. **Language background**: Adapt examples to known languages
5. **Professional context**: Business, academic, personal learning goals

---

## Support

For questions or issues:
- Review `ARCHITECTURE.md` for system design
- Check `CLAUDE.md` for implementation details
- See `dialogue-prompts-personalized.json` for complete examples
- Run `test_personalized_prompts.py` to verify setup

---

**Last Updated**: 2025-11-23
**Feature Version**: 1.0.0
**Compatibility**: Backward compatible with all existing assessments
