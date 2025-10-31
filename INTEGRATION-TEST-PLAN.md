# Integration Test Plan
## Adaptive Latin Learning Platform

**Purpose**: Verify frontend-backend integration, API contracts, data flows, and error handling across critical user journeys.

**Test Environment**:
- Backend: http://localhost:8000
- Frontend: http://localhost:5173

---

## 🎯 Critical User Journeys

### Journey 1: New User Onboarding
**Flow**: Welcome → Name Entry → Onboarding Questions → First Content

| Step | Frontend Action | Backend Endpoint | Expected Response | Validation |
|------|----------------|------------------|-------------------|------------|
| 1.1 | User enters name "Test User" | - | Local state update | Name stored in state |
| 1.2 | User clicks "Begin Learning" | - | Navigate to onboarding | Shows onboarding component |
| 1.3 | User completes onboarding profile | `POST /start` | 201 Created | Returns `{"success": true, "message": "..."}` |
| 1.4 | Frontend requests initial content | `GET /progress/{learner_id}` | 200 OK | Returns progress with current_concept |
| 1.5 | Frontend loads first question | `POST /generate-content?stage=preview OR start` | 200 OK | Returns content object with type, question, etc. |

**Data Contract Checks**:
- POST /start request body: `{learner_id, name, profile: {learningStyle, priorExperience, interests}}`
- Response includes: `success`, `message`, `learner_id`
- Profile.learningStyle must be: "visual" | "practice" | "connections"
- Profile.priorExperience must be: "none" | "beginner" | "intermediate"

**Error Scenarios**:
- [ ] Empty name → Frontend shows validation error
- [ ] Duplicate learner_id → Backend handles gracefully
- [ ] Missing API key → Backend returns 500, frontend shows connection error
- [ ] Network timeout → Frontend shows retry option

---

### Journey 2: Question → Answer → Confidence → Feedback
**Flow**: Display Question → User Answers → Confidence Rating → Receive Feedback → Next Content

| Step | Frontend Action | Backend Endpoint | Expected Response | Validation |
|------|----------------|------------------|-------------------|------------|
| 2.1 | Display multiple-choice question | - | - | Shows scenario, question, 4 options |
| 2.2 | User selects option index 2 | - | Local state | Shows confidence slider |
| 2.3 | User rates confidence (3/4 stars) | `POST /submit-response` | 200 OK | Returns assessment-result with feedback |
| 2.4 | Frontend displays feedback | - | - | Shows score, feedback, calibration message |
| 2.5 | Frontend shows "_next_content" | - | - | Renders next question or remediation |

**Data Contract Checks**:
- POST /submit-response request body:
  ```json
  {
    "learner_id": "string",
    "question_type": "multiple-choice" | "fill-blank" | "dialogue",
    "user_answer": 2,
    "correct_answer": 1,
    "confidence": 3,  // 1-4 stars
    "current_concept": "concept-001",
    "question_text": "string",
    "scenario_text": "string",
    "options": ["opt1", "opt2", "opt3", "opt4"]
  }
  ```
- Response structure:
  ```json
  {
    "type": "assessment-result",
    "score": 0.0,
    "feedback": "string",
    "correctAnswer": 1,
    "calibration": "overconfident",
    "_next_content": {...}
  }
  ```

**Confidence Scale Consistency**:
- [ ] Frontend sends confidence 1-4 (not 1-5)
- [ ] Backend accepts confidence 1-4 (validation in Pydantic model)
- [ ] Confidence slider shows 4 stars (not 5)
- [ ] Backend calibration logic uses 1-4 scale (confidence.py)

**Error Scenarios**:
- [ ] Confidence = 5 → Backend rejects with 422 validation error
- [ ] Missing required field → Backend returns 422, frontend shows error
- [ ] Network failure during submit → Frontend retries or shows error
- [ ] Backend timeout (>60s) → Frontend receives timeout error

---

### Journey 3: Tutor Chat Interaction
**Flow**: Click Tutor Button → Enter Question → Receive Response → Continue Conversation

| Step | Frontend Action | Backend Endpoint | Expected Response | Validation |
|------|----------------|------------------|-------------------|------------|
| 3.1 | User clicks floating tutor button | - | Opens chat modal | Shows chat interface |
| 3.2 | User types "Why is it 'puellam'?" | `POST /chat` | 200 OK | Returns assistant message |
| 3.3 | Display tutor response | - | - | Markdown rendered correctly |
| 3.4 | User sends follow-up question | `POST /chat` | 200 OK | Maintains conversation context |

**Data Contract Checks**:
- POST /chat request body:
  ```json
  {
    "learner_id": "string",
    "concept_id": "concept-001",
    "message": "Why is it 'puellam'?",
    "conversation_history": []  // Optional
  }
  ```
- Response: `{"success": true, "message": "string", "conversation_history": [...]}`

**Rate Limiting Checks**:
- [ ] 30 requests/minute limit enforced on /chat
- [ ] Frontend handles 429 Too Many Requests gracefully
- [ ] Shows "Please wait" message to user

**Error Scenarios**:
- [ ] Empty message → Frontend validates before sending
- [ ] Rate limit exceeded → Frontend shows cooldown message
- [ ] Backend returns tool execution error → Frontend displays gracefully

---

### Journey 4: Progress Tracking
**Flow**: Answer Multiple Questions → Check Progress Dashboard → See Mastery Updates

| Step | Frontend Action | Backend Endpoint | Expected Response | Validation |
|------|----------------|------------------|-------------------|------------|
| 4.1 | Frontend polls progress | `GET /progress/{learner_id}` | 200 OK | Returns updated progress |
| 4.2 | Display mastery percentage | - | - | Shows 0-100% based on average_score |
| 4.3 | Show assessment count | - | - | Displays total_assessments |
| 4.4 | Display concept title | - | - | Shows current concept name |

**Data Contract Checks**:
- Response structure:
  ```json
  {
    "success": true,
    "learner_id": "string",
    "current_concept": "concept-001",
    "overall_progress": {
      "average_score": 0.75,
      "total_assessments": 5,
      "average_confidence": 3.2,
      "calibration_accuracy": 0.6
    },
    "concept_progress": {
      "concept-001": {
        "mastery": 0.75,
        "assessment_count": 5
      }
    }
  }
  ```

**Calculation Consistency**:
- [ ] Frontend mastery percentage = backend mastery * 100
- [ ] Mastery threshold 0.85 matches between frontend/backend
- [ ] Progress bar updates after each submission

---

## 🔌 API Contract Verification

### Endpoint: POST /start
**Request Schema**:
```typescript
{
  learner_id: string;
  name: string;
  profile: {
    learningStyle: 'visual' | 'practice' | 'connections';
    priorExperience: 'none' | 'beginner' | 'intermediate';
    interests: string;
  }
}
```

**Response Schema**:
```typescript
{
  success: boolean;
  message: string;
  learner_id: string;
}
```

**Tests**:
- [ ] All required fields present
- [ ] Enum values validated
- [ ] learner_id format: "learner-{timestamp}"
- [ ] 201 status code returned

---

### Endpoint: POST /generate-content
**Query Parameters**: `learner_id`, `stage`

**Stage Values**:
- [ ] "preview" - Returns lesson/table/example
- [ ] "start" - Returns diagnostic question
- [ ] "practice" - Returns practice question
- [ ] "assess" - Returns dialogue question
- [ ] "remediate" - Returns remediation content
- [ ] "reinforce" - Returns reinforcement content

**Response Types**:
- [ ] "multiple-choice" - Has: scenario, question, options[], correctAnswer
- [ ] "fill-blank" - Has: sentence, blanks[], correctAnswers[], hints[]
- [ ] "dialogue" - Has: question
- [ ] "lesson" - Has: title, html
- [ ] "paradigm-table" - Has: title, table_data
- [ ] "example-set" - Has: title, examples[]

**Content Validation**:
- [ ] All multiple-choice questions have 4 unique options
- [ ] correctAnswer index is valid (0-3)
- [ ] Fill-blank: blanks.length === correctAnswers.length
- [ ] show_confidence field present (boolean)

---

### Endpoint: POST /submit-response
**Request Schema**:
```typescript
{
  learner_id: string;
  question_type: 'multiple-choice' | 'fill-blank' | 'dialogue';
  user_answer: number | string;
  correct_answer: number | string;
  confidence: number | null;  // 1-4 or null if skipped
  current_concept: string;
  question_text?: string;
  scenario_text?: string;
  options?: string[];
}
```

**Response Type**: `assessment-result`
```typescript
{
  type: 'assessment-result';
  score: number;  // 0.0 or 1.0
  feedback: string;
  correctAnswer: number | string;
  calibration: 'calibrated' | 'overconfident' | 'underconfident';
  _next_content: ContentObject;
}
```

**Tests**:
- [ ] Confidence validation: 1 ≤ confidence ≤ 4
- [ ] Calibration types match expected values
- [ ] _next_content is valid content type
- [ ] Feedback message is non-empty

---

## ⚠️ Error Handling Integration

### HTTP Status Codes
| Status | Backend Scenario | Frontend Handling | User Message |
|--------|-----------------|-------------------|--------------|
| 400 | Bad request format | Show validation error | "Invalid request format" |
| 401 | Invalid API key | Show connection error | "Service temporarily unavailable" |
| 404 | Learner not found | Prompt to restart | "Session expired. Please start over." |
| 413 | Request too large (>1MB) | Should never happen | "Request too large" |
| 422 | Validation error (Pydantic) | Show field-specific error | "Invalid data: {detail}" |
| 429 | Rate limit exceeded | Show cooldown timer | "Please wait {X} seconds" |
| 500 | Internal server error | Show retry option | "Something went wrong. Please try again." |
| 503 | Service unavailable | Show maintenance message | "Service temporarily unavailable" |

**Test Each Scenario**:
- [ ] Trigger 422 by sending confidence=5
- [ ] Trigger 404 by using non-existent learner_id
- [ ] Trigger 429 by rapid-fire requests to /chat
- [ ] Simulate 500 by breaking backend temporarily
- [ ] Check frontend never shows raw error messages

---

## 🔒 Security Integration Tests

### CORS Configuration
- [ ] Frontend on :5173 can access backend on :8000
- [ ] Credentials are included in requests
- [ ] Only GET/POST/OPTIONS methods allowed
- [ ] Only whitelisted headers accepted
- [ ] Wildcard origins blocked in production

### Rate Limiting
- [ ] POST /start: Max 10/minute per IP
- [ ] POST /chat: Max 30/minute per IP
- [ ] POST /generate-content: Max 60/minute per IP
- [ ] POST /submit-response: Max 60/minute per IP
- [ ] Frontend handles 429 responses gracefully

### Input Sanitization
- [ ] Special characters in name don't break UI
- [ ] Script tags in interests field are escaped
- [ ] Markdown in chat doesn't execute XSS
- [ ] Long strings (>1000 chars) are truncated

---

## 🎨 UI/UX Integration Tests

### Loading States
- [ ] Onboarding shows loading during POST /start
- [ ] Content shows skeleton/spinner during generation
- [ ] Submit button disabled during POST /submit-response
- [ ] Chat shows typing indicator during POST /chat
- [ ] Progress dashboard shows loading on initial fetch

### Error Recovery
- [ ] Failed content generation shows retry button
- [ ] Network error shows "Try Again" option
- [ ] Timeout shows specific timeout message
- [ ] User can recover without refreshing page

### State Consistency
- [ ] localStorage syncs with backend state
- [ ] Progress dashboard updates after submission
- [ ] Confidence slider resets after submission
- [ ] Content index increments correctly
- [ ] Browser refresh maintains learner session

---

## 🧪 Edge Case Tests

### Content Edge Cases
- [ ] Empty scenario text handled
- [ ] Very long option text (>200 chars)
- [ ] Special characters in Latin text (macrons: ā, ē, etc.)
- [ ] Multiple blanks in fill-blank (3+)
- [ ] Cumulative review questions (is_cumulative: true)

### Learner Model Edge Cases
- [ ] First question (no history)
- [ ] Mastery threshold reached (≥0.85)
- [ ] Zero assessments completed
- [ ] Skip confidence rating (confidence: null)
- [ ] Switch concepts mid-session

### Timing Edge Cases
- [ ] Submit before content fully loaded
- [ ] Multiple rapid submissions
- [ ] Long API response (>30s but <60s)
- [ ] Backend restart during active session

---

## 📊 Test Execution Checklist

### Pre-Test Setup
- [ ] Backend running on :8000
- [ ] Frontend running on :5173
- [ ] Valid ANTHROPIC_API_KEY in .env
- [ ] Resource bank directory exists
- [ ] Clean browser (no cached data)

### Manual Test Execution
1. **Onboarding Flow** (5 min)
   - [ ] Complete full onboarding
   - [ ] Check browser console for errors
   - [ ] Verify localStorage has learner_id

2. **Question Flow** (10 min)
   - [ ] Answer 5 questions with varying confidence
   - [ ] Check each response has feedback
   - [ ] Verify calibration messages appear
   - [ ] Confirm progress updates

3. **Tutor Chat** (5 min)
   - [ ] Send 3 questions
   - [ ] Verify context maintained
   - [ ] Check rate limiting (31st request)

4. **Error Scenarios** (10 min)
   - [ ] Disconnect internet → Reconnect → Continue
   - [ ] Submit invalid confidence (5 stars)
   - [ ] Send empty chat message
   - [ ] Refresh page mid-question

5. **Progress Dashboard** (5 min)
   - [ ] Verify mastery percentage calculation
   - [ ] Check assessment count accuracy
   - [ ] Confirm concept title displayed

### Automated Test Script
```bash
# Run with: bash integration-test.sh

echo "Testing POST /start..."
curl -X POST http://localhost:8000/start \
  -H "Content-Type: application/json" \
  -d '{
    "learner_id": "test-learner-001",
    "name": "Test User",
    "profile": {
      "learningStyle": "connections",
      "priorExperience": "none",
      "interests": "Roman history"
    }
  }'

echo "\nTesting GET /progress..."
curl http://localhost:8000/progress/test-learner-001

echo "\nTesting POST /generate-content..."
curl -X POST "http://localhost:8000/generate-content?learner_id=test-learner-001&stage=start"

echo "\nTesting POST /submit-response..."
curl -X POST http://localhost:8000/submit-response \
  -H "Content-Type: application/json" \
  -d '{
    "learner_id": "test-learner-001",
    "question_type": "multiple-choice",
    "user_answer": 0,
    "correct_answer": 1,
    "confidence": 3,
    "current_concept": "concept-001",
    "question_text": "Test question",
    "scenario_text": "Test scenario",
    "options": ["A", "B", "C", "D"]
  }'

echo "\nTesting POST /chat..."
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "learner_id": "test-learner-001",
    "concept_id": "concept-001",
    "message": "Explain first declension"
  }'
```

---

## 🐛 Known Issues to Test

From recent fixes:
- [ ] Confidence scale is 1-4 everywhere (was mixed 1-4 and 1-5)
- [ ] Assessment-result wraps next content (was returning raw question)
- [ ] Hardcoded concept-001 replaced with dynamic (App.jsx:242)
- [ ] CORS restricted to needed methods/headers only
- [ ] Rate limiting active on all endpoints
- [ ] Prompt injection sanitization active

---

## 📝 Test Report Template

**Date**: _______________
**Tester**: _______________
**Environment**: Backend v____ / Frontend v____

### Journey Test Results
- [ ] Onboarding: PASS / FAIL - Notes: __________
- [ ] Question Flow: PASS / FAIL - Notes: __________
- [ ] Tutor Chat: PASS / FAIL - Notes: __________
- [ ] Progress Tracking: PASS / FAIL - Notes: __________

### API Contract Results
- [ ] POST /start: PASS / FAIL
- [ ] POST /generate-content: PASS / FAIL
- [ ] POST /submit-response: PASS / FAIL
- [ ] POST /chat: PASS / FAIL
- [ ] GET /progress: PASS / FAIL

### Error Handling Results
- [ ] Network errors: PASS / FAIL
- [ ] Validation errors: PASS / FAIL
- [ ] Rate limiting: PASS / FAIL
- [ ] Timeout handling: PASS / FAIL

### Critical Bugs Found
1. ________________________________
2. ________________________________
3. ________________________________

### Recommendations
1. ________________________________
2. ________________________________
3. ________________________________

---

**Next Steps After Testing**:
1. Fix any critical bugs discovered
2. Add automated E2E tests (Playwright/Cypress)
3. Set up CI/CD pipeline with integration tests
4. Monitor production for integration issues
