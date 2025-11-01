# Pedagogical Features - Adaptive Scaffolding & Choice/Agency

**Date:** 2025-11-01
**Version:** 0.4.0

## Overview

This document describes the pedagogical improvements implemented to address learner discouragement and enhance motivation. These features implement evidence-based learning science principles:

1. **Adaptive Scaffolding** - Adjusting difficulty based on performance
2. **Choice & Agency** - Practice mode for stress-free exploration
3. **Growth Mindset** - Encouragement messages during struggle

## Feature 1: Adaptive Scaffolding

### What is Adaptive Scaffolding?

Adaptive scaffolding automatically adjusts question difficulty based on recent performance, ensuring learners are challenged appropriately without being overwhelmed.

### How It Works

**Difficulty Levels:**
- **Easier** (< 40% recent performance) - Fundamental vocabulary, basic forms, clear context clues
- **Appropriate** (40-85% performance) - Standard difficulty level
- **Harder** (> 85% performance) - Complex vocabulary, deeper analysis, subtle distractors

**Performance Calculation:**
- Tracks the last 5 questions (sliding window)
- Calculates correctness ratio (e.g., 3/5 = 60%)
- Adjusts difficulty for next question

**Example:**
```
Student answers: ❌ ❌ ✅ ❌ ❌  (Recent performance: 20%)
→ System provides EASIER questions (back to fundamentals)

Student answers: ✅ ✅ ✅ ✅ ❌  (Recent performance: 80%)
→ System provides APPROPRIATE questions (maintain challenge)

Student answers: ✅ ✅ ✅ ✅ ✅  (Recent performance: 100%)
→ System provides HARDER questions (increase difficulty)
```

### Adaptive Mastery Thresholds

The system also adjusts mastery expectations:

| Performance Level | Mastery Threshold | Rationale |
|------------------|------------------|-----------|
| Struggling (< 40%) | 70% | Achievable wins build confidence |
| Normal (40-85%) | 75% | Standard expectation |
| Excelling (> 85%) | 85% | Higher bar for challenge |

### Implementation

**Backend Functions (backend/app/tools.py):**
```python
# Calculate recent performance
calculate_recent_performance(learner_id, concept_id, window_size=5)

# Select appropriate difficulty
select_question_difficulty(learner_id, concept_id)
# Returns: "easier", "appropriate", or "harder"

# Get adaptive mastery threshold
get_adaptive_mastery_threshold(learner_id, concept_id)
# Returns: 0.70, 0.75, or 0.85
```

**Constants (backend/app/constants.py):**
```python
DIFFICULTY_DOWN_THRESHOLD = 0.40  # Below 40% → easier
DIFFICULTY_UP_THRESHOLD = 0.85    # Above 85% → harder
DIFFICULTY_ASSESSMENT_WINDOW = 5  # Last 5 questions

MASTERY_THRESHOLD_STRUGGLING = 0.70  # Lower bar when struggling
MASTERY_THRESHOLD_NORMAL = 0.75      # Standard threshold (lowered from 0.85)
MASTERY_THRESHOLD_EXCELLING = 0.85   # Higher bar for high performers
```

## Feature 2: Choice & Agency (Practice Mode)

### What is Practice Mode?

Practice Mode allows learners to explore questions without affecting their mastery score. This provides psychological safety for experimentation and reduces performance anxiety.

### How It Works

**When Practice Mode is Enabled:**
- ✅ Questions are generated normally
- ✅ Feedback is provided on correctness
- ❌ Assessments **do not** count toward mastery score
- ❌ Incorrect answers **do not** prevent progression
- 🎯 Learners can practice stress-free

**When Practice Mode is Disabled (Graded Mode):**
- ✅ Questions count toward mastery
- ✅ Progress toward concept completion
- ✅ Normal adaptive learning flow

### Use Cases

1. **Explore Before Committing** - Preview concept difficulty
2. **Recover After Struggle** - Practice without pressure after several mistakes
3. **Review Previously Mastered** - Refresh knowledge without affecting score
4. **Experimentation** - Try different approaches risk-free

### Implementation

**Backend API Endpoint:**
```http
PUT /learner/{learner_id}/practice-mode
Content-Type: application/json

{
  "practiceMode": true  // or false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Practice mode enabled",
  "previous_mode": false,
  "new_mode": true
}
```

**Learner Model Schema:**
```json
{
  "learner_id": "...",
  "practice_mode": false,  // Default: disabled
  // ... other fields
}
```

**Backend Function:**
```python
# In backend/app/tools.py
record_assessment_and_check_completion(
    learner_id,
    concept_id,
    is_correct,
    confidence,
    question_type,
    practice_mode=True  # Skip mastery recording
)
```

## Feature 3: Growth Mindset Encouragement

### What is Growth Mindset Encouragement?

Automatic detection of struggle with supportive messages that reframe mistakes as learning opportunities.

### How It Works

**Struggle Detection:**
- **Consecutive incorrect** (2+ wrong in a row)
- **Moderate struggle** (< 40% recent performance)
- **Mild struggle** (< 60% recent performance)

**Encouragement Messages:**

**Consecutive Incorrect:**
> 💪 Learning is a journey! These mistakes are valuable feedback. Each wrong answer helps you understand better. Keep going!

**Moderate Struggle:**
> 🌟 This is challenging, but you're making progress! Consider trying the preview mode or practice mode to explore without pressure. Remember: struggle means your brain is growing!

**Mild Struggle:**
> 👍 You're working through some tricky material. That's exactly how learning happens! Take your time, and remember you can always review the preview.

### Implementation

**Backend Function:**
```python
# In backend/app/tools.py
struggle_info = detect_struggle(learner_id, concept_id)
# Returns: {
#   "struggle_level": "moderate",
#   "recent_performance": 0.35,
#   "consecutive_incorrect": 2,
#   "encouragement_message": "🌟 This is challenging..."
# }
```

**Response Integration (backend/app/main.py):**
```python
assessment_result = {
    "type": "assessment-result",
    "score": 1.0 if is_correct else 0.0,
    "feedback": feedback_text,
    "encouragement": encouragement_message,  # Added
    "practiceMode": practice_mode,  # Added
    // ...
}
```

## Configuration Constants

All pedagogical settings are centralized in `backend/app/constants.py`:

```python
# Adaptive Scaffolding
DIFFICULTY_DOWN_THRESHOLD = 0.40
DIFFICULTY_UP_THRESHOLD = 0.85
DIFFICULTY_ASSESSMENT_WINDOW = 5
MASTERY_THRESHOLD_STRUGGLING = 0.70
MASTERY_THRESHOLD_NORMAL = 0.75
MASTERY_THRESHOLD_EXCELLING = 0.85

# Practice Mode
PRACTICE_MODE_ENABLED = True
PRACTICE_MODE_DEFAULT = False
PRACTICE_MODE_SHOWS_ANSWERS = True
PRACTICE_MODE_ALLOWS_HINTS = True
PRACTICE_MODE_COUNTS_TOWARD_MASTERY = False

# Encouragement
STRUGGLE_THRESHOLD_MILD = 0.60
STRUGGLE_THRESHOLD_MODERATE = 0.40
STRUGGLE_DETECTION_WINDOW = 5
ENCOURAGEMENT_AFTER_N_INCORRECT = 2
```

## Frontend Integration (To Be Implemented)

### Practice Mode Toggle

**Location:** Learning interface header

**UI Component:**
```jsx
<PracticeModeToggle
  enabled={practiceMode}
  onChange={(enabled) => togglePracticeMode(enabled)}
/>
```

**Visual Indicator:**
- 🎯 **Practice Mode** (green badge) - When enabled
- 📊 **Graded Mode** (blue badge) - When disabled

### Encouragement Display

**Location:** Assessment result screen

**UI Component:**
```jsx
{encouragement && (
  <EncouragementMessage message={encouragement} />
)}
```

**Visual Style:**
- Warm color scheme (orange/yellow gradient)
- Icon indicating support (💪, 🌟, 👍)
- Friendly, non-judgmental tone

### Difficulty Indicator (Optional)

**Location:** Debug panel or settings

**Display:**
- Current difficulty level
- Recent performance graph
- Adaptive threshold visualization

## Benefits

### 1. Reduced Discouragement
- **Problem:** High mastery threshold (85%) felt unattainable
- **Solution:** Adaptive thresholds (70-85%) based on performance
- **Impact:** More achievable goals → sustained motivation

### 2. Increased Agency
- **Problem:** Learners felt trapped in assessment cycle
- **Solution:** Practice mode for stress-free exploration
- **Impact:** Psychological safety → willingness to experiment

### 3. Appropriate Challenge
- **Problem:** One-size-fits-all difficulty caused frustration
- **Solution:** Dynamic difficulty adjustment (easier/appropriate/harder)
- **Impact:** Flow state → optimal learning

### 4. Growth Mindset
- **Problem:** Mistakes felt like failures
- **Solution:** Encouragement messages reframe errors as learning
- **Impact:** Resilience → persistence through difficulty

## Testing

### Backend Testing

**Test adaptive scaffolding:**
```bash
cd backend
python -c "
from app.tools import select_question_difficulty
# Simulate struggling learner (20% performance)
difficulty = select_question_difficulty('test-learner', 'concept-001')
print(f'Difficulty: {difficulty}')  # Should be 'easier'
"
```

**Test practice mode:**
```bash
# Toggle practice mode
curl -X PUT http://localhost:8000/learner/test-learner/practice-mode \
  -H "Content-Type: application/json" \
  -d '{"practiceMode": true}'

# Submit answer in practice mode (won't count toward mastery)
curl -X POST http://localhost:8000/submit-response \
  -H "Content-Type: application/json" \
  -d '{
    "learner_id": "test-learner",
    "current_concept": "concept-001",
    "user_answer": 0,
    "correct_answer": 1,
    "is_correct": false
  }'
```

### Manual Testing Checklist

- [ ] Adaptive difficulty adjusts after 5 questions
- [ ] Practice mode toggle updates learner model
- [ ] Practice mode assessments don't affect mastery score
- [ ] Encouragement messages appear after 2+ incorrect answers
- [ ] Mastery threshold adapts to performance level

## Future Enhancements

1. **Frontend Practice Mode Toggle** - Visual UI component
2. **Difficulty Visualization** - Show current difficulty level to learners
3. **Performance Analytics** - Dashboard showing difficulty progression
4. **Hint System** - Contextual hints in practice mode
5. **Preview Skip Option** - Let learners skip directly to assessment
6. **Restart Diagnostic** - Ability to restart if learner feels unprepared

## Research References

- **Zone of Proximal Development** (Vygotsky, 1978) - Adaptive scaffolding
- **Self-Determination Theory** (Deci & Ryan, 1985) - Autonomy/choice
- **Growth Mindset** (Dweck, 2006) - Reframing mistakes
- **Flow Theory** (Csikszentmihalyi, 1990) - Optimal challenge

## Questions?

**Q: Will this make the course too easy?**
A: No! The system still maintains standards:
- Normal performance → 75% threshold (reasonable)
- High performance → 85% threshold (challenging)
- Struggling learners get temporary 70% threshold for confidence building

**Q: Can learners abuse practice mode to skip learning?**
A: Practice mode is an option, not default. Learners still need graded mode to progress. It's a tool for exploration, not avoidance.

**Q: How do I adjust the thresholds?**
A: Edit `backend/app/constants.py`:
```python
DIFFICULTY_DOWN_THRESHOLD = 0.40  # Adjust this
MASTERY_THRESHOLD_NORMAL = 0.75   # Adjust this
```

---

*Implementation completed: 2025-11-01*
*Backend features tested and ready ✅*
*Frontend integration pending 🔄*
