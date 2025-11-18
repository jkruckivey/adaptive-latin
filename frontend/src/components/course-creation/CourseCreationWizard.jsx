import { useState, useEffect, useRef } from 'react'
import { api } from '../../api'
import CourseSetup from './CourseSetup'
import OnboardingQuestionBuilder from './OnboardingQuestionBuilder'
import ModulePlanner from './ModulePlanner'
import ResourceLibrary from './ResourceLibrary'
import ConceptEditor from './ConceptEditor'
import CourseReview from './CourseReview'
import './CourseCreationWizard.css'

function CourseCreationWizard({ onComplete, onCancel }) {
  const [showInitialChoice, setShowInitialChoice] = useState(true)
  const [isParsingSyllabus, setIsParsingSyllabus] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)
  const [showToast, setShowToast] = useState(false)
  const [toastMessage, setToastMessage] = useState('')
  const [lastAutoSaved, setLastAutoSaved] = useState(null)
  const autoSaveTimeoutRef = useRef(null)
  const isInitialMount = useRef(true)
  const [courseData, setCourseData] = useState({
    // Course-level info
    title: '',
    domain: '',
    description: '',
    targetAudience: '',

    // Modules (each module contains concepts)
    modules: [],

    // External sources
    sources: []
  })

  const steps = [
    { title: 'Course Setup', component: CourseSetup },
    { title: 'Onboarding Questions', component: OnboardingQuestionBuilder },
    { title: 'Plan Modules', component: ModulePlanner },
    { title: 'Resource Library', component: ResourceLibrary },
    { title: 'Build Content', component: ConceptEditor },
    { title: 'Review & Publish', component: CourseReview }
  ]

  const handleNext = (stepData) => {
    // Merge step data into course data
    setCourseData(prev => ({ ...prev, ...stepData }))

    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1)
    }
  }

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleSaveDraft = () => {
    // Save to localStorage for now
    const timestamp = new Date().toLocaleString()
    localStorage.setItem('courseCreationDraft', JSON.stringify(courseData))
    localStorage.setItem('courseCreationDraftTimestamp', timestamp)

    // Show toast notification
    setToastMessage(`Draft saved at ${timestamp}`)
    setShowToast(true)

    // Auto-hide toast after 3 seconds
    setTimeout(() => {
      setShowToast(false)
    }, 3000)
  }

  const handlePublish = async () => {
    if (onComplete) {
      await onComplete(courseData)
    }
  }

  // Auto-save effect with debouncing
  useEffect(() => {
    // Skip auto-save on initial mount or if on initial choice screen
    if (isInitialMount.current || showInitialChoice) {
      isInitialMount.current = false
      return
    }

    // Skip if courseData is empty
    if (!courseData.title && courseData.modules.length === 0) {
      return
    }

    // Clear existing timeout
    if (autoSaveTimeoutRef.current) {
      clearTimeout(autoSaveTimeoutRef.current)
    }

    // Set new timeout for auto-save (3 seconds after last change)
    autoSaveTimeoutRef.current = setTimeout(() => {
      const timestamp = new Date().toLocaleString()
      localStorage.setItem('courseCreationDraft', JSON.stringify(courseData))
      localStorage.setItem('courseCreationDraftTimestamp', timestamp)
      setLastAutoSaved(timestamp)
    }, 3000)

    // Cleanup function
    return () => {
      if (autoSaveTimeoutRef.current) {
        clearTimeout(autoSaveTimeoutRef.current)
      }
    }
  }, [courseData, showInitialChoice])

  const handleStartFromScratch = () => {
    setShowInitialChoice(false)
  }

  const handleImportJSON = async (event) => {
    const file = event.target.files[0]
    if (!file) return

    try {
      const text = await file.text()
      const importData = JSON.parse(text)

      // Validate import structure
      if (!importData.export || !importData.export.course) {
        alert('Invalid export file format')
        return
      }

      const { course, modules } = importData.export

      // Transform imported data to match wizard format
      setCourseData({
        title: course.title,
        domain: course.domain,
        taxonomy: course.taxonomy || 'blooms',
        courseLearningOutcomes: course.course_learning_outcomes || [],
        description: course.description,
        targetAudience: course.target_audience,
        modules: (modules || []).map(module => ({
          moduleId: module.id,
          title: module.title,
          moduleLearningOutcomes: module.module_learning_outcomes || [],
          concepts: (module.concepts || []).map(concept => ({
            conceptId: concept.concept_id,
            title: concept.title,
            learningObjectives: concept.learning_objectives || [],
            prerequisites: concept.prerequisites || [],
            teachingContent: '',
            vocabulary: []
          }))
        })),
        sources: []
      })

      setShowInitialChoice(false)
      setCurrentStep(0)
      alert('Course imported successfully! Review and edit as needed.')
    } catch (error) {
      console.error('Import error:', error)
      alert('Failed to import course. Please check the file format.')
    }
  }

  const handleImportCartridge = async (event) => {
    console.log('handleImportCartridge called', event.target.files)
    const file = event.target.files[0]
    if (!file) {
      console.log('No file selected')
      return
    }

    console.log('Importing cartridge file:', file.name, file.size, 'bytes')
    setIsParsingSyllabus(true) // Reuse the same loading state
    try {
      console.log('Calling api.importCartridge...')
      const result = await api.importCartridge(file)
      console.log('Import result:', result)

      if (result.success && result.extracted_data) {
        // Populate wizard with extracted data
        setCourseData({
          ...result.extracted_data,
          sources: []
        })

        setShowInitialChoice(false)
        setCurrentStep(0)

        const moduleCount = result.extracted_data.modules?.length || 0
        const conceptCount = result.extracted_data.modules?.reduce((sum, m) => sum + (m.concepts?.length || 0), 0) || 0

        alert(`Common Cartridge imported successfully!\n\nExtracted:\n- ${moduleCount} modules\n- ${conceptCount} concepts\n\nReview and edit as needed.`)
      }
    } catch (error) {
      console.error('Cartridge import error:', error)
      alert(`Failed to import cartridge: ${error.message}\n\nTip: Make sure the file is a valid Common Cartridge (.imscc) export.`)
    } finally {
      setIsParsingSyllabus(false)
      // Reset file input so same file can be selected again
      event.target.value = ''
    }
  }

  const handleParseSyllabus = async (event) => {
    console.log('handleParseSyllabus called', event.target.files)
    const file = event.target.files[0]
    if (!file) {
      console.log('No file selected')
      return
    }

    console.log('Parsing syllabus file:', file.name, file.size, 'bytes')
    setIsParsingSyllabus(true)
    try {
      console.log('Calling api.parseSyllabus...')
      const result = await api.parseSyllabus(file)
      console.log('Parse result:', result)

      if (result.success && result.extracted_data) {
        // Populate wizard with extracted data
        setCourseData({
          ...result.extracted_data,
          sources: []
        })

        setShowInitialChoice(false)
        setCurrentStep(0)
        alert(`Syllabus parsed successfully!\n\nExtracted:\n- ${result.extracted_data.modules.length} modules\n- ${result.extracted_data.modules.reduce((sum, m) => sum + m.concepts.length, 0)} concepts\n\nReview and edit as needed.`)
      }
    } catch (error) {
      console.error('Syllabus parsing error:', error)
      alert(`Failed to parse syllabus: ${error.message}\n\nTip: Make sure your syllabus includes clear course information and topics.`)
    } finally {
      setIsParsingSyllabus(false)
      // Reset file input so same file can be selected again
      event.target.value = ''
    }
  }

  const CurrentStepComponent = steps[currentStep].component

  // Show initial choice screen
  if (showInitialChoice) {
    return (
      <div className="course-creation-wizard">
        <div className="wizard-content">
          <div className="initial-choice-screen">
            <h2>Create New Course</h2>
            <p className="subtitle">Choose how you'd like to get started</p>

            <div className="choice-options">
              <button
                className="choice-option"
                onClick={handleStartFromScratch}
              >
                <div className="choice-icon">+</div>
                <div className="choice-title">Start from Scratch</div>
                <div className="choice-description">
                  Build a new course step-by-step with our guided course creation wizard
                </div>
              </button>

              <label className="choice-option" htmlFor="syllabus-file">
                <div className="choice-icon">AI</div>
                <div className="choice-title">Upload Syllabus</div>
                <div className="choice-description">
                  Let AI extract course structure and learning outcomes from your syllabus (.txt or .pdf)
                </div>
                <input
                  id="syllabus-file"
                  type="file"
                  accept=".txt,.pdf"
                  onChange={handleParseSyllabus}
                  disabled={isParsingSyllabus}
                  style={{ display: 'none' }}
                />
                {isParsingSyllabus && <div className="parsing-indicator">Parsing...</div>}
              </label>

              <label className="choice-option" htmlFor="cartridge-file">
                <div className="choice-icon">LMS</div>
                <div className="choice-title">Import from LMS</div>
                <div className="choice-description">
                  Import existing course content from Canvas, Moodle, or Blackboard (.imscc export file)
                </div>
                <input
                  id="cartridge-file"
                  type="file"
                  accept=".imscc,.zip"
                  onChange={handleImportCartridge}
                  disabled={isParsingSyllabus}
                  style={{ display: 'none' }}
                />
                {isParsingSyllabus && <div className="parsing-indicator">Importing...</div>}
              </label>

              <label className="choice-option" htmlFor="import-file">
                <div className="choice-icon">{ }</div>
                <div className="choice-title">Import from JSON</div>
                <div className="choice-description">
                  Restore a previously exported course or import from another instance
                </div>
                <input
                  id="import-file"
                  type="file"
                  accept=".json"
                  onChange={handleImportJSON}
                  style={{ display: 'none' }}
                />
              </label>
            </div>

            <button
              onClick={onCancel}
              className="wizard-button secondary"
              style={{ marginTop: '2rem' }}
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="course-creation-wizard">
      {/* Toast Notification */}
      {showToast && (
        <div className="toast-notification">
          <span className="toast-icon">✓</span>
          <span className="toast-message">{toastMessage}</span>
          <button
            className="toast-close"
            onClick={() => setShowToast(false)}
            aria-label="Close notification"
          >
            ×
          </button>
        </div>
      )}

      {/* Auto-save indicator */}
      {lastAutoSaved && (
        <div className="auto-save-indicator">
          Auto-saved at {lastAutoSaved}
        </div>
      )}

      {/* Progress indicator */}
      <div className="wizard-progress">
        {steps.map((step, index) => (
          <div
            key={index}
            className={`progress-step ${index === currentStep ? 'active' : ''} ${index < currentStep ? 'completed' : ''}`}
          >
            <div className="step-number">{index + 1}</div>
            <div className="step-title">{step.title}</div>
          </div>
        ))}
      </div>

      {/* Current step content */}
      <div className="wizard-content">
        <CurrentStepComponent
          courseData={courseData}
          onNext={handleNext}
          onBack={handleBack}
          onSaveDraft={handleSaveDraft}
          onPublish={handlePublish}
          onCancel={onCancel}
        />
      </div>
    </div>
  )
}

export default CourseCreationWizard
