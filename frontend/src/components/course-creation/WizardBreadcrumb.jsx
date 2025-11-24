import './WizardBreadcrumb.css'

function WizardBreadcrumb({ steps, currentStep, onStepClick }) {
  return (
    <nav className="wizard-breadcrumb" aria-label="Wizard progress">
      <ol className="breadcrumb-list">
        {steps.map((step, index) => {
          const stepNumber = index + 1
          const isCompleted = stepNumber < currentStep
          const isCurrent = stepNumber === currentStep
          const isClickable = isCompleted && onStepClick

          return (
            <li
              key={step.id}
              className={`breadcrumb-item ${
                isCompleted ? 'completed' : ''
              } ${isCurrent ? 'current' : ''} ${isClickable ? 'clickable' : ''}`}
            >
              {isClickable ? (
                <button
                  onClick={() => onStepClick(stepNumber)}
                  className="breadcrumb-button"
                  aria-label={`Go to ${step.label}`}
                  aria-current={isCurrent ? 'step' : undefined}
                >
                  <span className="step-indicator" aria-hidden="true">
                    {isCompleted ? '✓' : stepNumber}
                  </span>
                  <span className="step-label">{step.label}</span>
                </button>
              ) : (
                <div
                  className="breadcrumb-content"
                  aria-current={isCurrent ? 'step' : undefined}
                >
                  <span className="step-indicator" aria-hidden="true">
                    {isCompleted ? '✓' : stepNumber}
                  </span>
                  <span className="step-label">{step.label}</span>
                </div>
              )}

              {index < steps.length - 1 && (
                <span className="breadcrumb-separator" aria-hidden="true">
                  →
                </span>
              )}
            </li>
          )
        })}
      </ol>

      {/* Progress bar */}
      <div className="breadcrumb-progress-bar" role="progressbar" aria-valuenow={currentStep} aria-valuemin={1} aria-valuemax={steps.length} aria-label={`Step ${currentStep} of ${steps.length}`}>
        <div
          className="progress-fill"
          style={{ width: `${(currentStep / steps.length) * 100}%` }}
        />
      </div>

      {/* Step count text for screen readers */}
      <div className="sr-only" role="status" aria-live="polite">
        Step {currentStep} of {steps.length}: {steps[currentStep - 1]?.label}
      </div>
    </nav>
  )
}

export default WizardBreadcrumb
