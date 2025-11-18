import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import ContentRenderer from '../components/ContentRenderer'
import ProgressDashboard from '../components/ProgressDashboard'
import ConfidenceSlider from '../components/ConfidenceSlider'
import FloatingTutorButton from '../components/FloatingTutorButton'
import MasteryProgressBar from '../components/MasteryProgressBar'
import ConceptMasteryModal from '../components/ConceptMasteryModal'
import Syllabus from '../components/Syllabus'
import { useSubmitResponse } from '../hooks/useSubmitResponse'
import { api } from '../api'

export default function LearningPage({ learnerId, selectedCourseId, selectedCourseTitle, onReset }) {
    const navigate = useNavigate()

    // State
    const [currentContent, setCurrentContent] = useState(null)
    const [contentIndex, setContentIndex] = useState(0)
    const [progress, setProgress] = useState(null)
    const [learnerProfile, setLearnerProfile] = useState(null)

    // Mastery progress state
    const [masteryScore, setMasteryScore] = useState(0)
    const [masteryThreshold, setMasteryThreshold] = useState(0.85)
    const [assessmentsCount, setAssessmentsCount] = useState(0)
    const [currentConceptName, setCurrentConceptName] = useState('')

    // Mastery celebration state
    const [showMasteryModal, setShowMasteryModal] = useState(false)
    const [completedConceptId, setCompletedConceptId] = useState(null)

    // Local loading/error state
    const [isLoadingContent, setIsLoadingContent] = useState(false)
    const [contentError, setContentError] = useState(null)

    // Syllabus state
    const [showSyllabus, setShowSyllabus] = useState(false)

    // Use custom hook for submission logic
    const { submitResponse, isLoading: isSubmitting, error: submitError, setError: setSubmitError } = useSubmitResponse()

    // Combined loading and error state
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

    // Load initial data
    useEffect(() => {
        if (learnerId) {
            loadLearnerProfile()
            loadProgress(learnerId)
        }
    }, [learnerId])

    // Load initial content
    useEffect(() => {
        if (learnerId && !currentContent && !isLoadingContent) {
            loadInitialContent()
        }
    }, [learnerId, currentContent])

    const loadLearnerProfile = () => {
        const storedProfile = localStorage.getItem('learnerProfile')
        if (storedProfile) {
            setLearnerProfile(JSON.parse(storedProfile))
        }
    }

    const loadProgress = async (id) => {
        try {
            const data = await api.getProgress(id)
            if (data.success) {
                setProgress(data)
                // Update mastery info if available in progress
                if (data.concept_details && data.current_concept) {
                    const currentData = data.concept_details[data.current_concept]
                    if (currentData) {
                        setMasteryScore(currentData.mastery_score || 0)
                        setAssessmentsCount(currentData.assessments?.length || 0)
                    }
                }
            }
        } catch (err) {
            console.error('Failed to load progress:', err)
        }
    }

    const loadInitialContent = async () => {
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
            }
        } catch (err) {
            setContentError('Connection error. Please try again.')
        } finally {
            setIsLoadingContent(false)
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
            }
        } catch (err) {
            setContentError('Connection error. Please try again.')
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
            }
        } catch (err) {
            setContentError('Connection error. Please try again.')
        } finally {
            setIsLoadingContent(false)
        }
    }

    const handleNext = async () => {
        if (currentContent?._next_content) {
            setCurrentContent(currentContent._next_content)
            setContentIndex(i => i + 1)
            return
        }

        setIsLoadingContent(true)
        try {
            const stage = 'practice'
            const result = await api.generateContent(learnerId, stage)
            if (result.success) {
                setCurrentContent(result.content)
                setContentIndex(i => i + 1)
            } else {
                setContentError('Failed to generate next content. Please try again.')
            }
        } catch (err) {
            setContentError('Connection error. Please try again.')
        } finally {
            setIsLoadingContent(false)
        }
    }

    const handleResponse = async (response) => {
        const shouldShowConfidence = currentContent?.show_confidence !== false

        const userAnswer = response.type === 'fill-blank'
            ? (response.answers?.[0] || '')
            : response.answer

        const correctAnswer = response.type === 'fill-blank'
            ? (currentContent.correctAnswers || [])
            : (currentContent.correctAnswer || 0)

        if (shouldShowConfidence) {
            setCurrentAnswer(userAnswer)
            setCurrentQuestionData({
                type: response.type || 'multiple-choice',
                content: currentContent,
                correctAnswer: correctAnswer
            })
            setWaitingForConfidence(true)
        } else {
            await submitResponse({
                learnerId,
                questionType: response.type || 'multiple-choice',
                answer: userAnswer,
                correctAnswer: correctAnswer,
                confidence: null,
                conceptId: progress?.current_concept || 'concept-001',
                questionText: currentContent.question,
                scenario: currentContent.scenario,
                options: currentContent.options || null,
                onSuccess: handleSubmissionSuccess
            })
        }
    }

    const handleConfidenceSelect = async (confidenceLevel) => {
        setWaitingForConfidence(false)
        await submitResponse({
            learnerId,
            questionType: currentQuestionData.type,
            answer: currentAnswer,
            correctAnswer: currentQuestionData.correctAnswer,
            confidence: confidenceLevel,
            conceptId: progress?.current_concept || 'concept-001',
            questionText: currentQuestionData.content.question,
            scenario: currentQuestionData.content.scenario,
            options: currentQuestionData.content.options || null,
            onSuccess: handleSubmissionSuccess
        })
        setCurrentAnswer(null)
        setCurrentQuestionData(null)
    }

    const handleSubmissionSuccess = (contentWithDebug, masteryData) => {
        setCurrentContent(contentWithDebug)
        setContentIndex(i => i + 1)

        if (masteryData) {
            setMasteryScore(masteryData.masteryScore || 0)
            setMasteryThreshold(masteryData.masteryThreshold || 0.85)
            setAssessmentsCount(masteryData.assessmentsCount || 0)

            if (masteryData.conceptCompleted) {
                setCompletedConceptId(progress?.current_concept || 'concept-001')
                setShowMasteryModal(true)
            }
        }

        // Refresh progress to keep dashboard in sync
        loadProgress(learnerId)
    }

    const handleMasteryContinue = () => {
        setShowMasteryModal(false)
        setCompletedConceptId(null)

        // Reload progress and get next concept content
        loadProgress(learnerId).then(() => {
            handleNext()
        })
    }

    const handleConceptClick = (conceptId) => {
        alert(`Concept navigation clicked: ${conceptId}\n\nThis feature allows reviewing previous concepts or jumping ahead. Full implementation coming soon!`)
    }

    return (
        <div className="app">
            <header className="app-header">
                <div className="header-content">
                    <h1>{selectedCourseTitle || 'Adaptive Learning'}</h1>
                    <div className="header-buttons">
                        <button onClick={() => setShowSyllabus(true)} className="syllabus-button">
                            View Syllabus
                        </button>
                        <button onClick={() => navigate('/admin')} className="admin-button">
                            Admin Dashboard
                        </button>
                        <button onClick={() => navigate('/create-course')} className="create-course-button">
                            + Create Course
                        </button>
                        <button onClick={onReset} className="reset-button">
                            Reset Progress
                        </button>
                    </div>
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
                                    <span className="button-icon"></span>
                                    <span className="button-text">
                                        <strong>Show me a preview first</strong>
                                        <small>Quick 30-second introduction</small>
                                    </span>
                                </button>
                                <button onClick={handleSkipPreview} className="preview-button skip-preview">
                                    <span className="button-icon"></span>
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
                    {error && <div className="error-message">{error}</div>}
                </div>
                <div className="progress-column">
                    <ProgressDashboard
                        learnerId={learnerId}
                        progress={progress}
                        courseTitle={selectedCourseTitle}
                        courseId={selectedCourseId}
                        onConceptClick={handleConceptClick}
                    />
                </div>
            </div>

            <FloatingTutorButton
                learnerId={learnerId}
                conceptId={progress?.current_concept || 'concept-001'}
            />

            {showMasteryModal && (
                <ConceptMasteryModal
                    conceptId={completedConceptId}
                    masteryScore={masteryScore}
                    onContinue={handleMasteryContinue}
                />
            )}

            {showSyllabus && (
                <Syllabus
                    learnerId={learnerId}
                    courseId={selectedCourseId}
                    onClose={() => setShowSyllabus(false)}
                />
            )}
        </div>
    )
}
