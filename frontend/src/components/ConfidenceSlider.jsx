import { useState } from 'react'
import './ConfidenceSlider.css'

function ConfidenceSlider({ onConfidenceSelect }) {
  const [selected, setSelected] = useState(null)

  const confidenceLevels = [
    { value: 1, label: '', description: 'Guessing' },
    { value: 2, label: '', description: 'Somewhat sure' },
    { value: 3, label: '', description: 'Pretty confident' },
    { value: 4, label: '', description: 'Very confident' }
  ]

  const handleSelect = (value) => {
    setSelected(value)
    onConfidenceSelect(value)
  }

  return (
    <div className="confidence-slider">
      <div className="confidence-header">
        <h3>How confident are you in your answer?</h3>
        <p>Be honest - this helps you learn better!</p>
      </div>

      <div className="confidence-options">
        {confidenceLevels.map((level) => (
          <button
            key={level.value}
            className={`confidence-option ${selected === level.value ? 'selected' : ''}`}
            onClick={() => handleSelect(level.value)}
            aria-label={`Confidence level ${level.value}: ${level.description}`}
          >
            <div className="confidence-stars">{level.label}</div>
            <div className="confidence-desc">{level.description}</div>
          </button>
        ))}
      </div>

      {selected && (
        <div className="confidence-hint">
          You selected: <strong>{confidenceLevels[selected - 1].description}</strong>
        </div>
      )}
    </div>
  )
}

export default ConfidenceSlider
