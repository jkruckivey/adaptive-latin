import { useState } from 'react'
import DeclensionExplorer from './DeclensionExplorer'
import WordOrderManipulator from './WordOrderManipulator'
import './ScenarioWidget.css'

function ScenarioWidget({ scenario, onComplete }) {
  const [currentStep, setCurrentStep] = useState(0)

  const getScenarioIcon = () => {
    const icons = {
      market: '🏛️',
      music: '🎵',
      speech: '🗣️',
      bath: '🛁',
      feast: '🍇',
      temple: '⛩️',
      military: '⚔️',
      letter: '✉️'
    }
    return icons[scenario.theme] || '📜'
  }

  const step = scenario.steps[currentStep]

  const handleNext = () => {
    if (currentStep < scenario.steps.length - 1) {
      setCurrentStep(currentStep + 1)
    } else {
      onComplete?.()
    }
  }

  const renderStepContent = () => {
    switch (step.type) {
      case 'narrative':
        return (
          <div className="scenario-narrative">
            {step.image && <div className="narrative-image">{step.image}</div>}
            <div className="narrative-text">
              {step.paragraphs.map((p, i) => (
                <p key={i}>{p}</p>
              ))}
            </div>
            {step.dialogue && (
              <div className="narrative-dialogue">
                <div className="dialogue-label">You hear:</div>
                <div className="dialogue-text">"{step.dialogue}"</div>
                {step.translation && (
                  <div className="dialogue-translation">({step.translation})</div>
                )}
              </div>
            )}
          </div>
        )

      case 'declension-explorer':
        return <DeclensionExplorer {...step.widgetProps} />

      case 'word-order-manipulator':
        return <WordOrderManipulator {...step.widgetProps} />

      case 'challenge':
        return (
          <div className="scenario-challenge">
            <div className="challenge-prompt">{step.prompt}</div>
            <div className="challenge-options">
              {step.options.map((option, i) => (
                <button
                  key={i}
                  className="challenge-option"
                  onClick={() => step.onSelect?.(i)}
                >
                  {option}
                </button>
              ))}
            </div>
          </div>
        )

      default:
        return <div>Unknown step type</div>
    }
  }

  return (
    <div className="scenario-widget">
      <div className="scenario-header">
        <div className="scenario-icon">{getScenarioIcon()}</div>
        <div className="scenario-title-section">
          <h2 className="scenario-title">{scenario.title}</h2>
          <p className="scenario-subtitle">{scenario.setting}</p>
        </div>
      </div>

      <div className="scenario-progress">
        <div className="progress-label">
          Step {currentStep + 1} of {scenario.steps.length}
        </div>
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${((currentStep + 1) / scenario.steps.length) * 100}%` }}
          />
        </div>
      </div>

      <div className="scenario-content">
        {step.stepTitle && (
          <h3 className="step-title">{step.stepTitle}</h3>
        )}
        {renderStepContent()}
      </div>

      <div className="scenario-navigation">
        {currentStep > 0 && (
          <button
            onClick={() => setCurrentStep(currentStep - 1)}
            className="nav-button prev-button"
          >
            ← Previous
          </button>
        )}
        <button
          onClick={handleNext}
          className="nav-button next-button"
        >
          {currentStep < scenario.steps.length - 1 ? 'Continue →' : 'Complete ✓'}
        </button>
      </div>
    </div>
  )
}

export default ScenarioWidget
