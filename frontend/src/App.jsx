import { useState, useEffect } from 'react'
import ContentRenderer from './components/ContentRenderer'
import ProgressDashboard from './components/ProgressDashboard'
import OnboardingFlow from './components/OnboardingFlow'
import ConfidenceSlider from './components/ConfidenceSlider'
import FloatingTutorButton from './components/FloatingTutorButton'
import MasteryProgressBar from './components/MasteryProgressBar'
import { useSubmitResponse } from './hooks/useSubmitResponse'
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
  const [progress, setProgress] = useState(null)

  // Mastery progress state
  const [masteryScore, setMasteryScore] = useState(0)
  const [masteryThreshold, setMasteryThreshold] = useState(0.85)
  const [assessmentsCount, setAssessmentsCount] = useState(0)
  const [currentConceptName, setCurrentConceptName] = useState('First Declension')

  // Local loading/error state for content generation
  const [isLoadingContent, setIsLoadingContent] = useState(false)
  const [contentError, setContentError] = useState(null)

  // Use custom hook for submission logic
  const { submitResponse, isLoading: isSubmitting, error: submitError, setError: setSubmitError } = useSubmitResponse()

  // Combined loading and error state for UI
  const isLoading = isLoadingContent || isSubmitting
  const error = contentError || submitError
  const setError = (err) => {
    setContentError(err)
    setSubmitError(err)
  }

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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [learnerId, onboardingComplete, currentContent])

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

    setIsLoadingContent(true)
    try {
      const result = await api.generateContent(learnerId, 'start')
      if (result.success) {
        setCurrentContent(result.content)
      } else {
        setContentError('Failed to load content. Please try again.')
        console.error('Content generation error:', result.error)
      }
    } catch (err) {
      setContentError('Connection error. Please try again.')
      console.error('Failed to load content:', err)
    } finally {
      setIsLoadingContent(false)
    }
  }

  const handleStart = async (e) => {
    e.preventDefault()
    if (!learnerName.trim()) {
      setContentError('Please enter your name')
      return
    }

    // Start onboarding
    setIsStarted(true)
    setContentError(null)
  }

  const handleOnboardingComplete = async (profile) => {
    setIsLoadingContent(true) // Show loading indicator during scenario generation
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
        setContentError(response.message || 'Failed to start learning session')
        setIsLoadingContent(false)
      }
    } catch (err) {
      setContentError('Connection error. Please try again.')
      setIsLoadingContent(false)
      console.error('Start error:', err)
    }
  }

  const handleShowPreview = async () => {
    setShowPreviewChoice(false)
    setIsLoadingContent(true)
    try {
      const result = await api.generateContent(learnerId, 'preview')
      if (result.success) {
        setCurrentContent(result.content)
        setPreviewShown(true)
      } else {
        setContentError('Failed to load preview. Please try again.')
        console.error('Preview generation error:', result.error)
      }
    } catch (err) {
      setContentError('Connection error. Please try again.')
      console.error('Failed to load preview:', err)
    } finally {
      setIsLoadingContent(false)
    }
  }

  const handleSkipPreview = async () => {
    setShowPreviewChoice(false)
    setPreviewShown(true)
    setIsLoadingContent(true)
    try {
      const result = await api.generateContent(learnerId, 'start')
      if (result.success) {
        setCurrentContent(result.content)
      } else {
        setContentError('Failed to load content. Please try again.')
        console.error('Content generation error:', result.error)
      }
    } catch (err) {
      setContentError('Connection error. Please try again.')
      console.error('Failed to load content:', err)
    } finally {
      setIsLoadingContent(false)
    }
  }

  const handleNext = async () => {
    // Check if current content has pre-loaded next content (from assessment results)
    if (currentContent?._next_content) {
      // Use the adaptive next content that was already prepared based on performance
      setCurrentContent(currentContent._next_content)
      setContentIndex(i => i + 1)
      return
    }

    // Otherwise, fetch new content from API
    setIsLoadingContent(true)
    try {
      // Determine stage based on content progression
      // For now, alternate between practice and assess
      const stage = contentIndex % 2 === 0 ? 'practice' : 'assess'

      const result = await api.generateContent(learnerId, stage)
      if (result.success) {
        setCurrentContent(result.content)
        setContentIndex(i => i + 1)
      } else {
        setContentError('Failed to generate next content. Please try again.')
        console.error('Content generation error:', result.error)
      }
    } catch (err) {
      setContentError('Connection error. Please try again.')
      console.error('Failed to generate content:', err)
    } finally {
      setIsLoadingContent(false)
    }
  }

  const handleResponse = async (response) => {
    // Check if we should show confidence rating for this question
    const shouldShowConfidence = currentContent?.show_confidence !== false

    // Extract answer based on question type
    const userAnswer = response.type === 'fill-blank'
      ? (response.answers?.[0] || '') // Fill-blank sends answers array, take first
      : response.answer // Multiple-choice sends answer as number

    // Extract correct answer based on question type
    const correctAnswer = response.type === 'fill-blank'
      ? (currentContent.correctAnswers || []) // Fill-blank: send all acceptable answers
      : (currentContent.correctAnswer || 0) // Multiple-choice has correctAnswer number

    if (shouldShowConfidence) {
      // Store the answer and question data, then show confidence slider
      setCurrentAnswer(userAnswer)
      setCurrentQuestionData({
        type: response.type || 'multiple-choice',
        content: currentContent,
        correctAnswer: correctAnswer
      })
      setWaitingForConfidence(true)
    } else {
      // Skip confidence slider - submit directly with null confidence
      await submitResponse({
        learnerId,
        questionType: response.type || 'multiple-choice',
        answer: userAnswer,
        correctAnswer: correctAnswer,
        confidence: null, // No confidence rating
        conceptId: progress?.current_concept || 'concept-001',
        questionText: currentContent.question,
        scenario: currentContent.scenario,
        options: currentContent.options || null,
        onSuccess: (contentWithDebug, masteryData) => {
          setCurrentContent(contentWithDebug)
          setContentIndex(i => i + 1)

          // Update mastery progress
          if (masteryData) {
            setMasteryScore(masteryData.masteryScore || 0)
            setMasteryThreshold(masteryData.masteryThreshold || 0.85)
            setAssessmentsCount(masteryData.assessmentsCount || 0)
          }
        }
      })
    }
  }

  const handleConfidenceSelect = async (confidenceLevel) => {
    setWaitingForConfidence(false)

    await submitResponse({
      learnerId,
      questionType: currentQuestionData.type,
      answer: currentAnswer,
      correctAnswer: currentQuestionData.correctAnswer, // Use pre-extracted correct answer
      confidence: confidenceLevel,
      conceptId: progress?.current_concept || 'concept-001',
      questionText: currentQuestionData.content.question,
      scenario: currentQuestionData.content.scenario,
      options: currentQuestionData.content.options || null,
      onSuccess: (contentWithDebug, masteryData) => {
        setCurrentContent(contentWithDebug)
        setContentIndex(i => i + 1)

        // Update mastery progress
        if (masteryData) {
          setMasteryScore(masteryData.masteryScore || 0)
          setMasteryThreshold(masteryData.masteryThreshold || 0.85)
          setAssessmentsCount(masteryData.assessmentsCount || 0)
        }
      }
    })

    // Clear confidence state
    setCurrentAnswer(null)
    setCurrentQuestionData(null)
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
                <p>Adaptive questions, visual diagrams, and interactive widgets</p>
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

  // Show loading screen between onboarding and main content
  if (onboardingComplete && !currentContent && isLoadingContent) {
    return (
      <div className="app">
        <div className="initial-loading-screen">
          <div className="loading-container">
            <div className="spinner large"></div>
            <h2 className="loading-title">Setting up your learning experience</h2>
            <div className="loading-steps">
              <div className="loading-step">
                <span className="step-icon">🏛️</span>
                <span className="step-text">Creating your personalized Roman scenario</span>
              </div>
              <div className="loading-step">
                <span className="step-icon">🎭</span>
                <span className="step-text">Introducing characters tailored to your interests</span>
              </div>
              <div className="loading-step">
                <span className="step-icon">📚</span>
                <span className="step-text">Preparing your first Latin exercise</span>
              </div>
            </div>
            <p className="loading-patience">This may take 10-15 seconds...</p>
          </div>
        </div>
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
          <span className="banner-status">
            {progress?.overall_progress?.concepts_completed || 0}/7 Complete
          </span>
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
            <>
              {/* Show mastery progress bar when we have assessment data */}
              {assessmentsCount > 0 && (
                <MasteryProgressBar
                  masteryScore={masteryScore}
                  masteryThreshold={masteryThreshold}
                  conceptName={currentConceptName}
                  assessmentsCount={assessmentsCount}
                />
              )}

              <ContentRenderer
                content={isLoading ? null : currentContent}
                onResponse={handleResponse}
                onNext={handleNext}
                isLoading={isLoading}
                learnerId={learnerId}
                conceptId={progress?.current_concept || 'concept-001'}
              />
            </>
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
