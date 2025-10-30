import { useState, useEffect } from 'react'
import ContentRenderer from './components/ContentRenderer'
import ProgressDashboard from './components/ProgressDashboard'
import OnboardingFlow from './components/OnboardingFlow'
import ConfidenceSlider from './components/ConfidenceSlider'
import FloatingTutorButton from './components/FloatingTutorButton'
import MasteryProgressBar from './components/MasteryProgressBar'
import ConceptMasteryModal from './components/ConceptMasteryModal'
import CourseCreationWizard from './components/course-creation/CourseCreationWizard'
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

  // Mastery celebration state
  const [showMasteryModal, setShowMasteryModal] = useState(false)
  const [completedConceptId, setCompletedConceptId] = useState(null)

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

  // Course creation state
  const [showCourseCreation, setShowCourseCreation] = useState(false)

  // Generate or retrieve learner ID
  useEffect(() => {
    const storedLearnerId = localStorage.getItem('learnerId')
    const storedProfile = localStorage.getItem('learnerProfile')

    console.log('🔍 Initial load check:', {
      hasLearnerId: !!storedLearnerId,
      hasProfile: !!storedProfile,
      learnerId: storedLearnerId
    })

    if (storedLearnerId && storedProfile) {
      // Both ID and profile exist - skip onboarding
      console.log('✅ Restoring existing session')
      setLearnerId(storedLearnerId)
      setLearnerProfile(JSON.parse(storedProfile))
      setIsStarted(true)
      setOnboardingComplete(true)
      loadProgress(storedLearnerId)
    } else if (storedLearnerId && !storedProfile) {
      // ID exists but no profile - clear stale data and start fresh
      console.log('🧹 Clearing stale learnerId without profile')
      localStorage.removeItem('learnerId')
    } else {
      console.log('👋 New user - showing welcome screen')
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
      console.log('📦 Using pre-loaded adaptive content:', currentContent._next_content.type)
      setCurrentContent(currentContent._next_content)
      setContentIndex(i => i + 1)
      return
    }

    // Otherwise, fetch new content from API
    console.log('🔄 Fetching new content from API')
    setIsLoadingContent(true)
    try {
      // Always use 'practice' stage to generate multiple-choice questions
      // (dialogue questions disabled - 'assess' stage not used)
      const stage = 'practice'

      const result = await api.generateContent(learnerId, stage)
      if (result.success) {
        console.log('✅ Got new content:', result.content.type)
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

  const handleMasteryContinue = () => {
    // Dismiss the modal and reload progress to get next concept
    setShowMasteryModal(false)
    setCompletedConceptId(null)

    // Reload progress from backend to get the new concept
    if (learnerId) {
      api.getProgress(learnerId).then((progressData) => {
        if (progressData.success) {
          setProgress(progressData.progress)
          // Generate first content for the new concept
          handleNext()
        }
      })
    }
  }

  const handleResponse = async (response) => {
    console.log('📝 User answered question:', response)

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
      console.log('🤔 Showing confidence slider')
      // Store the answer and question data, then show confidence slider
      setCurrentAnswer(userAnswer)
      setCurrentQuestionData({
        type: response.type || 'multiple-choice',
        content: currentContent,
        correctAnswer: correctAnswer
      })
      setWaitingForConfidence(true)
    } else {
      console.log('⏭️ Skipping confidence, submitting directly')
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
          console.log('✅ Got response, setting content:', contentWithDebug.type)
          setCurrentContent(contentWithDebug)
          setContentIndex(i => i + 1)

          // Update mastery progress
          if (masteryData) {
            setMasteryScore(masteryData.masteryScore || 0)
            setMasteryThreshold(masteryData.masteryThreshold || 0.85)
            setAssessmentsCount(masteryData.assessmentsCount || 0)

            // Check if concept was just completed
            if (masteryData.conceptCompleted) {
              console.log('🎉 Concept completed! Showing celebration modal')
              setCompletedConceptId(progress?.current_concept || 'concept-001')
              setShowMasteryModal(true)
            }
          }
        }
      })
    }
  }

  const handleConfidenceSelect = async (confidenceLevel) => {
    console.log('🎯 Confidence selected:', confidenceLevel)
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
        console.log('✅ Got response with confidence, setting content:', contentWithDebug.type)
        console.log('📦 Next content attached:', !!contentWithDebug._next_content)
        setCurrentContent(contentWithDebug)
        setContentIndex(i => i + 1)

        // Update mastery progress
        if (masteryData) {
          setMasteryScore(masteryData.masteryScore || 0)
          setMasteryThreshold(masteryData.masteryThreshold || 0.85)
          setAssessmentsCount(masteryData.assessmentsCount || 0)

          // Check if concept was just completed
          if (masteryData.conceptCompleted) {
            console.log('🎉 Concept completed! Showing celebration modal')
            setCompletedConceptId(progress?.current_concept || 'concept-001')
            setShowMasteryModal(true)
          }
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

  // Show course creation wizard
  if (showCourseCreation) {
    return (
      <div className="app">
        <CourseCreationWizard
          onComplete={async (courseData) => {
            try {
              console.log('Creating course with data:', courseData)

              // Create the course with all metadata and concepts
              const result = await api.createCourse(courseData)
              console.log('Course created:', result)

              // If there are sources, add them to the course
              if (courseData.sources && courseData.sources.length > 0) {
                console.log(`Adding ${courseData.sources.length} sources...`)

                for (const source of courseData.sources) {
                  try {
                    // Determine if this is a course-level or concept-level source
                    if (source.scope === 'course') {
                      await api.addCourseSource(result.course_id, source)
                      console.log(`Added course-level source: ${source.title}`)
                    } else {
                      // Extract concept index from scope (e.g., "concept-0" -> 0)
                      const conceptIndex = parseInt(source.scope.replace('concept-', ''))
                      const conceptId = `concept-${String(conceptIndex + 1).padStart(3, '0')}`
                      await api.addConceptSource(result.course_id, conceptId, source)
                      console.log(`Added source to ${conceptId}: ${source.title}`)
                    }
                  } catch (sourceError) {
                    console.error('Error adding source:', sourceError)
                    // Continue adding other sources even if one fails
                  }
                }
              }

              alert(`Course "${courseData.title}" created successfully!`)
              setShowCourseCreation(false)
            } catch (error) {
              console.error('Error creating course:', error)
              alert(`Failed to create course: ${error.message}`)
            }
          }}
          onCancel={() => setShowCourseCreation(false)}
        />
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
          <div className="header-buttons">
            <button onClick={() => setShowCourseCreation(true)} className="create-course-button">
              + Create Course
            </button>
            <button onClick={handleReset} className="reset-button">
              Reset Progress
            </button>
          </div>
        </div>
        {/* Development Status Banner */}
        <div className="development-banner">
          <span className="banner-icon">🚧</span>
          <span className="banner-text">
            <strong>Early Access:</strong> Concepts 001-002 available. Additional concepts in development.
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
              {/* Always show mastery progress bar */}
              <MasteryProgressBar
                masteryScore={masteryScore}
                masteryThreshold={masteryThreshold}
                conceptName={currentConceptName}
                assessmentsCount={assessmentsCount}
              />

              <ContentRenderer
                content={isLoading ? null : currentContent}
                onResponse={handleResponse}
                onNext={handleNext}
                isLoading={isLoading}
                learnerId={learnerId}
                learnerProfile={learnerProfile}
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

      {/* Mastery celebration modal */}
      {showMasteryModal && (
        <ConceptMasteryModal
          conceptId={completedConceptId}
          masteryScore={masteryScore}
          onContinue={handleMasteryContinue}
        />
      )}
    </div>
  )
}

export default App
