import { useState } from 'react'
import './OnboardingQuestionBuilder.css'

function OnboardingQuestionBuilder({ courseData, onNext, onBack, onSaveDraft }) {
  const [onboardingQuestions, setOnboardingQuestions] = useState(
    courseData.onboarding_questions || []
  )
  const [useCustom, setUseCustom] = useState(
    courseData.onboarding_questions && courseData.onboarding_questions.length > 0
  )
  const [selectedTemplate, setSelectedTemplate] = useState('')

  // Domain-specific templates
  const getDomainTemplate = (domain) => {
    const domainLower = (domain || '').toLowerCase()

    if (domainLower.includes('excel') || domainLower.includes('spreadsheet')) {
      return [
        {
          type: 'question',
          question: `Tell me about yourself - what brings you to ${courseData.title}?`,
          placeholder: 'Your background, current role, and why you want to learn...',
          key: 'background'
        },
        {
          type: 'question',
          question: 'How much experience do you have with spreadsheets?',
          options: [
            { value: 'never', label: 'Never used them - complete beginner' },
            { value: 'basic', label: 'Basic - can enter data and simple formulas' },
            { value: 'intermediate', label: 'Intermediate - comfortable with common functions' },
            { value: 'advanced', label: 'Advanced - pivot tables, macros, complex analysis' }
          ],
          key: 'spreadsheetExperience',
          priorKnowledgeKey: 'level'
        },
        {
          type: 'question',
          question: 'What will you use these skills for?',
          placeholder: 'e.g., Work projects, personal budgeting, data analysis, school assignments...',
          key: 'useCase',
          priorKnowledgeKey: 'interests'
        }
      ]
    } else if (domainLower.includes('language') || domainLower.includes('latin') || domainLower.includes('spanish') || domainLower.includes('french')) {
      return [
        {
          type: 'question',
          question: `Tell me about yourself - what brings you to ${courseData.title}?`,
          placeholder: 'Your background and why you\'re interested in learning this language...',
          key: 'background'
        },
        {
          type: 'question',
          question: 'Have you studied this language before?',
          options: [
            { value: 'never', label: 'Never studied it' },
            { value: 'some', label: 'Some basics - a semester or two' },
            { value: 'intermediate', label: 'Solid foundation - can read simple texts' },
            { value: 'advanced', label: 'Advanced - comfortable with complex texts' }
          ],
          key: 'languageExperience',
          priorKnowledgeKey: 'level'
        },
        {
          type: 'question',
          question: 'What other languages do you know?',
          placeholder: 'List any languages you speak, even at a basic level...',
          key: 'otherLanguages',
          priorKnowledgeKey: 'relatedSkills'
        },
        {
          type: 'question',
          question: 'What\'s your goal with this language?',
          placeholder: 'Reading texts, travel, academic requirements, professional use...',
          key: 'goals',
          priorKnowledgeKey: 'interests'
        }
      ]
    } else if (domainLower.includes('programming') || domainLower.includes('code')) {
      return [
        {
          type: 'question',
          question: `Tell me about yourself - what brings you to ${courseData.title}?`,
          placeholder: 'Your background and what you hope to build or accomplish...',
          key: 'background'
        },
        {
          type: 'question',
          question: 'Do you have programming experience?',
          options: [
            { value: 'never', label: 'No programming experience' },
            { value: 'basic', label: 'Basic - written simple programs' },
            { value: 'intermediate', label: 'Intermediate - comfortable with data structures' },
            { value: 'advanced', label: 'Advanced - built complete applications' }
          ],
          key: 'codingExperience',
          priorKnowledgeKey: 'level'
        },
        {
          type: 'question',
          question: 'What programming languages do you already know?',
          placeholder: 'e.g., Python, JavaScript, Java, C++, or "None yet"...',
          key: 'knownLanguages',
          priorKnowledgeKey: 'relatedSkills'
        },
        {
          type: 'question',
          question: 'What do you want to build or accomplish?',
          placeholder: 'e.g., Web apps, data analysis, automation, games, career change...',
          key: 'goals',
          priorKnowledgeKey: 'interests'
        }
      ]
    } else {
      // Generic template
      return [
        {
          type: 'question',
          question: `Tell me about yourself - what brings you to ${courseData.title}?`,
          placeholder: 'Your background and why you\'re interested in this course...',
          key: 'background'
        },
        {
          type: 'question',
          question: `How familiar are you with ${courseData.domain || 'this subject'}?`,
          options: [
            { value: 'beginner', label: 'Complete beginner - starting from scratch' },
            { value: 'some', label: 'Some basics - studied or worked with it before' },
            { value: 'intermediate', label: 'Solid foundation - comfortable with core concepts' },
            { value: 'advanced', label: 'Advanced - deep understanding and experience' }
          ],
          key: 'experience',
          priorKnowledgeKey: 'level'
        },
        {
          type: 'question',
          question: 'What do you hope to achieve by completing this course?',
          placeholder: 'Your goals, what you want to learn, how you plan to use these skills...',
          key: 'goals',
          priorKnowledgeKey: 'interests'
        }
      ]
    }
  }

  const loadTemplate = (domain) => {
    const template = getDomainTemplate(domain)
    setOnboardingQuestions(template)
    setUseCustom(true)
    setSelectedTemplate(domain)
  }

  const addQuestion = (type) => {
    const newQuestion = type === 'text'
      ? {
          type: 'question',
          question: '',
          placeholder: '',
          key: ''
        }
      : {
          type: 'question',
          question: '',
          options: [
            { value: '', label: '' },
            { value: '', label: '' }
          ],
          key: ''
        }

    setOnboardingQuestions([...onboardingQuestions, newQuestion])
  }

  const updateQuestion = (index, field, value) => {
    const updated = [...onboardingQuestions]
    updated[index] = { ...updated[index], [field]: value }
    setOnboardingQuestions(updated)
  }

  const removeQuestion = (index) => {
    setOnboardingQuestions(onboardingQuestions.filter((_, i) => i !== index))
  }

  const addOption = (questionIndex) => {
    const updated = [...onboardingQuestions]
    const question = { ...updated[questionIndex] }
    question.options = [...(question.options || []), { value: '', label: '' }]
    updated[questionIndex] = question
    setOnboardingQuestions(updated)
  }

  const updateOption = (questionIndex, optionIndex, field, value) => {
    const updated = [...onboardingQuestions]
    const question = { ...updated[questionIndex] }
    const options = [...question.options]
    options[optionIndex] = { ...options[optionIndex], [field]: value }
    question.options = options
    updated[questionIndex] = question
    setOnboardingQuestions(updated)
  }

  const removeOption = (questionIndex, optionIndex) => {
    const updated = [...onboardingQuestions]
    const question = { ...updated[questionIndex] }
    question.options = question.options.filter((_, i) => i !== optionIndex)
    updated[questionIndex] = question
    setOnboardingQuestions(updated)
  }

  const handleNext = () => {
    const data = {
      ...courseData,
      onboarding_questions: useCustom ? onboardingQuestions : null
    }
    onNext(data)
  }

  return (
    <div className="wizard-step onboarding-question-builder">
      <div className="step-header">
        <h2>Onboarding Questions (Optional)</h2>
        <p className="step-description">
          Custom onboarding questions help you gather learner background, experience, and goals.
          The AI tutor uses this information to personalize examples, adjust pacing, and make
          connections to learners' interests.
        </p>
      </div>

      <div className="value-proposition">
        <div className="value-card">
          <span className="value-icon">🎯</span>
          <h4>Personalized Examples</h4>
          <p>If a learner mentions "running a coffee shop," examples use coffee shop scenarios instead of generic "Widget A"</p>
        </div>
        <div className="value-card">
          <span className="value-icon">🔗</span>
          <h4>Build on Prior Knowledge</h4>
          <p>Connect new concepts to what learners already know (e.g., "Like in Python, Excel functions take arguments...")</p>
        </div>
        <div className="value-card">
          <span className="value-icon">📊</span>
          <h4>Adaptive Pacing</h4>
          <p>Adjust difficulty and depth based on experience level</p>
        </div>
      </div>

      <div className="onboarding-choice">
        <label className="choice-option">
          <input
            type="radio"
            name="onboarding-type"
            checked={!useCustom}
            onChange={() => setUseCustom(false)}
          />
          <div className="choice-content">
            <h3>Use Default Questions</h3>
            <p>Generic questions that work for any course (background, experience level, goals)</p>
          </div>
        </label>

        <label className="choice-option">
          <input
            type="radio"
            name="onboarding-type"
            checked={useCustom}
            onChange={() => setUseCustom(true)}
          />
          <div className="choice-content">
            <h3>Custom Questions</h3>
            <p>Create domain-specific questions or use a template</p>
          </div>
        </label>
      </div>

      {useCustom && (
        <>
          <div className="template-selector">
            <h3>Start with a Template</h3>
            <div className="template-buttons">
              <button
                onClick={() => loadTemplate(courseData.domain)}
                className={`template-button ${selectedTemplate === courseData.domain ? 'active' : ''}`}
              >
                {courseData.domain || 'General'} Template
              </button>
              <button
                onClick={() => loadTemplate('generic')}
                className={`template-button ${selectedTemplate === 'generic' ? 'active' : ''}`}
              >
                Generic Template
              </button>
              <button
                onClick={() => {
                  setOnboardingQuestions([])
                  setSelectedTemplate('custom')
                }}
                className={`template-button ${selectedTemplate === 'custom' ? 'active' : ''}`}
              >
                Start from Scratch
              </button>
            </div>
          </div>

          <div className="questions-list">
            <h3>Onboarding Questions</h3>
            <p className="help-text">
              💡 <strong>Tip:</strong> Always include a question about learner goals/interests.
              This helps the AI create relevant, engaging examples.
            </p>

            {onboardingQuestions.map((question, index) => (
              <div key={index} className="question-card">
                <div className="question-header">
                  <span className="question-number">Question {index + 1}</span>
                  <button
                    onClick={() => removeQuestion(index)}
                    className="remove-question-btn"
                  >
                    Remove
                  </button>
                </div>

                <div className="form-group">
                  <label>Question Text *</label>
                  <input
                    type="text"
                    value={question.question}
                    onChange={(e) => updateQuestion(index, 'question', e.target.value)}
                    placeholder="What question will you ask the learner?"
                  />
                </div>

                <div className="form-group">
                  <label>Storage Key *</label>
                  <input
                    type="text"
                    value={question.key}
                    onChange={(e) => updateQuestion(index, 'key', e.target.value)}
                    placeholder="e.g., background, goals, experience (no spaces)"
                  />
                  <small>Internal name for storing this answer</small>
                </div>

                {question.options ? (
                  // Multiple choice question
                  <div className="options-section">
                    <label>Answer Options</label>
                    {question.options.map((option, optIndex) => (
                      <div key={optIndex} className="option-row">
                        <input
                          type="text"
                          value={option.value}
                          onChange={(e) => updateOption(index, optIndex, 'value', e.target.value)}
                          placeholder="Value (e.g., beginner)"
                        />
                        <input
                          type="text"
                          value={option.label}
                          onChange={(e) => updateOption(index, optIndex, 'label', e.target.value)}
                          placeholder="Label (e.g., Complete beginner - starting from scratch)"
                        />
                        <button
                          onClick={() => removeOption(index, optIndex)}
                          className="remove-option-btn"
                        >
                          ×
                        </button>
                      </div>
                    ))}
                    <button
                      onClick={() => addOption(index)}
                      className="add-option-btn"
                    >
                      + Add Option
                    </button>
                  </div>
                ) : (
                  // Text input question
                  <div className="form-group">
                    <label>Placeholder Text</label>
                    <input
                      type="text"
                      value={question.placeholder || ''}
                      onChange={(e) => updateQuestion(index, 'placeholder', e.target.value)}
                      placeholder="Hint text to guide learners..."
                    />
                  </div>
                )}

                <div className="form-group">
                  <label>Prior Knowledge Key (optional)</label>
                  <input
                    type="text"
                    value={question.priorKnowledgeKey || ''}
                    onChange={(e) => updateQuestion(index, 'priorKnowledgeKey', e.target.value)}
                    placeholder="e.g., level, interests, relatedSkills"
                  />
                  <small>Save to learner's priorKnowledge profile (useful for AI personalization)</small>
                </div>
              </div>
            ))}

            <div className="add-question-buttons">
              <button
                onClick={() => addQuestion('text')}
                className="add-question-btn"
              >
                + Add Text Question
              </button>
              <button
                onClick={() => addQuestion('multiple')}
                className="add-question-btn"
              >
                + Add Multiple Choice
              </button>
            </div>
          </div>
        </>
      )}

      <div className="wizard-actions">
        <button onClick={onBack} className="wizard-button secondary">
          ← Back
        </button>
        <div className="right-actions">
          <button onClick={() => onSaveDraft(courseData)} className="wizard-button secondary">
            Save Draft
          </button>
          <button onClick={handleNext} className="wizard-button primary">
            Continue →
          </button>
        </div>
      </div>
    </div>
  )
}

export default OnboardingQuestionBuilder
