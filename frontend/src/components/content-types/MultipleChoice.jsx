import { useState } from 'react'
import './MultipleChoice.css'

function MultipleChoice({ scenario, question, options, onAnswer, isLoading }) {
  const [selected, setSelected] = useState(null)

  const handleSelect = (optionIndex) => {
    if (isLoading) return
    setSelected(optionIndex)
  }

  const handleSubmit = () => {
    if (selected !== null && !isLoading) {
      onAnswer(selected)
    }
  }

  return (
    <div className="quiz-section">
      <div className="question-container">
        <div className="question-header">
          <div className="question-icon">?</div>
          <h3 className="question-title">Diagnostic Question</h3>
        </div>

        {scenario && (
          <div className="question-scenario">
            <p>{scenario}</p>
          </div>
        )}

        <div className="question-text">
          <p>{question}</p>
        </div>

        <div className="answer-options">
          {options.map((option, index) => (
            <label
              key={index}
              className={`answer-option ${selected === index ? 'selected' : ''}`}
            >
              <input
                type="radio"
                name="answer"
                checked={selected === index}
                onChange={() => handleSelect(index)}
                disabled={isLoading}
              />
              <div className="radio-custom"></div>
              <span className="answer-text">{option}</span>
            </label>
          ))}
        </div>

        <div className="quiz-footer">
          <button
            onClick={handleSubmit}
            className="submit-btn"
            disabled={selected === null || isLoading}
          >
            {isLoading ? 'Checking...' : 'Submit Answer'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default MultipleChoice
