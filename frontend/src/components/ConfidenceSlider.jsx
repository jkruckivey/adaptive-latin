import { useState } from 'react'
import './ConfidenceSlider.css'

function ConfidenceSlider({ onConfidenceSelect }) {
  const [selected, setSelected] = useState(null)

  // 5-point Likert scale for clearer metacognitive calibration
  const confidenceLevels = [
    { value: 1, percentage: 20, label: 'Guessing', description: 'I made a random guess', color: '#a0aec0' },
    { value: 2, percentage: 40, label: 'Unsure', description: 'I have some doubt about my answer', color: '#bfe5e7' },
    { value: 3, percentage: 60, label: 'Moderately Confident', description: 'I think this is correct', color: '#d5cae0' },
    { value: 4, percentage: 80, label: 'Confident', description: 'I\'m fairly certain this is right', color: '#b8a8c9' },
    { value: 5, percentage: 100, label: 'Very Confident', description: 'I\'m certain this is correct', color: '#c0d1cd' }
  ]

  const handleSelect = (value) => {
    setSelected(value)
    onConfidenceSelect(value)
  }

  const handleKeyDown = (e, value) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      handleSelect(value)
    }
    // Arrow key navigation
    else if (e.key === 'ArrowLeft' && value > 1) {
      e.preventDefault()
      const prevButton = e.currentTarget.previousElementSibling
      if (prevButton) prevButton.focus()
    } else if (e.key === 'ArrowRight' && value < 5) {
      e.preventDefault()
      const nextButton = e.currentTarget.nextElementSibling
      if (nextButton) nextButton.focus()
    }
  }

  return (
    <div className="confidence-slider">
      <div className="confidence-header">
        <h3>How confident are you in your answer?</h3>
        <p>Be honest - this helps you learn better!</p>
      </div>

      <div
        className="confidence-scale"
        role="radiogroup"
        aria-label="Confidence level selection"
      >
        {confidenceLevels.map((level, index) => (
          <button
            key={level.value}
            className={`confidence-option ${selected === level.value ? 'selected' : ''}`}
            onClick={() => handleSelect(level.value)}
            onKeyDown={(e) => handleKeyDown(e, level.value)}
            role="radio"
            aria-checked={selected === level.value}
            aria-label={`${level.label} - ${level.percentage}% confidence - ${level.description}`}
            tabIndex={selected === level.value || (selected === null && index === 2) ? 0 : -1}
          >
            <div className="confidence-indicator" style={{ backgroundColor: level.color }} aria-hidden="true">
              <span className="confidence-percentage">{level.percentage}%</span>
            </div>
            <div className="confidence-label">{level.label}</div>
            <div className="confidence-desc">{level.description}</div>
          </button>
        ))}
      </div>

      {selected && (
        <div className="confidence-feedback" role="status" aria-live="polite">
          You selected: <strong>{confidenceLevels[selected - 1].label}</strong> ({confidenceLevels[selected - 1].percentage}%)
          <p className="feedback-desc">{confidenceLevels[selected - 1].description}</p>
        </div>
      )}

      <div className="confidence-explainer">
        <p className="explainer-text">
          <span className="explainer-icon" aria-hidden="true">💡</span>
          Your confidence rating helps the system understand how well you're learning and identify areas that need more practice.
        </p>
      </div>
    </div>
  )
}

export default ConfidenceSlider
