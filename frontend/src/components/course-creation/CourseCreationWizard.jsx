import { useState } from 'react'
import CourseSetup from './CourseSetup'
import ModulePlanner from './ModulePlanner'
import ResourceLibrary from './ResourceLibrary'
import ConceptEditor from './ConceptEditor'
import CourseReview from './CourseReview'
import './CourseCreationWizard.css'

function CourseCreationWizard({ onComplete, onCancel }) {
  const [currentStep, setCurrentStep] = useState(0)
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
    localStorage.setItem('courseCreationDraft', JSON.stringify(courseData))
    alert('Draft saved!')
  }

  const handlePublish = async () => {
    if (onComplete) {
      await onComplete(courseData)
    }
  }

  const CurrentStepComponent = steps[currentStep].component

  return (
    <div className="course-creation-wizard">
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
