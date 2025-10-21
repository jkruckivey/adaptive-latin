# Confidence Tracking in Adaptive Learning System

**Purpose**: Gauge student confidence throughout learning journey to build metacognitive awareness and improve AI agent decision-making

**Last Updated**: 2025-10-21

---

## Why Track Confidence?

### Pedagogical Benefits

**1. Metacognitive Development**
Students learn to accurately assess their own understanding - a critical skill for lifelong learning.

**2. Identify Knowledge Gaps vs. Confidence Gaps**
- **Overconfident**: "I know this!" but scores low → Need to recognize misconceptions
- **Underconfident**: "I'm confused" but scores high → Need encouragement and reassurance
- **Calibrated**: Confidence matches performance → Healthy self-awareness

**3. Early Warning System**
Sudden drops in confidence (even with good performance) may indicate:
- Approaching cognitive limits
- Need for break or different approach
- Anxiety or frustration building

**4. Personalized Intervention**
The AI agent can respond differently based on confidence-performance patterns:
- High confidence + Low performance → "Let's review this concept - there's a gap we need to address"
- Low confidence + High performance → "You're doing better than you think! Trust your understanding"
- Low confidence + Low performance → "This is challenging. Let's break it down into smaller pieces"

### Research Basis

**Dunning-Kruger Effect**: People with low competence often overestimate their ability. Tracking confidence helps identify and address this.

**Calibration Theory**: Experts are better at judging what they know vs. don't know. We want to develop this skill in learners.

**Self-Regulated Learning**: Metacognitive monitoring (knowing what you know) is a key component of effective learning.

---

## Implementation Options

### Option 1: Post-Assessment Confidence Rating ⭐ RECOMMENDED
**When**: After student submits answer, before seeing results
**How**: Simple 1-5 scale

**Example Flow**:
```
AI: "Look at this sentence: 'Puellae aquam do.' What case is 'puellae' and why?"

Student: "I think it's dative because 'do' means 'I give' and you give TO someone."

AI: "Before I give you feedback, how confident are you in this answer?"
    ○ 1 - Just guessing
    ○ 2 - Not very confident
    ○ 3 - Somewhat confident
    ○ 4 - Quite confident
    ○ 5 - Very confident

Student: [selects 4]

AI: "You're absolutely right! Puellae is dative - 'to the girl.' And I'm glad
     to see your confidence (4/5) matches your strong understanding. You
     correctly reasoned from the verb 'do' to the indirect object function."
```

**Data Collected**:
```json
{
  "assessment_id": "assess-001-dialogue-6",
  "student_response": "I think it's dative because...",
  "pre_result_confidence": 4,
  "actual_score": 0.95,
  "confidence_accuracy": "calibrated",
  "confidence_error": 0.15
}
```

**Pros**:
- Natural insertion point in assessment flow
- Captures confidence before feedback influence
- Easy to implement
- Clear data for analysis

**Cons**:
- Adds step after every assessment (could feel tedious)
- May interrupt flow

---

### Option 2: Concept-Level Confidence Check
**When**: Before starting a new concept and after mastering current concept
**How**: Rating scale + optional comment

**Example Flow**:
```
[Student has just mastered Concept 001]

AI: "Excellent work! You've demonstrated mastery of first declension nouns
     (confidence score: 0.88). Before we move to first conjugation verbs,
     let's do a quick check-in.

     How confident do you feel with first declension now?
     ○ 1 - Still very unsure
     ○ 2 - Somewhat shaky
     ○ 3 - Adequately confident
     ○ 4 - Quite confident
     ○ 5 - Very confident

     (Optional) Anything still unclear about first declension?"

Student: [selects 4] "I'm pretty confident, though sometimes I still mix up
          when puellae is genitive vs. dative."

AI: "That's great self-awareness! The puellae ambiguity is exactly the kind
     of thing that takes practice. As you work with more complex sentences
     in upcoming concepts, you'll get more context clues. Your mastery score
     (0.88) matches your confidence (4/5), which shows healthy calibration.
     Ready for first conjugation verbs?"
```

**Data Collected**:
```json
{
  "concept_id": "concept-001",
  "concept_confidence_rating": 4,
  "concept_mastery_score": 0.88,
  "confidence_comment": "still mix up when puellae is genitive vs. dative",
  "timestamp": "2025-10-17T16:50:00Z",
  "calibration": "well_calibrated"
}
```

**Pros**:
- Less intrusive (only at concept transitions)
- Allows reflection on full concept
- Optional comment captures nuance
- Natural point for metacognitive reflection

**Cons**:
- Lower granularity (per concept, not per assessment)
- May not catch confidence shifts during concept

---

### Option 3: Prediction + Reflection Cycle
**When**: Before attempting assessment, then after seeing results
**How**: Predict performance, then reflect on accuracy

**Example Flow**:
```
AI: "I'm going to give you a translation exercise with 5 sentences. Before
     you start, how many do you think you'll get correct?

     ○ 0-1 (I'm really struggling)
     ○ 2-3 (I'll get some right)
     ○ 4-5 (I think I'll do well)"

Student: [selects "4-5"]

[Student completes exercise, scores 3/5]

AI: "You got 3 out of 5 correct - good work! You predicted you'd get 4-5.
     Let's reflect: Were there any that surprised you? What made them harder
     than you expected?"

Student: "I thought I understood ablative better than I do. The 'with/by/from'
          distinction is still confusing."

AI: "That's valuable insight. Many students struggle with ablative uses at
     first. Let's spend some time on that before moving forward..."
```

**Data Collected**:
```json
{
  "task_id": "applied-001-1",
  "predicted_score": "4-5 out of 5",
  "actual_score": 0.60,
  "reflection": "thought I understood ablative better",
  "identified_gap": "ablative uses (with/by/from)",
  "overconfidence_magnitude": 0.20
}
```

**Pros**:
- Develops prediction skills (metacognition)
- Reflection after results promotes growth mindset
- Identifies specific areas where confidence was misplaced

**Cons**:
- More time-intensive (two interaction points)
- Requires more cognitive effort from student

---

### Option 4: Real-Time Confidence During Dialogue
**When**: Embedded in conversational assessment
**How**: Ask confidence before revealing if answer is correct

**Example Flow**:
```
AI: "What case is 'viam' in the sentence 'Puella viam videt'?"

Student: "Accusative, because it's the direct object."

AI: "On a scale of 1-5, how sure are you?"

Student: "5 - I'm very sure."

AI: "You're exactly right, and your confidence is justified! Viam is accusative,
     the direct object of videt. Let's try a trickier one..."

[Later in same session]

AI: "What about 'puellae' in 'Vita puellae est bona'?"

Student: "I think... genitive? Because it shows possession?"

AI: "How confident?"

Student: "Maybe a 2. I'm not really sure."

AI: "Actually, you're correct! It IS genitive (of the girl / the girl's life).
     I notice you were less confident on this one even though you got it right.
     What made you uncertain?"

Student: "I saw -ae and thought it might be nominative plural."

AI: "Ah! Great awareness of the ambiguity. You correctly used context (vita is
     singular) to rule out nominative plural. Your reasoning was sound - trust
     it more!"
```

**Data Collected**:
```json
{
  "dialogue_exchange_1": {
    "question": "case of viam",
    "answer": "accusative",
    "confidence": 5,
    "correct": true,
    "agent_response": "justified confidence"
  },
  "dialogue_exchange_2": {
    "question": "case of puellae",
    "answer": "genitive",
    "confidence": 2,
    "correct": true,
    "agent_response": "underconfident - encourage trust in reasoning"
  }
}
```

**Pros**:
- High granularity (per question within dialogue)
- AI can immediately address confidence-performance gaps
- Builds calibration in real-time

**Cons**:
- Could feel repetitive if asked too often
- Interrupts conversational flow
- May make assessment feel mechanical

---

### Option 5: Visual Confidence Journey (Dashboard)
**When**: Always available, updated in real-time
**How**: Graph showing confidence vs. performance over time

**Visual Example**:
```
Confidence vs. Performance Over Time

Confidence (self-reported)  ●━━━━●━━━●
Performance (actual score)  ●━●━━━●━━━●
                           ↑         ↑
                         Low        High
                      Calibration  Calibration

Concept 001: First Declension
├─ Assessment 1: Overconfident (predicted 4, scored 0.60)
├─ Assessment 2: Calibrated (predicted 3, scored 0.75)
├─ Assessment 3: Calibrated (predicted 4, scored 0.85)
└─ Assessment 4: Underconfident (predicted 3, scored 0.95)

Trend: Your calibration is improving! You're getting better at
       predicting your performance.
```

**Data Displayed**:
- Confidence trajectory
- Performance trajectory
- Calibration accuracy over time
- Specific instances of over/underconfidence
- Metacognitive growth indicators

**Pros**:
- Powerful metacognitive tool
- Students SEE their calibration improve
- Can review journey at any time
- Motivating to watch calibration accuracy increase

**Cons**:
- Requires frontend development
- Needs data from other confidence tracking methods
- Could be overwhelming if too much data

---

## Recommended Approach: Hybrid System

Combine **Option 1** (Post-Assessment) and **Option 2** (Concept-Level) for optimal balance:

### During Assessments (Option 1)
- After each dialogue/written/applied task
- Quick 1-5 confidence rating
- Before showing results
- Lightweight, non-intrusive

### At Concept Transitions (Option 2)
- Before starting new concept
- Reflect on mastered concept confidence
- Optional qualitative comment
- Deeper metacognitive moment

### Visualize Progress (Option 5)
- Show confidence journey over time
- Highlight calibration improvements
- Celebrate metacognitive growth

---

## Integration into Existing Architecture

### 1. Learner Model Schema Updates

**Add to concept_mastery object**:
```json
{
  "concept-001": {
    "status": "mastered",
    "confidence": 0.88,
    "self_reported_confidence": 4.0,
    "confidence_calibration": "well_calibrated",
    "confidence_history": [
      {
        "assessment_id": "dialogue-001-1",
        "timestamp": "2025-10-15T09:30:00Z",
        "self_confidence": 3,
        "actual_score": 0.75,
        "calibration": "calibrated",
        "error": 0.00
      },
      {
        "assessment_id": "dialogue-001-2",
        "timestamp": "2025-10-16T11:15:00Z",
        "self_confidence": 5,
        "actual_score": 0.85,
        "calibration": "slightly_overconfident",
        "error": 0.15
      },
      {
        "assessment_id": "written-001-1",
        "timestamp": "2025-10-17T14:00:00Z",
        "self_confidence": 4,
        "actual_score": 0.90,
        "calibration": "slightly_underconfident",
        "error": -0.10
      }
    ],
    "concept_end_confidence": {
      "rating": 4,
      "timestamp": "2025-10-17T16:50:00Z",
      "comment": "Pretty confident, though sometimes mix up puellae cases",
      "matches_mastery": true
    }
  }
}
```

**Add calibration tracking**:
```json
{
  "calibration_metrics": {
    "overall_calibration_accuracy": 0.85,
    "overconfidence_tendency": 0.10,
    "underconfidence_tendency": 0.05,
    "calibration_trend": "improving",
    "calibration_by_assessment_type": {
      "dialogue": 0.90,
      "written": 0.80,
      "applied": 0.75
    }
  }
}
```

### 2. Assessment Flow Updates

**Dialogue Assessment with Confidence**:
```
1. AI asks question
2. Student responds
3. AI asks: "How confident are you? (1-5)"
4. Student rates confidence
5. AI evaluates response using rubric
6. AI provides feedback that acknowledges confidence:
   - If calibrated: "Your confidence matches your understanding!"
   - If overconfident: "Let's review this - there's a gap to address"
   - If underconfident: "You're doing better than you think!"
7. AI updates learner model with confidence data
```

**Written/Applied Assessment with Confidence**:
```
1. AI presents task
2. Student completes task
3. AI asks: "How confident are you in your work? (1-5)"
4. Student rates confidence
5. AI evaluates using rubric
6. AI provides results + calibration feedback
7. AI updates learner model
```

### 3. AI Agent Prompt Updates

**Add to system prompt**:
```
## Confidence Tracking

After each assessment, ask the learner to rate their confidence (1-5):
- 1: Just guessing
- 2: Not very confident
- 3: Somewhat confident
- 4: Quite confident
- 5: Very confident

Compare their self-reported confidence to their actual score:
- Score 0.00-0.20 = confidence should be 1
- Score 0.21-0.50 = confidence should be 2
- Score 0.51-0.75 = confidence should be 3
- Score 0.76-0.90 = confidence should be 4
- Score 0.91-1.00 = confidence should be 5

Calibration Error = |self_confidence - expected_confidence|

If error ≤ 1: "calibrated" (good metacognitive awareness)
If error = 2: "moderately miscalibrated" (some gap)
If error ≥ 3: "significantly miscalibrated" (major gap)

## Responding to Confidence-Performance Gaps

**Overconfident (high confidence, low score)**:
- Don't shame: "I can see why you felt confident - this is tricky!"
- Identify gap: "Let's look at where the confusion is..."
- Provide targeted review
- Build accurate self-assessment

**Underconfident (low confidence, high score)**:
- Encourage: "You're doing better than you think!"
- Point out correct reasoning: "Your logic here was sound..."
- Build justified confidence
- Reinforce strengths

**Well-calibrated**:
- Celebrate: "Your confidence matches your understanding - great self-awareness!"
- Encourage continued metacognitive monitoring

## Use Confidence Data for Decisions

When deciding whether to progress/continue/regress:
- Well-calibrated + high scores = strong candidate for progression
- Overconfident + low scores = needs intervention before progression
- Underconfident + high scores = encourage, then progress
- Low confidence + low scores = provide extra support, possibly regress
```

### 4. New Tool for AI Agent

**Add to backend/tools.py**:
```python
def track_confidence(learner_id: str, assessment_id: str,
                    self_confidence: int, actual_score: float) -> dict:
    """
    Track confidence rating and calculate calibration.

    Args:
        learner_id: Student identifier
        assessment_id: Which assessment this is for
        self_confidence: Student's 1-5 rating
        actual_score: Actual performance (0.0-1.0)

    Returns:
        Calibration analysis
    """
    # Map score to expected confidence
    if actual_score <= 0.20:
        expected_confidence = 1
    elif actual_score <= 0.50:
        expected_confidence = 2
    elif actual_score <= 0.75:
        expected_confidence = 3
    elif actual_score <= 0.90:
        expected_confidence = 4
    else:
        expected_confidence = 5

    # Calculate calibration error
    calibration_error = abs(self_confidence - expected_confidence)

    # Categorize calibration
    if calibration_error <= 1:
        calibration = "calibrated"
    elif calibration_error == 2:
        calibration = "moderately_miscalibrated"
    else:
        calibration = "significantly_miscalibrated"

    # Determine direction
    if self_confidence > expected_confidence:
        direction = "overconfident"
    elif self_confidence < expected_confidence:
        direction = "underconfident"
    else:
        direction = "calibrated"

    return {
        "self_confidence": self_confidence,
        "actual_score": actual_score,
        "expected_confidence": expected_confidence,
        "calibration_error": calibration_error,
        "calibration": calibration,
        "direction": direction,
        "timestamp": datetime.now().isoformat()
    }
```

---

## Example: Confidence-Aware Assessment Session

```
AI: "Let's test your understanding of first declension. What case is 'puellam'
     and what function does it serve?"

Student: "It's accusative, which is the direct object case."

AI: "How confident are you in this answer? (1-5)"

Student: "5 - I'm sure."

AI: [Evaluates: Correct, score = 1.0]
    [Compares: self_confidence=5, expected=5, calibration="calibrated"]

    "Exactly right! Puellam is accusative, the direct object. And your
     confidence (5/5) perfectly matches your understanding - that's excellent
     self-awareness. Let's try something trickier..."

---

AI: "What about 'puellae' in the sentence 'Aquam puellae do'?"

Student: "Hmm... I think dative? Because you give TO someone?"

AI: "How confident?"

Student: "Maybe 2... I'm not sure."

AI: [Evaluates: Correct, score = 0.95 - excellent reasoning]
    [Compares: self_confidence=2, expected=5, calibration="underconfident"]

    "You're absolutely right, and your reasoning is sound! Puellae is dative -
     'to the girl.' I noticed you rated your confidence as 2/5, but your answer
     was excellent. What made you uncertain?"

Student: "I saw the -ae ending and wasn't sure if it was dative or genitive."

AI: "That's actually sophisticated thinking - you recognized the ambiguity! But
     your reasoning from the verb 'do' (I give) to 'gives TO someone' was
     perfect. Trust that logic more. You're developing good instincts!"

---

[After several more assessments]

AI: "You've completed 5 assessments on first declension. Let me show you
     something interesting about your confidence journey:

     Assessment 1: Predicted 5, scored 0.75 (overconfident)
     Assessment 2: Predicted 2, scored 0.95 (underconfident)
     Assessment 3: Predicted 4, scored 0.85 (calibrated!)
     Assessment 4: Predicted 4, scored 0.90 (calibrated!)
     Assessment 5: Predicted 5, scored 0.95 (calibrated!)

     Your calibration improved significantly! You're getting much better at
     knowing what you know. This metacognitive skill will serve you well as
     concepts get more complex. Ready to move on to first conjugation verbs?"
```

---

## Data Analysis Possibilities

### For Researchers / System Improvement

**Calibration Trends**:
- Does calibration improve over time? (Hypothesis: Yes, as metacognitive skills develop)
- Do certain concepts produce more overconfidence? (e.g., "easy" concepts like Concept 001 vs. hard ones like Concept 007)
- Do certain assessment types show better calibration? (dialogue vs. written vs. applied)

**Intervention Effectiveness**:
- When AI addresses overconfidence, does it improve in next assessment?
- When AI encourages underconfident students, do they gain confidence appropriately?

**Regression Predictions**:
- Can confidence-performance gaps predict when students will struggle with next concept?
- Is overconfidence a leading indicator of needing to regress?

**Learning Patterns**:
- Do well-calibrated students progress faster?
- Do underconfident students take longer (even when they're ready)?

---

## User Interface Mockup (Future)

```
┌─────────────────────────────────────────────────────────┐
│ Your Learning Journey - Concept 001                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Mastery Score: ████████░░ 88%                         │
│  Self-Confidence: ████████░░ 4/5                       │
│  Calibration: ✓ Well-calibrated                        │
│                                                         │
│  ┌───────────────────────────────────────────┐         │
│  │ Confidence vs. Performance Over Time      │         │
│  │                                           │         │
│  │  1.0 ●━━━━●━━━━●━━━━●  Performance       │         │
│  │  0.8 ●━●━━━●━━━━●━━━●  Confidence        │         │
│  │  0.6 ●━━━━━━━━━━━━━━━                    │         │
│  │  0.4 ━━━━━━━━━━━━━━━━                    │         │
│  │  0.2 ━━━━━━━━━━━━━━━━                    │         │
│  │      A1  A2  A3  A4  A5                  │         │
│  │                                           │         │
│  │  Insight: Your calibration improved       │         │
│  │  from A1 (overconfident) to A5            │         │
│  │  (well-calibrated). Great progress!       │         │
│  └───────────────────────────────────────────┘         │
│                                                         │
│  Recent Assessments:                                   │
│  • Dialogue 5: ✓ Correct, Confidence 5 → Calibrated   │
│  • Applied 2:  ✓ Correct, Confidence 2 → Underconf.   │
│  • Written 1:  ✓ Correct, Confidence 4 → Calibrated   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Implementation Priority

### Phase 1 (PoC - Must Have)
- ✓ Post-assessment confidence ratings (1-5 scale)
- ✓ Calibration calculation and tracking
- ✓ AI agent responds to confidence-performance gaps
- ✓ Store confidence data in learner model

### Phase 2 (Enhancement)
- Concept-level confidence check at transitions
- Calibration trend analysis
- Confidence-aware progression decisions

### Phase 3 (Advanced)
- Visual confidence journey dashboard
- Predictive analytics (confidence predicts struggles)
- Personalized calibration coaching

---

## Questions to Consider

1. **Frequency**: How often should we ask for confidence ratings? After every assessment or only selected ones?

2. **Scale**: Is 1-5 sufficient, or do you want more granularity (1-10)?

3. **Timing**: Post-assessment only, or also pre-assessment predictions?

4. **Intervention**: Should low confidence trigger extra support even if performance is good?

5. **Visualization**: How important is showing confidence journey to students vs. just using it for AI agent decisions?

---

## Next Steps

1. **Choose approach**: Which option(s) do you prefer? (Recommended: Hybrid of Options 1 + 2)

2. **Update Concept 001**: Add confidence ratings to existing assessments

3. **Update architecture docs**: Integrate confidence tracking into ARCHITECTURE.md

4. **Create example flows**: Show what confidence-aware assessment looks like in practice

5. **Test with pilot**: See how real students respond to confidence tracking

---

**What do you think? Which approach resonates with your vision for the confidence tracking feature?**
