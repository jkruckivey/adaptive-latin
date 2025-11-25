import { useState, useMemo } from 'react'
import './OnboardingFlow.css'

function OnboardingFlow({ learnerName, onComplete, courseTitle = 'this course', courseDomain = '', customQuestions = null }) {
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
  const [selectedOption, setSelectedOption] = useState('')

  const updateProfile = (key, value) => {
    setProfile(prev => {
      if (key === 'priorKnowledge' && typeof value === 'object') {
        // Merge with existing priorKnowledge to avoid stale closure issues
        return { ...prev, priorKnowledge: { ...prev.priorKnowledge, ...value } }
      }
      return { ...prev, [key]: value }
    })
  }

  const handleNext = () => {
    console.log('[Onboarding] handleNext called')
    setStep(prev => {
      console.log('[Onboarding] Incrementing step from', prev, 'to', prev + 1)
      return prev + 1
    })
    setCurrentAnswer('')
    setSelectedOption('')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleComplete = () => {
    setIsStarting(true)
    // Use callback to get latest profile state (avoids stale closure issue)
    setProfile(currentProfile => {
      onComplete(currentProfile)
      return currentProfile
    })
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

  // Generate smart placeholder based on domain
  const getRelatedSkillsPlaceholder = (domain) => {
    const domainLower = domain.toLowerCase()

    if (domainLower.includes('excel') || domainLower.includes('spreadsheet') || domainLower.includes('data')) {
      return 'e.g., Programming languages, statistics, databases, other spreadsheet tools...'
    } else if (domainLower.includes('language') || domainLower.includes('latin') || domainLower.includes('spanish')) {
      return 'e.g., Other languages you speak, linguistics background...'
    } else if (domainLower.includes('programming') || domainLower.includes('code') || domainLower.includes('software')) {
      return 'e.g., Other programming languages, mathematics, problem-solving experience...'
    } else if (domainLower.includes('math') || domainLower.includes('statistics')) {
      return 'e.g., Programming, physics, analytical coursework...'
    } else if (domainLower.includes('business') || domainLower.includes('finance')) {
      return 'e.g., Accounting, economics, data analysis, management experience...'
    } else {
      return 'e.g., Related subjects, skills, or experiences you have...'
    }
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

    // Add custom questions if provided, otherwise use generic defaults
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
                updateProfile('priorKnowledge', { [q.priorKnowledgeKey]: value })
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
                updateProfile('priorKnowledge', { [q.priorKnowledgeKey]: answer })
              }
              handleNext()
            }
          })
        }
      })
    } else {
      // Default generic onboarding questions

      // 1. Background & Motivation
      builtSteps.push({
        type: 'question',
        question: `Tell me about yourself - what brings you to ${courseTitle}?`,
        placeholder: 'Tell me about your background and why you\'re interested in this course...',
        onAnswer: (answer) => {
          console.log('[Onboarding] Background answer submitted:', answer)
          console.log('[Onboarding] Current step before update:', step)
          updateProfile('background', answer)
          console.log('[Onboarding] Calling handleNext()')
          handleNext()
        }
      })

      // 2. Prior Knowledge
      builtSteps.push({
        type: 'question',
        question: `How familiar are you with ${courseDomain || 'this subject'}?`,
        options: [
          { value: 'beginner', label: 'Complete beginner - starting from scratch' },
          { value: 'some', label: 'Some basics - studied or worked with it before' },
          { value: 'intermediate', label: 'Solid foundation - comfortable with core concepts' },
          { value: 'advanced', label: 'Advanced - deep understanding and experience' }
        ],
        onSelect: (value) => {
          updateProfile('priorKnowledge', { level: value })
          handleNext()
        }
      })

      // 3. Related Skills & Knowledge
      builtSteps.push({
        type: 'question',
        question: 'What related skills or subjects do you already know? This helps me connect new concepts to things you\'re familiar with.',
        placeholder: getRelatedSkillsPlaceholder(courseDomain),
        onAnswer: (answer) => {
          updateProfile('priorKnowledge', { relatedSkills: answer })
          handleNext()
        }
      })

      // 4. Learning Goals
      builtSteps.push({
        type: 'question',
        question: 'What do you hope to achieve by completing this course?',
        placeholder: 'Your goals, what you want to learn, how you plan to use these skills...',
        onAnswer: (answer) => {
          updateProfile('interests', answer)
          handleNext()
        }
      })
    }

    // Completion step
    builtSteps.push({
      type: 'completion',
      content: (
        <div className="onboarding-step completion-step">
          <h2>Perfect! You're all set.</h2>
          <p className="lead">I'm preparing your personalized learning path now...</p>
          <button onClick={handleComplete} className="start-button" disabled={isStarting}>
            {isStarting ? 'Starting...' : 'Begin Learning'}
          </button>
        </div>
      )
    })

    console.log('[Onboarding] Building steps array, total steps:', builtSteps.length)
    return builtSteps
  }, [learnerName, courseTitle, courseDomain, customQuestions, isStarting, profile.priorKnowledge])

  console.log('[Onboarding] Render - current step index:', step, 'total steps:', steps.length)

  const currentStep = steps[step]

  if (!currentStep) return null

  // Render based on step type
  if (currentStep.type === 'welcome' || currentStep.type === 'completion') {
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
        <>
          <div className="option-buttons">
            {currentStep.options.map((option, index) => (
              <label
                key={index}
                className="assessment-option"
              >
                <input
                  type="radio"
                  name="question-option"
                  value={option.value}
                  checked={selectedOption === option.value}
                  onChange={(e) => setSelectedOption(e.target.value)}
                />
                <div className="option-text">
                  <div className="option-title">{option.label}</div>
                </div>
              </label>
            ))}
          </div>
          <button
            onClick={() => {
              currentStep.onSelect(selectedOption)
            }}
            className="continue-button"
            disabled={!selectedOption}
            style={{ marginTop: '24px' }}
          >
            Continue
          </button>
        </>
      ) : (
        // Text input
        <div className="text-input-container">
          <textarea
            value={currentAnswer}
            onChange={(e) => setCurrentAnswer(e.target.value)}
            placeholder={currentStep.placeholder}
            className="answer-input"
            rows="6"
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
