import { useState } from 'react'
import './OnboardingFlow.css'

function OnboardingFlow({ learnerName, onComplete }) {
  const [step, setStep] = useState(0)
  const [profile, setProfile] = useState({
    name: learnerName,
    background: '',
    languages: [],
    grammarExperience: '',
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

  // Discovery questions and interactions
  const steps = [
    {
      type: 'welcome',
      content: (
        <div className="onboarding-step welcome-step">
          <h1>Welcome, {learnerName}! 🎉</h1>
          <p className="lead">Before we dive into Latin, I'd love to learn a bit about you. This helps me tailor everything to your background and interests.</p>
          <p className="subtext">No worries - this isn't a test. Just a friendly conversation so I can be a better tutor for you!</p>
          <button onClick={handleNext} className="continue-button">
            Let's get started →
          </button>
        </div>
      )
    },
    {
      type: 'question',
      question: "Tell me about yourself - what brings you to Latin?",
      placeholder: "I'm studying classics, I love ancient history, working on SAT vocab, just curious...",
      onAnswer: (answer) => {
        updateProfile('background', answer)
        handleNext()
      }
    },
    {
      type: 'question',
      question: "Have you studied any other languages before? (Even just a little bit in school counts!)",
      placeholder: "Spanish, French, German, nothing yet...",
      onAnswer: (answer) => {
        const languages = answer.toLowerCase()
        updateProfile('languages', languages)
        // Extract useful info
        const hasSpanish = languages.includes('spanish')
        const hasFrench = languages.includes('french')
        const hasGerman = languages.includes('german')
        updateProfile('priorKnowledge', {
          ...profile.priorKnowledge,
          hasRomanceLanguage: hasSpanish || hasFrench,
          hasInflectedLanguage: hasGerman,
          languageDetails: answer
        })
        handleNext()
      }
    },
    {
      type: 'question',
      question: "When you learned grammar in English class, how did it feel?",
      options: [
        { value: 'loved', label: '✨ Loved it! Parts of speech, diagrams, all of it', emoji: '🤓' },
        { value: 'okay', label: '📚 It was okay, I remember the basics', emoji: '👍' },
        { value: 'confused', label: '😵 Honestly? Pretty confusing', emoji: '🤷' },
        { value: 'forgotten', label: '🤔 That was a long time ago...', emoji: '⏰' }
      ],
      onSelect: (value) => {
        updateProfile('grammarExperience', value)
        handleNext()
      }
    },
    {
      type: 'interactive',
      prompt: "Let's try something fun. No pressure - just see what you think.",
      content: (
        <div className="interactive-assessment">
          <h3>Look at these English sentences:</h3>
          <div className="sentence-examples">
            <div className="sentence">
              <span className="highlighted">The girl</span> sees the road.
            </div>
            <div className="sentence">
              I see <span className="highlighted">the girl</span>.
            </div>
          </div>

          <p className="question-text">
            Notice how "the girl" appears in both sentences? What's different about its role?
          </p>

          <div className="option-buttons">
            <button onClick={() => {
              updateProfile('priorKnowledge', {
                ...profile.priorKnowledge,
                understandsSubjectObject: true,
                subjectObjectConfidence: 'high'
              })
              handleNext()
            }} className="assessment-option">
              <div className="option-content">
                <div className="option-icon">💡</div>
                <div className="option-text">
                  <div className="option-title">First one is the subject (doing the seeing)</div>
                  <div className="option-subtitle">Second one is the object (being seen)</div>
                </div>
              </div>
            </button>

            <button onClick={() => {
              updateProfile('priorKnowledge', {
                ...profile.priorKnowledge,
                understandsSubjectObject: 'partial',
                subjectObjectConfidence: 'medium'
              })
              handleNext()
            }} className="assessment-option">
              <div className="option-content">
                <div className="option-icon">🤔</div>
                <div className="option-text">
                  <div className="option-title">They feel different but I'm not sure why</div>
                  <div className="option-subtitle">Something about position maybe?</div>
                </div>
              </div>
            </button>

            <button onClick={() => {
              updateProfile('priorKnowledge', {
                ...profile.priorKnowledge,
                understandsSubjectObject: false,
                subjectObjectConfidence: 'low'
              })
              handleNext()
            }} className="assessment-option">
              <div className="option-content">
                <div className="option-icon">😊</div>
                <div className="option-text">
                  <div className="option-title">Not really sure - they look the same to me!</div>
                  <div className="option-subtitle">No worries, we'll explore this together</div>
                </div>
              </div>
            </button>
          </div>

          <p className="encouragement">
            💙 There's no wrong answer here - this just helps me know where to start!
          </p>
        </div>
      )
    },
    {
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
                <div className="option-icon">🔄</div>
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
    },
    {
      type: 'question',
      question: "Last one! What topics interest you? (This helps me choose examples you'll actually care about)",
      placeholder: "Roman history, mythology, philosophy, medicine, law, sports, anything...",
      onAnswer: (answer) => {
        updateProfile('interests', answer)
        handleNext()
      }
    },
    {
      type: 'summary',
      content: (
        <div className="onboarding-step summary-step">
          <h2>Perfect! Here's what I learned about you:</h2>

          <div className="profile-summary">
            <div className="summary-item">
              <div className="summary-icon">👤</div>
              <div className="summary-content">
                <div className="summary-label">Background</div>
                <div className="summary-value">{profile.background || 'Curious learner'}</div>
              </div>
            </div>

            {profile.languages && (
              <div className="summary-item">
                <div className="summary-icon">🌍</div>
                <div className="summary-content">
                  <div className="summary-label">Language Experience</div>
                  <div className="summary-value">{profile.priorKnowledge.languageDetails || 'Starting fresh'}</div>
                </div>
              </div>
            )}

            <div className="summary-item">
              <div className="summary-icon">📚</div>
              <div className="summary-content">
                <div className="summary-label">Grammar Comfort</div>
                <div className="summary-value">
                  {profile.grammarExperience === 'loved' && 'Grammar enthusiast!'}
                  {profile.grammarExperience === 'okay' && 'Solid foundation'}
                  {profile.grammarExperience === 'confused' && "We'll take it step by step"}
                  {profile.grammarExperience === 'forgotten' && "We'll refresh together"}
                </div>
              </div>
            </div>

            <div className="summary-item">
              <div className="summary-icon">🎯</div>
              <div className="summary-content">
                <div className="summary-label">Learning Preferences</div>
                <div className="summary-value">
                  {profile.learningStyle === 'narrative' && 'Story-based learning'}
                  {profile.learningStyle === 'varied' && 'Varied question types'}
                  {profile.learningStyle === 'adaptive' && 'Adaptive progression'}
                </div>
              </div>
            </div>

            {profile.interests && (
              <div className="summary-item">
                <div className="summary-icon">⭐</div>
                <div className="summary-content">
                  <div className="summary-label">Interests</div>
                  <div className="summary-value">{profile.interests}</div>
                </div>
              </div>
            )}
          </div>

          <div className="personalization-promise">
            <h3>How I'll use this:</h3>
            <ul>
              {profile.priorKnowledge.hasRomanceLanguage && (
                <li>✓ I'll connect Latin to the Spanish/French you know</li>
              )}
              {profile.learningStyle === 'narrative' && (
                <li>✓ I'll use story-based examples and contextual explanations</li>
              )}
              {profile.learningStyle === 'varied' && (
                <li>✓ I'll mix different formats - tables, stories, and exercises</li>
              )}
              {profile.learningStyle === 'adaptive' && (
                <li>✓ I'll adjust difficulty based on your performance patterns</li>
              )}
              {profile.interests && profile.interests.trim() && (
                <li>✓ Examples will feature {profile.interests.split(',')[0].trim()}</li>
              )}
              <li>✓ I'll adapt as we go based on what works for you</li>
            </ul>
          </div>

          <button onClick={handleComplete} className="continue-button big" disabled={isStarting}>
            {isStarting ? 'Starting your journey...' : 'Start Learning! 🚀'}
          </button>
        </div>
      )
    }
  ]

  const currentStep = steps[step]

  if (currentStep.type === 'question') {
    if (currentStep.options) {
      // Multiple choice question
      return (
        <div className="onboarding-container">
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${(step / steps.length) * 100}%` }} />
          </div>

          <div className="onboarding-step question-step">
            <h2>{currentStep.question}</h2>
            <div className="option-buttons">
              {currentStep.options.map((option, index) => (
                <button
                  key={index}
                  onClick={() => currentStep.onSelect(option.value)}
                  className="assessment-option"
                >
                  <div className="option-content">
                    <div className="option-emoji">{option.emoji}</div>
                    <div className="option-label">{option.label}</div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      )
    } else {
      // Open-ended question
      return (
        <div className="onboarding-container">
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${(step / steps.length) * 100}%` }} />
          </div>

          <div className="onboarding-step question-step">
            <h2>{currentStep.question}</h2>
            <textarea
              value={currentAnswer}
              onChange={(e) => setCurrentAnswer(e.target.value)}
              placeholder={currentStep.placeholder}
              className="answer-input"
              rows={3}
              autoFocus
            />
            <button
              onClick={() => currentStep.onAnswer(currentAnswer)}
              disabled={!currentAnswer.trim()}
              className="continue-button"
            >
              Continue →
            </button>
          </div>
        </div>
      )
    }
  }

  if (currentStep.type === 'interactive') {
    return (
      <div className="onboarding-container">
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${(step / steps.length) * 100}%` }} />
        </div>

        <div className="onboarding-step interactive-step">
          <p className="step-prompt">{currentStep.prompt}</p>
          {currentStep.content}
        </div>
      </div>
    )
  }

  // Welcome or Summary step
  return (
    <div className="onboarding-container">
      {step > 0 && step < steps.length - 1 && (
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${(step / steps.length) * 100}%` }} />
        </div>
      )}
      {currentStep.content}
    </div>
  )
}

export default OnboardingFlow
