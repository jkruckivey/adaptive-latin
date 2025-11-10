import { useState, useMemo } from 'react'
import './OnboardingFlow.css'

function OnboardingFlow({ learnerName, onComplete, courseTitle = 'this course', customQuestions = null }) {
  const [step, setStep] = useState(0)
  const [profile, setProfile] = useState({
    name: learnerName,
    background: '',
    learningStyle: '',
    interests: '',
    priorKnowledge: {}
  })
  const [currentAnswer, setCurrentAnswer] = useState('')
  const [isStarting, setIsStarting] = useState(false)

  const updateProfile = (key, value) => {
    setProfile(prev => ({ ...prev, [key]: value }))
  }

  const handleNext = () => {
    setStep(step + 1)
    setCurrentAnswer('')
  }

  const handleComplete = () => {
    setIsStarting(true)
    onComplete(profile)
  }

  const handleQuickStart = () => {
    const templateProfile = {
      name: 'Tester',
      background: 'Test user',
      learningStyle: 'varied',
      interests: 'learning new skills'
    }
    setIsStarting(true)
    onComplete(templateProfile)
  }

  // Build steps dynamically from custom questions or use defaults
  const steps = useMemo(() => {
    const builtSteps = []

    // Welcome step (always first)
    builtSteps.push({
      type: 'welcome',
      content: (
        <div className="onboarding-step welcome-step">
          <h1>Welcome, {learnerName}!</h1>
          <p className="lead">Before we dive in, I'd love to learn a bit about you. This helps me tailor everything to your background and interests.</p>
          <p className="subtext">No worries - this isn't a test. Just a friendly conversation so I can be a better tutor for you!</p>
          <button onClick={handleNext} className="continue-button">
            Let's get started
          </button>
          <button onClick={handleQuickStart} className="quick-start-button" disabled={isStarting}>
            {isStarting ? 'Starting...' : 'Quick Start (Testing)'}
          </button>
          <p className="quick-start-hint">Skip onboarding with preset profile for testing</p>
        </div>
      )
    })

    // Add custom questions if provided
    if (customQuestions && customQuestions.length > 0) {
      customQuestions.forEach(q => {
        if (q.options) {
          // Multiple choice question
          builtSteps.push({
            type: 'question',
            question: q.question,
            options: q.options,
            onSelect: (value) => {
              if (q.key) updateProfile(q.key, value)
              if (q.priorKnowledgeKey) {
                updateProfile('priorKnowledge', {
                  ...profile.priorKnowledge,
                  [q.priorKnowledgeKey]: value
                })
              }
              handleNext()
            }
          })
        } else {
          // Text input question
          builtSteps.push({
            type: 'question',
            question: q.question,
            placeholder: q.placeholder,
            onAnswer: (answer) => {
              if (q.key) updateProfile(q.key, answer)
              if (q.priorKnowledgeKey) {
                updateProfile('priorKnowledge', {
                  ...profile.priorKnowledge,
                  [q.priorKnowledgeKey]: answer
                })
              }
              handleNext()
            }
          })
        }
      })
    }

    // Learning style question (always included)
    builtSteps.push({
      type: 'interactive',
      prompt: "One more quick thing...",
      content: (
        <div className="interactive-assessment">
          <h3>When learning something new, what format helps you most?</h3>
          <p className="question-text">
            If you need extra help with a concept, which would you reach for first?
          </p>
          <div className="option-buttons">
            <button onClick={() => {
              updateProfile('learningStyle', 'narrative')
              handleNext()
            }} className="assessment-option">
              <div className="option-content">
                <div className="option-icon">📖</div>
                <div className="option-text">
                  <div className="option-title">Story-based learning</div>
                  <div className="option-subtitle">Learning through scenarios and conversations</div>
                </div>
              </div>
            </button>

            <button onClick={() => {
              updateProfile('learningStyle', 'varied')
              handleNext()
            }} className="assessment-option">
              <div className="option-content">
                <div className="option-icon">🎨</div>
                <div className="option-text">
                  <div className="option-title">Varied content types</div>
                  <div className="option-subtitle">Mix of questions, visual diagrams, and interactive widgets</div>
                </div>
              </div>
            </button>

            <button onClick={() => {
              updateProfile('learningStyle', 'adaptive')
              handleNext()
            }} className="assessment-option">
              <div className="option-content">
                <div className="option-icon">🎯</div>
                <div className="option-text">
                  <div className="option-title">Adaptive progression</div>
                  <div className="option-subtitle">Content adjusts based on your performance</div>
                </div>
              </div>
            </button>
          </div>
        </div>
      )
    })

    // Completion step
    builtSteps.push({
      type: 'completion',
      content: (
        <div className="onboarding-step completion-step">
          <div className="completion-icon">✨</div>
          <h2>Perfect! You're all set.</h2>
          <p className="lead">I'm preparing your personalized learning path now...</p>
          <button onClick={handleComplete} className="start-button" disabled={isStarting}>
            {isStarting ? 'Starting...' : 'Begin Learning'}
          </button>
        </div>
      )
    })

    return builtSteps
  }, [learnerName, customQuestions, isStarting, profile.priorKnowledge])

  const currentStep = steps[step]

  if (!currentStep) return null

  // Render based on step type
  if (currentStep.type === 'welcome' || currentStep.type === 'interactive' || currentStep.type === 'completion') {
    return currentStep.content
  }

  // Render question step
  return (
    <div className="onboarding-step question-step">
      <div className="progress-indicator">
        Step {step + 1} of {steps.length}
      </div>

      <h2>{currentStep.question}</h2>

      {currentStep.options ? (
        // Multiple choice
        <div className="option-buttons">
          {currentStep.options.map((option, index) => (
            <button
              key={index}
              onClick={() => currentStep.onSelect(option.value)}
              className="assessment-option"
            >
              <div className="option-content">
                {option.emoji && <div className="option-icon">{option.emoji}</div>}
                <div className="option-text">
                  <div className="option-title">{option.label}</div>
                </div>
              </div>
            </button>
          ))}
        </div>
      ) : (
        // Text input
        <div className="text-input-container">
          <textarea
            value={currentAnswer}
            onChange={(e) => setCurrentAnswer(e.target.value)}
            placeholder={currentStep.placeholder}
            className="onboarding-input"
            rows="4"
          />
          <button
            onClick={() => {
              if (currentAnswer.trim()) {
                currentStep.onAnswer(currentAnswer)
              }
            }}
            className="continue-button"
            disabled={!currentAnswer.trim()}
          >
            Continue
          </button>
        </div>
      )}
    </div>
  )
}

export default OnboardingFlow
