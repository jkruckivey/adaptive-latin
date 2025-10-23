import { useState, useEffect } from 'react'
import ContentRenderer from './components/ContentRenderer'
import ProgressDashboard from './components/ProgressDashboard'
import OnboardingFlow from './components/OnboardingFlow'
import ConfidenceSlider from './components/ConfidenceSlider'
import FloatingTutorButton from './components/FloatingTutorButton'
import { api } from './api'
import './App.css'

function App() {
  const [learnerId, setLearnerId] = useState(null)
  const [learnerName, setLearnerName] = useState('')
  const [isStarted, setIsStarted] = useState(false)
  const [onboardingComplete, setOnboardingComplete] = useState(false)
  const [learnerProfile, setLearnerProfile] = useState(null)
  const [currentContent, setCurrentContent] = useState(null)
  const [contentIndex, setContentIndex] = useState(0)
  const [isLoading, setIsLoading] = useState(false)
  const [progress, setProgress] = useState(null)
  const [error, setError] = useState(null)

  // Confidence flow state
  const [waitingForConfidence, setWaitingForConfidence] = useState(false)
  const [currentAnswer, setCurrentAnswer] = useState(null)
  const [currentQuestionData, setCurrentQuestionData] = useState(null)

  // Preview mode state
  const [showPreviewChoice, setShowPreviewChoice] = useState(false)
  const [previewShown, setPreviewShown] = useState(false)

  // Generate or retrieve learner ID
  useEffect(() => {
    const storedLearnerId = localStorage.getItem('learnerId')
    if (storedLearnerId) {
      setLearnerId(storedLearnerId)
      setIsStarted(true)
      setOnboardingComplete(true)
      loadProgress(storedLearnerId)
    }
  }, [])

  // Load initial content when learner ID is set
  useEffect(() => {
    if (learnerId && onboardingComplete && !currentContent) {
      loadInitialContent()
    }
  }, [learnerId, onboardingComplete])

  const loadProgress = async (id) => {
    try {
      const data = await api.getProgress(id)
      if (data.success) {
        setProgress(data)
      }
    } catch (err) {
      console.error('Failed to load progress:', err)
    }
  }

  const loadInitialContent = async () => {
    if (!learnerId) return

    // Show preview choice for first question only
    if (!previewShown && progress?.overall_progress?.total_assessments === 0) {
      setShowPreviewChoice(true)
      return
    }

    setIsLoading(true)
    try {
      const result = await api.generateContent(learnerId, 'start')
      if (result.success) {
        setCurrentContent(result.content)
      } else {
        setError('Failed to load content. Please try again.')
        console.error('Content generation error:', result.error)
      }
    } catch (err) {
      setError('Connection error. Please try again.')
      console.error('Failed to load content:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleStart = async (e) => {
    e.preventDefault()
    if (!learnerName.trim()) {
      setError('Please enter your name')
      return
    }

    // Start onboarding
    setIsStarted(true)
    setError(null)
  }

  const handleOnboardingComplete = async (profile) => {
    try {
      const id = `learner-${Date.now()}`
      const response = await api.startLearner(id, learnerName, profile)

      if (response.success) {
        setLearnerId(id)
        setLearnerProfile(profile)
        setOnboardingComplete(true)
        localStorage.setItem('learnerId', id)
        localStorage.setItem('learnerProfile', JSON.stringify(profile))
        // Content will be loaded by the useEffect hook watching learnerId and onboardingComplete
      } else {
        setError(response.message || 'Failed to start learning session')
      }
    } catch (err) {
      setError('Connection error. Please try again.')
      console.error('Start error:', err)
    }
  }

  const handleShowPreview = async () => {
    setShowPreviewChoice(false)
    setIsLoading(true)
    try {
      const result = await api.generateContent(learnerId, 'preview')
      if (result.success) {
        setCurrentContent(result.content)
        setPreviewShown(true)
      } else {
        setError('Failed to load preview. Please try again.')
        console.error('Preview generation error:', result.error)
      }
    } catch (err) {
      setError('Connection error. Please try again.')
      console.error('Failed to load preview:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSkipPreview = async () => {
    setShowPreviewChoice(false)
    setPreviewShown(true)
    setIsLoading(true)
    try {
      const result = await api.generateContent(learnerId, 'start')
      if (result.success) {
        setCurrentContent(result.content)
      } else {
        setError('Failed to load content. Please try again.')
        console.error('Content generation error:', result.error)
      }
    } catch (err) {
      setError('Connection error. Please try again.')
      console.error('Failed to load content:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleNext = async () => {
    setIsLoading(true)
    try {
      // Determine stage based on content progression
      // For now, alternate between practice and assess
      const stage = contentIndex % 2 === 0 ? 'practice' : 'assess'

      const result = await api.generateContent(learnerId, stage)
      if (result.success) {
        setCurrentContent(result.content)
        setContentIndex(contentIndex + 1)
      } else {
        setError('Failed to generate next content. Please try again.')
        console.error('Content generation error:', result.error)
      }
    } catch (err) {
      setError('Connection error. Please try again.')
      console.error('Failed to generate content:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleResponse = async (response) => {
    // Check if we should show confidence rating for this question
    const shouldShowConfidence = currentContent?.show_confidence !== false

    if (shouldShowConfidence) {
      // Store the answer and question data, then show confidence slider
      setCurrentAnswer(response.answer)
      setCurrentQuestionData({
        type: response.type || 'multiple-choice',
        content: currentContent
      })
      setWaitingForConfidence(true)
    } else {
      // Skip confidence slider - submit directly with null confidence
      setIsLoading(true)
      try {
        const result = await api.submitResponse(
          learnerId,
          response.type || 'multiple-choice',
          response.answer,
          currentContent.correctAnswer || 0,
          null,  // No confidence rating
          progress?.current_concept || 'concept-001',
          currentContent.question,
          currentContent.scenario
        )

        if (result.next_content) {
          setCurrentContent(result.next_content)
          setContentIndex(contentIndex + 1)
        } else {
          setError('Failed to get next content')
        }
      } catch (err) {
        setError('Connection error. Please try again.')
        console.error('Failed to submit response:', err)
      } finally {
        setIsLoading(false)
      }
    }
  }

  const handleConfidenceSelect = async (confidenceLevel) => {
    setIsLoading(true)
    setWaitingForConfidence(false)

    try {
      // Call backend to evaluate with confidence
      const result = await api.submitResponse(
        learnerId,
        currentQuestionData.type,
        currentAnswer,
        currentQuestionData.content.correctAnswer || 0, // Use correct answer from content
        confidenceLevel,
        'noun-declensions', // TODO: Get from learner state
        currentQuestionData.content.question, // Pass question text
        currentQuestionData.content.scenario // Pass scenario text
      )

      // Show the next content returned by the backend
      if (result.next_content) {
        setCurrentContent(result.next_content)
        setContentIndex(contentIndex + 1)
      } else {
        setError('Failed to get next content')
      }
    } catch (err) {
      setError('Connection error. Please try again.')
      console.error('Failed to submit response:', err)
    } finally {
      setIsLoading(false)
      setCurrentAnswer(null)
      setCurrentQuestionData(null)
    }
  }

  const handleReset = () => {
    if (confirm('Are you sure you want to reset your progress?')) {
      localStorage.removeItem('learnerId')
      localStorage.removeItem('learnerProfile')
      setLearnerId(null)
      setIsStarted(false)
      setOnboardingComplete(false)
      setLearnerName('')
      setLearnerProfile(null)
      setProgress(null)
      setContentIndex(0)
      setCurrentContent(null)
      setError(null)
    }
  }

  if (!isStarted) {
    return (
      <div className="app">
        <div className="welcome-container">
          <h1>🏛️ Adaptive Latin Learning</h1>
          <p className="welcome-subtitle">AI-powered personalized Latin grammar instruction</p>

          <form onSubmit={handleStart} className="start-form">
            <div className="form-group">
              <label htmlFor="name">What's your name?</label>
              <input
                id="name"
                type="text"
                value={learnerName}
                onChange={(e) => setLearnerName(e.target.value)}
                placeholder="Enter your name"
                className="name-input"
                autoFocus
              />
            </div>

            {error && <div className="error-message">{error}</div>}

            <button type="submit" className="start-button">
              Begin Learning
            </button>
          </form>

          <div className="features">
            <div className="feature">
              <span className="feature-icon">📚</span>
              <div>
                <h3>Rich Content</h3>
                <p>Lessons, tables, examples, and interactive exercises</p>
              </div>
            </div>
            <div className="feature">
              <span className="feature-icon">🎯</span>
              <div>
                <h3>Adaptive Learning</h3>
                <p>AI serves exactly what you need, when you need it</p>
              </div>
            </div>
            <div className="feature">
              <span className="feature-icon">⚡</span>
              <div>
                <h3>Varied Formats</h3>
                <p>Multiple choice, fill-in-blank, open response, and more</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Show onboarding flow
  if (isStarted && !onboardingComplete) {
    return (
      <div className="app">
        <OnboardingFlow
          learnerName={learnerName}
          onComplete={handleOnboardingComplete}
        />
      </div>
    )
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <h1>🏛️ Adaptive Latin</h1>
          <button onClick={handleReset} className="reset-button">
            Reset Progress
          </button>
        </div>
        {/* Development Status Banner */}
        <div className="development-banner">
          <span className="banner-icon">🚧</span>
          <span className="banner-text">
            <strong>Early Access:</strong> Currently featuring Concept 001 (First Declension). Additional concepts in development.
          </span>
          <span className="banner-status">1/7 Complete</span>
        </div>
      </header>

      <div className="main-content">
        <div className="chat-column">
          {showPreviewChoice ? (
            <div className="preview-choice-container">
              <h2>Ready to start your first question?</h2>
              <p className="preview-description">
                This is your first diagnostic question. Would you like a quick preview of the concept first,
                or jump right into the assessment?
              </p>
              <div className="preview-buttons">
                <button onClick={handleShowPreview} className="preview-button show-preview">
                  <span className="button-icon">📖</span>
                  <span className="button-text">
                    <strong>Show me a preview first</strong>
                    <small>Quick 30-second introduction</small>
                  </span>
                </button>
                <button onClick={handleSkipPreview} className="preview-button skip-preview">
                  <span className="button-icon">🎯</span>
                  <span className="button-text">
                    <strong>Jump right in</strong>
                    <small>Start with the diagnostic</small>
                  </span>
                </button>
              </div>
            </div>
          ) : waitingForConfidence ? (
            <ConfidenceSlider onConfidenceSelect={handleConfidenceSelect} />
          ) : (
            <ContentRenderer
              content={isLoading ? null : currentContent}
              onResponse={handleResponse}
              onNext={handleNext}
              isLoading={isLoading}
              learnerId={learnerId}
              conceptId={progress?.current_concept || 'concept-001'}
            />
          )}
        </div>
        <div className="progress-column">
          <ProgressDashboard
            learnerId={learnerId}
            progress={progress}
          />
        </div>
      </div>

      {/* Floating Tutor Button - always accessible */}
      <FloatingTutorButton
        learnerId={learnerId}
        conceptId={progress?.current_concept || 'concept-001'}
      />
    </div>
  )
}

export default App
