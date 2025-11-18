import './ConfidenceRating.css'

function ConfidenceRating({ onSubmit }) {
  const levels = [
    { value: 1, label: 'Just guessing', emoji: '' },
    { value: 2, label: 'Not very confident', emoji: '' },
    { value: 3, label: 'Somewhat confident', emoji: '' },
    { value: 4, label: 'Quite confident', emoji: '' },
    { value: 5, label: 'Very confident', emoji: '' }
  ]

  return (
    <div className="confidence-rating">
      <div className="confidence-prompt">
        <p>How confident are you in your answer?</p>
      </div>
      <div className="confidence-buttons">
        {levels.map((level) => (
          <button
            key={level.value}
            onClick={() => onSubmit(level.value)}
            className="confidence-button"
          >
            <span className="confidence-emoji">{level.emoji}</span>
            <span className="confidence-value">{level.value}</span>
            <span className="confidence-label">{level.label}</span>
          </button>
        ))}
      </div>
    </div>
  )
}

export default ConfidenceRating
